"""Local HTTP bridge: /audio_list, /tts, /speakers, /health."""
import hashlib
import json
import logging
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import __version__
from .config import CACHE_DIR, load_config

log = logging.getLogger("bridge.server")

FISH_API_URL = "https://api.fish.audio/v1/tts"


class _Handler(BaseHTTPRequestHandler):
    server_version = f"YomitanFishAudioBridge/{__version__}"

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")

    def _json(self, status, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _bytes(self, status, data, ctype):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def _html(self, status, html):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _index(self):
        port = self.server.bridge.port
        self._html(200, f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<title>Yomitan FishAudio Bridge</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;max-width:640px;margin:40px auto;padding:0 20px;color:#222}}
code{{background:#f3f3f3;padding:2px 6px;border-radius:4px}}
h1{{color:#c8441a}}</style></head>
<body>
<h1>Yomitan FishAudio Bridge</h1>
<p>Сервер работает на порту <code>{port}</code>.</p>
<p>Это не веб-интерфейс. Отсюда ничего нажимать не нужно — все настройки
в отдельном окне приложения.</p>
<p>URL для Yomitan:</p>
<p><code>http://127.0.0.1:{port}/audio_list?term={{term}}&amp;reading={{reading}}</code></p>
<p>Проверка: <a href="/health">/health</a></p>
</body></html>""")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        path = parsed.path
        if path == "/audio_list":
            return self._audio_list(params)
        if path == "/tts":
            return self._tts(params)
        if path == "/speakers":
            return self._json(200, self.server.bridge.variants)
        if path == "/health":
            return self._json(200, {"ok": True, "version": __version__})
        if path in ("/", ""):
            return self._index()
        self._json(404, {"detail": "Not found"})

    def _audio_list(self, params):
        term = params.get("term", [None])[0]
        reading = params.get("reading", [None])[0]
        target = reading or term
        if not target:
            return self._json(200, {"type": "audioSourceList", "audioSources": []})
        encoded = urllib.parse.quote(target)
        host = self.headers.get("Host") or f"{self.server.bridge.host}:{self.server.bridge.port}"
        base = f"http://{host}"
        sources = [
            {
                "name": v["name"],
                "url": (
                    f"{base}/tts?text={encoded}"
                    f"&reference_id={v['reference_id']}"
                    f"&format={v.get('format', 'mp3')}"
                ),
            }
            for v in self.server.bridge.variants
        ]
        self._json(200, {"type": "audioSourceList", "audioSources": sources})

    def _tts(self, params):
        text = params.get("text", [None])[0]
        reading = params.get("reading", [None])[0]
        reference_id = params.get("reference_id", [None])[0]
        fmt = params.get("format", [None])[0]
        target = reading or text
        if not target:
            return self._json(400, {"detail": "text/reading required"})
        cfg = load_config()
        if not cfg["api_key"]:
            return self._json(500, {"detail": "API key not set"})
        if not reference_id:
            voices = cfg.get("voices", [])
            if voices:
                reference_id = voices[0]["reference_id"]
            else:
                return self._json(400, {"detail": "no voices configured"})
        active_fmt = fmt or "mp3"
        try:
            audio = self.server.bridge.synthesize(target, reference_id, active_fmt)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            log.error("Fish Audio HTTP %s: %s", e.code, body)
            return self._json(e.code, {"detail": "Fish Audio API error"})
        except Exception as e:
            log.exception("synthesis failed: %s", e)
            return self._json(503, {"detail": "Fish Audio unreachable"})
        ctype = "audio/mpeg" if active_fmt == "mp3" else "audio/wav"
        self._bytes(200, audio, ctype)

    def log_message(self, fmt, *args):
        log.info("%s - %s", self.address_string(), fmt % args)


class BridgeServer:
    def __init__(self, host="127.0.0.1", port=47632):
        self.host = host
        self.port = port
        self._httpd = None
        self._thread = None

    @property
    def variants(self):
        cfg = load_config()
        return [
            {
                "name": v.get("name", "Voice"),
                "reference_id": v["reference_id"],
                "format": v.get("format", "mp3"),
            }
            for v in cfg.get("voices", [])
        ]

    def synthesize(self, text: str, reference_id: str, fmt: str) -> bytes:
        key = f"{text}_{reference_id}_{fmt}"
        h = hashlib.md5(key.encode()).hexdigest()
        cache_file = CACHE_DIR / f"{h}.{fmt}"
        if cache_file.exists():
            log.info("[CACHE HIT] %s", text)
            return cache_file.read_bytes()
        log.info("[GENERATING] %s", text)
        cfg = load_config()
        payload = json.dumps({
            "text": text,
            "reference_id": reference_id,
            "format": fmt,
        }).encode("utf-8")
        req = urllib.request.Request(
            FISH_API_URL,
            data=payload,
            headers={
                "Authorization": f"Bearer {cfg['api_key']}",
                "Content-Type": "application/json",
                "model": cfg.get("model", "s2.1-pro-free"),
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            audio = r.read()
        cache_file.write_bytes(audio)
        return audio

    def start(self):
        if self._httpd is not None:
            return
        ThreadingHTTPServer.allow_reuse_address = True
        self._httpd = ThreadingHTTPServer((self.host, self.port), _Handler)
        self._httpd.bridge = self
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        log.info("Server on http://%s:%s", self.host, self.port)

    def stop(self):
        if self._httpd is None:
            return
        self._httpd.shutdown()
        self._httpd.server_close()
        self._httpd = None
        self._thread = None
        log.info("Server stopped")


def find_free_port(host: str, start: int = 47632, tries: int = 200) -> int:
    for p in range(start, start + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, p))
                return p
            except OSError:
                continue
    raise RuntimeError("No free port found")


def run_headless(host: str = "127.0.0.1", port: int | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    if port is None:
        port = find_free_port(host)
    srv = BridgeServer(host=host, port=port)
    srv.start()
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        srv.stop()

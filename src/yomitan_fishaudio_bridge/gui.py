"""tkinter GUI."""
import json
import logging
import queue
import threading
import tkinter as tk
import urllib.error
import urllib.request
import webbrowser
from tkinter import messagebox, ttk

from . import __version__, autostart
from .config import load_config, save_config
from .i18n import LANGS, set_lang, t
from .server import BridgeServer, find_free_port

log = logging.getLogger("bridge.gui")

DOCS_URL = "https://github.com/"


class _LogHandler(logging.Handler):
    def __init__(self, q):
        super().__init__()
        self.q = q
        self.setFormatter(logging.Formatter("%(asctime)s  %(message)s", "%H:%M:%S"))

    def emit(self, record):
        self.q.put(self.format(record))


class App:
    def __init__(self, background=False):
        self.cfg = load_config()
        set_lang(self.cfg.get("lang", "ru"))
        self.server = None
        self.log_q = queue.Queue()

        self.root = tk.Tk()
        self.root.title(f"{t('app_title')} {__version__}")
        self.root.minsize(660, 500)

        self._setup_logging()
        self._build()
        self._load_into_form()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(200, self._drain_log)

        if background:
            self.root.withdraw()

    def _setup_logging(self):
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        root.addHandler(_LogHandler(self.log_q))
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        root.addHandler(sh)

    def _build(self):
        pad = {"padx": 12, "pady": 6}
        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True)

        top = ttk.Frame(main)
        top.pack(fill="x", **pad)
        ttk.Label(top, text=t("lang_label")).pack(side="left")
        self.lang_var = tk.StringVar()
        cb = ttk.Combobox(top, textvariable=self.lang_var, values=list(LANGS), width=4, state="readonly")
        cb.pack(side="left", padx=6)
        cb.bind("<<ComboboxSelected>>", self._on_lang)

        row = ttk.Frame(main)
        row.pack(fill="x", **pad)
        ttk.Label(row, text=t("api_key_label")).pack(anchor="w")
        inner = ttk.Frame(row)
        inner.pack(fill="x")
        self.key_var = tk.StringVar()
        ttk.Entry(inner, textvariable=self.key_var, show="•").pack(side="left", fill="x", expand=True)
        ttk.Button(inner, text=t("check"), command=self._on_check).pack(side="left", padx=6)
        ttk.Label(row, text=t("api_key_hint"), foreground="#888").pack(anchor="w")

        row = ttk.Frame(main)
        row.pack(fill="x", **pad)
        ttk.Label(row, text=t("port_label")).pack(side="left")
        self.port_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.port_var, width=8).pack(side="left", padx=6)
        self.autostart_var = tk.BooleanVar()
        ttk.Checkbutton(row, text=t("autostart"), variable=self.autostart_var,
                        command=self._on_autostart).pack(side="left", padx=12)

        row = ttk.Frame(main)
        row.pack(fill="x", **pad)
        ttk.Label(row, text=t("url_label")).pack(anchor="w")
        inner = ttk.Frame(row)
        inner.pack(fill="x")
        self.url_var = tk.StringVar()
        ttk.Entry(inner, textvariable=self.url_var, state="readonly").pack(side="left", fill="x", expand=True)
        ttk.Button(inner, text=t("copy"), command=self._on_copy).pack(side="left", padx=6)

        row = ttk.Frame(main)
        row.pack(fill="x", **pad)
        self.start_btn = ttk.Button(row, text=t("start"), command=self._on_start)
        self.start_btn.pack(side="left")
        self.stop_btn = ttk.Button(row, text=t("stop"), command=self._on_stop, state="disabled")
        self.stop_btn.pack(side="left", padx=6)
        ttk.Button(row, text=t("open_docs"), command=self._on_docs).pack(side="right")

        self.status_var = tk.StringVar(value=t("status_stopped"))
        ttk.Label(main, textvariable=self.status_var, foreground="#555").pack(anchor="w", **pad)

        ttk.Label(main, text=t("log")).pack(anchor="w", padx=12)
        self.log_text = tk.Text(main, height=12, wrap="word", state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _load_into_form(self):
        self.lang_var.set(self.cfg.get("lang", "ru"))
        self.key_var.set(self.cfg.get("api_key", ""))
        self.port_var.set(str(self.cfg.get("port", 47632)))
        try:
            self.autostart_var.set(autostart.is_enabled())
        except Exception:
            self.autostart_var.set(False)
        self._update_url()

    def _update_url(self):
        port = self.port_var.get() or "47632"
        self.url_var.set(
            f"http://127.0.0.1:{port}/audio_list?term={{term}}&reading={{reading}}"
        )

    def _on_lang(self, *_):
        lang = self.lang_var.get()
        set_lang(lang)
        self.cfg["lang"] = lang
        save_config(self.cfg)
        messagebox.showinfo(t("app_title"), t("restart_hint"))

    def _on_check(self):
        key = self.key_var.get().strip()
        if not key:
            messagebox.showwarning(t("app_title"), t("key_required"))
            return
        self.status_var.set(t("checking"))
        threading.Thread(target=self._check_worker, args=(key,), daemon=True).start()

    def _check_worker(self, key):
        payload = json.dumps({
            "text": "test",
            "reference_id": self.cfg["reference_id"],
            "format": "mp3",
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.fish.audio/v1/tts",
            data=payload,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "model": self.cfg.get("model", "s2.1-pro-free"),
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                r.read()
            self.root.after(0, lambda: self.status_var.set(t("check_ok")))
        except urllib.error.HTTPError as e:
            self.root.after(0, lambda: self.status_var.set(t("check_fail", err=f"HTTP {e.code}")))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(t("check_fail", err=str(e))))

    def _on_autostart(self):
        want = self.autostart_var.get()
        try:
            if want:
                autostart.enable()
            else:
                autostart.disable()
            self.cfg["autostart"] = want
            save_config(self.cfg)
        except Exception as e:
            log.error("autostart failed: %s", e)
            self.autostart_var.set(not want)

    def _on_copy(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.url_var.get())
        self.status_var.set(t("copied"))

    def _on_docs(self):
        webbrowser.open(DOCS_URL)

    def _on_start(self):
        key = self.key_var.get().strip()
        if not key:
            messagebox.showwarning(t("app_title"), t("key_required"))
            return
        try:
            port = int(self.port_var.get())
        except ValueError:
            port = 47632

        self.cfg.update({"api_key": key, "port": port, "lang": self.lang_var.get()})
        save_config(self.cfg)

        free = find_free_port("127.0.0.1", start=port)
        if free != port:
            log.warning(t("port_busy", old=port, new=free))
            self.port_var.set(str(free))
            self.cfg["port"] = free
            save_config(self.cfg)

        self.server = BridgeServer(host="127.0.0.1", port=free)
        self.server.start()
        self._update_url()
        self.status_var.set(t("status_running", port=free))
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

    def _on_stop(self):
        if self.server:
            self.server.stop()
            self.server = None
        self.status_var.set(t("status_stopped"))
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    def _on_close(self):
        if self.server:
            self.server.stop()
        self.root.destroy()

    def _drain_log(self):
        try:
            while True:
                line = self.log_q.get_nowait()
                self.log_text.config(state="normal")
                self.log_text.insert("end", line + "\n")
                self.log_text.see("end")
                self.log_text.config(state="disabled")
        except queue.Empty:
            pass
        self.root.after(200, self._drain_log)

    def run(self):
        self.root.mainloop()


def run_gui(background: bool = False) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    App(background=background).run()

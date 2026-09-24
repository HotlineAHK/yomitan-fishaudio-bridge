"""Config storage — platform-aware."""
import json
import os
import sys
from pathlib import Path

APP_NAME = "YomitanFishAudioBridge"


def _config_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / APP_NAME


def _cache_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / APP_NAME / "cache"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / APP_NAME
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / APP_NAME


CONFIG_DIR = _config_dir()
CONFIG_PATH = CONFIG_DIR / "config.json"
CACHE_DIR = _cache_dir()
CACHE_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_VOICES = [
    {
        "name": "Indian",
        "reference_id": "8e468a7c906648e3bb4cb7c08185b14a",
        "format": "mp3",
    }
]

DEFAULTS = {
    "api_key": "",
    "port": 47632,
    "voices": DEFAULT_VOICES,
    "model": "s2.1-pro-free",
    "lang": "ru",
    "autostart": False,
}


def _normalize_voices(raw) -> list:
    out = []
    if not isinstance(raw, list):
        return out
    for v in raw:
        if not isinstance(v, dict):
            continue
        rid = str(v.get("reference_id", "")).strip()
        if not rid:
            continue
        out.append({
            "name": (str(v.get("name", "Voice")).strip() or "Voice"),
            "reference_id": rid,
            "format": (str(v.get("format", "mp3")).strip() or "mp3"),
        })
    return out


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        cfg = dict(DEFAULTS)
        cfg["voices"] = [dict(v) for v in DEFAULT_VOICES]
        return cfg
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        cfg = dict(DEFAULTS)
        cfg["voices"] = [dict(v) for v in DEFAULT_VOICES]
        return cfg

    # migrate old single-voice config
    if "voices" not in data and data.get("reference_id"):
        data["voices"] = [{
            "name": data.get("voice_name", "Voice"),
            "reference_id": data["reference_id"],
            "format": data.get("format", "mp3"),
        }]

    cfg = dict(DEFAULTS)
    cfg.update({k: v for k, v in data.items() if k in DEFAULTS})
    cfg["voices"] = _normalize_voices(cfg.get("voices", []))
    return cfg


def save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

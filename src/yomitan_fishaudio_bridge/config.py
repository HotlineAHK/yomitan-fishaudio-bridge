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

DEFAULTS = {
    "api_key": "",
    "port": 47632,
    "reference_id": "8e468a7c906648e3bb4cb7c08185b14a",
    "format": "mp3",
    "model": "s2.1-pro-free",
    "voice_name": "Indian",
    "lang": "ru",
    "autostart": False,
}


def load_config() -> dict:
    cfg = dict(DEFAULTS)
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            cfg.update({k: v for k, v in data.items() if k in DEFAULTS})
        except Exception:
            pass
    return cfg


def save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

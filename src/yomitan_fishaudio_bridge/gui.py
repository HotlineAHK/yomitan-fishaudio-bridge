"""CustomTkinter GUI."""
import json
import logging
import queue
import sys
import threading
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from . import __version__, autostart
from .config import load_config, save_config
from .i18n import LANGS, set_lang, t
from .server import BridgeServer, find_free_port
from .tray import HAS_TRAY, TrayController

log = logging.getLogger("bridge.gui")

DOCS_URL = "https://github.com/HotlineAHK/yomitan-fishaudio-bridge"
APP_TITLE = "Yomitan FishAudio Bridge"

PRIMARY = "#e07030"
PRIMARY_HOVER = "#c8441a"
PRIMARY_SOFT = ("#f8e4d5", "#3a2a22")
OK = "#2e9e5b"
OK_HOVER = "#247d47"
ERR = "#d94545"
ERR_HOVER = "#b33636"
ERR_SOFT = ("#f9dede", "#3a2222")
STOP = ("#c9c9cc", "#4a4a4e")
STOP_HOVER = ("#b3b3b6", "#5e5e62")
MUTED = "#8a8a8a"
CARD = ("#ffffff", "#252528")
CARD_BORDER = ("#e6e6e8", "#333336")
CHIP_NEUTRAL = ("#efeff1", "#333336")
CHIP_TEXT_NEUTRAL = ("#5a5a5e", "#cfcfd3")
LOG_BG = ("#fafafb", "#1f1f22")

_MONO = {"win32": "Consolas", "darwin": "Menlo"}.get(sys.platform, "Monospace")


def _resource_path(rel: str) -> Path:
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        base = Path(__file__).resolve().parent.parent.parent
    return base / rel


def _extract_ref_id(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    if "://" in text or text.startswith("fish.audio"):
        from urllib.parse import urlparse
        url = text if "://" in text else "https://" + text
        try:
            parsed = urlparse(url)
            parts = [p for p in parsed.path.split("/") if p]
            for p in reversed(parts):
                if len(p) >= 8:
                    return p
        except Exception:
            pass
    return text


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
        self.tray = None
        self.log_q = queue.Queue()
        self._copied_reset = None
        self._check_reset = None
        self._chip_state = "neutral"

        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title(f"{APP_TITLE} {__version__}")
        self.root.geometry("780x900")
        self.root.minsize(740, 820)
        self._set_window_icon()

        self._setup_logging()
        self._build()
        self._load_into_form()
        self._refresh_voices()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(200, self._drain_log)

        log.info("%s %s", APP_TITLE, __version__)
        log.info("Готово к запуску. Вставьте API-ключ и нажмите «Старт».")

        if background:
            self.root.after(150, self._auto_background_start)

    def _set_window_icon(self):
        try:
            import tkinter as tk
            p = _resource_path("assets/icon.png")
            if p.exists():
                self._icon_photo = tk.PhotoImage(file=str(p))
                self.root.iconphoto(True, self._icon_photo)
        except Exception as e:
            log.debug("window icon: %s", e)

    def _setup_logging(self):
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        root.addHandler(_LogHandler(self.log_q))
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        root.addHandler(sh)

    # ---------- ui ----------
    def _build(self):
        padx = 18
        sect_pady = 8

        header = ctk.CTkFrame(self.root, fg_color="transparent")
        header.pack(fill="x", padx=padx, pady=(16, 8))
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(title_box, text="  ", fg_color=PRIMARY, corner_radius=6,
                     width=22, height=22, text_color=PRIMARY).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(title_box, text=APP_TITLE,
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=PRIMARY).pack(side="left")

        lang_box = ctk.CTkFrame(header, fg_color="transparent")
        lang_box.pack(side="right")
        ctk.CTkLabel(lang_box, text=t("lang_label"), text_color=MUTED,
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 6))
        self.lang_var = ctk.StringVar(value=self.cfg.get("lang", "ru"))
        ctk.CTkOptionMenu(
            lang_box, values=list(LANGS), variable=self.lang_var,
            width=72, height=30, corner_radius=8,
            fg_color=PRIMARY, button_color=PRIMARY_HOVER,
            button_hover_color=PRIMARY_HOVER,
            dropdown_fg_color=CARD, dropdown_hover_color=PRIMARY_SOFT,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_lang,
        ).pack(side="left")

        # API key
        card = ctk.CTkFrame(self.root, corner_radius=14, fg_color=CARD,
                            border_width=1, border_color=CARD_BORDER)
        card.pack(fill="x", padx=padx, pady=sect_pady)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(inner, text=t("api_key_label"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=(8, 0))
        self.key_var = ctk.StringVar()
        ctk.CTkEntry(row, textvariable=self.key_var, show="•", height=38,
                     corner_radius=8, font=ctk.CTkFont(family=_MONO, size=12)
                     ).pack(side="left", fill="x", expand=True)
        self.check_btn = ctk.CTkButton(
            row, text=t("check"), width=140, height=38, corner_radius=8,
            fg_color="transparent", text_color=PRIMARY,
            border_width=1, border_color=PRIMARY, hover_color=PRIMARY_SOFT,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_check,
        )
        self.check_btn.pack(side="left", padx=(8, 0))
        ctk.CTkLabel(inner, text=t("api_key_hint"), text_color=MUTED,
                     font=ctk.CTkFont(size=11), anchor="w", justify="left",
                     ).pack(anchor="w", pady=(8, 0))

        # Voices
        card = ctk.CTkFrame(self.root, corner_radius=14, fg_color=CARD,
                            border_width=1, border_color=CARD_BORDER)
        card.pack(fill="x", padx=padx, pady=sect_pady)
        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(14, 4))
        self.voices_title = ctk.CTkLabel(head, text=t("voices_section"),
                                          font=ctk.CTkFont(size=13, weight="bold"))
        self.voices_title.pack(side="left")

        self.voices_scroll = ctk.CTkScrollableFrame(card, height=140,
                                                     corner_radius=8, fg_color=LOG_BG)
        self.voices_scroll.pack(fill="x", padx=12, pady=(4, 4))
        self.voices_inner = ctk.CTkFrame(self.voices_scroll, fg_color="transparent")
        self.voices_inner.pack(fill="both", expand=True)

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(6, 14))
        ctk.CTkButton(
            btn_row, text=t("add_voice"), height=36, width=190, corner_radius=8,
            fg_color="transparent", text_color=PRIMARY,
            border_width=1, border_color=PRIMARY, hover_color=PRIMARY_SOFT,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_add_voice,
        ).pack(side="left")

        # Settings
        card = ctk.CTkFrame(self.root, corner_radius=14, fg_color=CARD,
                            border_width=1, border_color=CARD_BORDER)
        card.pack(fill="x", padx=padx, pady=sect_pady)
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(row, text=t("port_label"), width=50, anchor="w").pack(side="left")
        self.port_var = ctk.StringVar()
        ctk.CTkEntry(row, textvariable=self.port_var, width=110, height=34,
                     corner_radius=8, font=ctk.CTkFont(family=_MONO, size=12),
                     justify="center").pack(side="left", padx=(4, 20))

        self.autostart_var = ctk.BooleanVar()
        ctk.CTkCheckBox(
            row, text=t("autostart"), variable=self.autostart_var,
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            border_color=MUTED, checkmark_color="#ffffff",
            font=ctk.CTkFont(size=12),
            command=self._on_autostart,
        ).pack(side="left", padx=(0, 18))

        self.tray_var = ctk.BooleanVar(value=False)
        tray_cb = ctk.CTkCheckBox(
            row, text=t("minimize_to_tray"), variable=self.tray_var,
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            border_color=MUTED, checkmark_color="#ffffff",
            font=ctk.CTkFont(size=12),
        )
        tray_cb.pack(side="left")
        if not HAS_TRAY:
            tray_cb.configure(state="disabled")
            self.tray_var.set(False)

        # URL
        card = ctk.CTkFrame(self.root, corner_radius=14, fg_color=CARD,
                            border_width=1, border_color=CARD_BORDER)
        card.pack(fill="x", padx=padx, pady=sect_pady)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(inner, text=t("url_label"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=(8, 0))
        self.url_var = ctk.StringVar()
        ctk.CTkEntry(row, textvariable=self.url_var, height=38, corner_radius=8,
                     font=ctk.CTkFont(family=_MONO, size=11)).pack(
            side="left", fill="x", expand=True)
        self.copy_btn = ctk.CTkButton(
            row, text=t("copy"), width=150, height=38, corner_radius=8,
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_copy,
        )
        self.copy_btn.pack(side="left", padx=(8, 0))

        # Actions
        actions = ctk.CTkFrame(self.root, fg_color="transparent")
        actions.pack(fill="x", padx=padx, pady=(14, 6))
        self.start_btn = ctk.CTkButton(
            actions, text=t("start"), width=160, height=46, corner_radius=10,
            fg_color=OK, hover_color=OK_HOVER,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._on_start,
        )
        self.start_btn.pack(side="left")
        self.stop_btn = ctk.CTkButton(
            actions, text=t("stop"), width=160, height=46, corner_radius=10,
            fg_color=STOP, hover_color=STOP_HOVER, state="disabled",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._on_stop,
        )
        self.stop_btn.pack(side="left", padx=(10, 0))
        ctk.CTkButton(
            actions, text="→ " + t("open_docs"), height=46, corner_radius=10,
            fg_color="transparent", text_color=PRIMARY,
            border_width=1, border_color=PRIMARY, hover_color=PRIMARY_SOFT,
            font=ctk.CTkFont(size=13),
            command=self._on_docs,
        ).pack(side="right")

        self.status_chip = ctk.CTkLabel(
            self.root, text="  " + t("status_stopped") + "  ",
            corner_radius=10, height=26,
            fg_color=CHIP_NEUTRAL, text_color=CHIP_TEXT_NEUTRAL,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.status_chip.pack(anchor="w", padx=padx + 2, pady=(2, 10))

        log_frame = ctk.CTkFrame(self.root, corner_radius=14, fg_color=CARD,
                                 border_width=1, border_color=CARD_BORDER)
        log_frame.pack(fill="both", expand=True, padx=padx, pady=(4, 16))
        ctk.CTkLabel(log_frame, text=t("log"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(
            anchor="w", padx=16, pady=(12, 6))
        self.log_text = ctk.CTkTextbox(
            log_frame, height=120, corner_radius=8, border_width=0,
            fg_color=LOG_BG, font=ctk.CTkFont(family=_MONO, size=11),
        )
        self.log_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.log_text.configure(state="disabled")

    # ---------- voices ----------
    def _refresh_voices(self):
        for w in self.voices_inner.winfo_children():
            w.destroy()
        voices = load_config().get("voices", [])
        self.voices_title.configure(text=t("voices_section") + f" ({len(voices)})")
        if not voices:
            ctk.CTkLabel(self.voices_inner, text=t("voices_empty"),
                         text_color=MUTED, font=ctk.CTkFont(size=12)).pack(pady=24)
            return
        for idx, v in enumerate(voices):
            self._make_voice_row(idx, v)

    def _make_voice_row(self, idx, v):
        row = ctk.CTkFrame(self.voices_inner, fg_color=CHIP_NEUTRAL, corner_radius=8)
        row.pack(fill="x", pady=3, padx=2)
        row.grid_columnconfigure(0, weight=1)

        name = v.get("name", "Voice")
        rid = v.get("reference_id", "")
        rid_short = rid if len(rid) <= 18 else rid[:16] + "…"

        ctk.CTkLabel(row, text=name, anchor="w",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=(12, 8), pady=8)
        ctk.CTkLabel(row, text=rid_short, text_color=MUTED, anchor="e",
                     font=ctk.CTkFont(family=_MONO, size=10)).grid(
            row=0, column=1, sticky="e", padx=(8, 10), pady=8)
        ctk.CTkButton(
            row, text="✎", width=32, height=28, corner_radius=6,
            fg_color="transparent", text_color=PRIMARY,
            border_width=1, border_color=PRIMARY, hover_color=PRIMARY_SOFT,
            font=ctk.CTkFont(size=13),
            command=lambda i=idx: self._on_edit_voice(i),
        ).grid(row=0, column=2, padx=(0, 4), pady=6)
        ctk.CTkButton(
            row, text="✕", width=32, height=28, corner_radius=6,
            fg_color="transparent", text_color=ERR,
            border_width=1, border_color=ERR, hover_color=ERR_SOFT,
            font=ctk.CTkFont(size=13),
            command=lambda i=idx, n=name: self._on_delete_voice(i, n),
        ).grid(row=0, column=3, padx=(0, 8), pady=6)

    def _on_add_voice(self):
        self._open_voice_dialog()

    def _on_edit_voice(self, idx):
        voices = load_config().get("voices", [])
        if 0 <= idx < len(voices):
            self._open_voice_dialog(idx, voices[idx])

    def _on_delete_voice(self, idx, name):
        if not messagebox.askyesno(t("confirm_delete_title"),
                                   t("confirm_delete", name=name),
                                   parent=self.root):
            return
        cfg = load_config()
        voices = list(cfg.get("voices", []))
        if 0 <= idx < len(voices):
            voices.pop(idx)
            cfg["voices"] = voices
            save_config(cfg)
            log.info(t("voice_deleted"))
            self._refresh_voices()

    def _open_voice_dialog(self, idx=None, voice=None):
        dlg = ctk.CTkToplevel(self.root)
        dlg.title(t("voice_dialog_edit") if idx is not None else t("voice_dialog_add"))
        dlg.geometry("520x340")
        dlg.resizable(False, False)
        dlg.transient(self.root)

        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 520) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 340) // 2
        dlg.geometry(f"+{max(x, 0)}+{max(y, 0)}")

        content = ctk.CTkFrame(dlg, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=22, pady=20)

        ctk.CTkLabel(content, text=t("voice_name"),
                     font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").pack(fill="x")
        name_var = ctk.StringVar(value=voice["name"] if voice else "")
        name_entry = ctk.CTkEntry(content, textvariable=name_var,
                                   height=38, corner_radius=8)
        name_entry.pack(fill="x", pady=(6, 16))

        ctk.CTkLabel(content, text=t("voice_ref_id"),
                     font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").pack(fill="x")
        rid_var = ctk.StringVar(value=voice["reference_id"] if voice else "")
        ctk.CTkEntry(content, textvariable=rid_var, height=38, corner_radius=8,
                     font=ctk.CTkFont(family=_MONO, size=11)).pack(fill="x", pady=(6, 6))
        ctk.CTkLabel(content, text=t("voice_ref_hint"), text_color=MUTED,
                     font=ctk.CTkFont(size=10), justify="left",
                     wraplength=470, anchor="w").pack(fill="x", pady=(0, 20))

        btn_row = ctk.CTkFrame(content, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom")

        def on_save():
            name = name_var.get().strip()
            rid = _extract_ref_id(rid_var.get())
            if not name:
                messagebox.showwarning(APP_TITLE, t("name_required"), parent=dlg)
                return
            if not rid:
                messagebox.showwarning(APP_TITLE, t("ref_id_required"), parent=dlg)
                return
            cfg = load_config()
            voices = list(cfg.get("voices", []))
            new_v = {"name": name, "reference_id": rid, "format": "mp3"}
            if idx is None:
                voices.append(new_v)
            else:
                voices[idx] = new_v
            cfg["voices"] = voices
            save_config(cfg)
            log.info(t("voice_saved"))
            self._refresh_voices()
            dlg.destroy()

        def on_cancel():
            dlg.destroy()

        ctk.CTkButton(
            btn_row, text=t("cancel"), command=on_cancel,
            width=120, height=40, corner_radius=8,
            fg_color="transparent", text_color=("#555", "#ccc"),
            border_width=1, border_color=CARD_BORDER, hover_color=CHIP_NEUTRAL,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            btn_row, text=t("save"), command=on_save,
            width=150, height=40, corner_radius=8,
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="right")

        dlg.bind("<Escape>", lambda e: on_cancel())
        dlg.bind("<Return>", lambda e: on_save())

        def _grab():
            try:
                dlg.grab_set()
                name_entry.focus_set()
            except Exception:
                pass
        dlg.after(80, _grab)

    # ---------- state ----------
    def _load_into_form(self):
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

    def _set_chip(self, text, kind="neutral"):
        colors = {
            "neutral": (CHIP_NEUTRAL, CHIP_TEXT_NEUTRAL),
            "ok": ((OK, OK), ("#ffffff", "#ffffff")),
            "err": ((ERR, ERR), ("#ffffff", "#ffffff")),
            "warn": ((PRIMARY, PRIMARY), ("#ffffff", "#ffffff")),
        }
        fg, fg_text = colors.get(kind, colors["neutral"])
        self.status_chip.configure(text="  " + text + "  ",
                                    fg_color=fg, text_color=fg_text)
        self._chip_state = kind

    # ---------- handlers ----------
    def _on_lang(self, *_):
        lang = self.lang_var.get()
        set_lang(lang)
        self.cfg["lang"] = lang
        save_config(self.cfg)
        messagebox.showinfo(APP_TITLE, t("restart_hint"))

    def _on_check(self):
        key = self.key_var.get().strip()
        if not key:
            messagebox.showwarning(APP_TITLE, t("key_required"))
            return
        if self._check_reset:
            self.root.after_cancel(self._check_reset)
            self._check_reset = None
        self.check_btn.configure(state="disabled", text="…")
        self._set_chip(t("checking"), "warn")
        threading.Thread(target=self._check_worker, args=(key,), daemon=True).start()

    def _check_worker(self, key):
        cfg = load_config()
        voices = cfg.get("voices", [])
        if not voices:
            self.root.after(0, self._check_done, False, t("no_voices_warn"))
            return
        rid = voices[0]["reference_id"]
        payload = json.dumps({"text": "test", "reference_id": rid, "format": "mp3"}).encode("utf-8")
        req = urllib.request.Request(
            "https://api.fish.audio/v1/tts", data=payload,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "model": cfg.get("model", "s2.1-pro-free"),
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                r.read()
            self.root.after(0, self._check_done, True, None)
        except urllib.error.HTTPError as e:
            self.root.after(0, self._check_done, False, f"HTTP {e.code}")
        except Exception as e:
            self.root.after(0, self._check_done, False, str(e))

    def _check_done(self, ok, err):
        self.check_btn.configure(state="normal", text=t("check"))
        if ok:
            self._set_chip(t("check_ok"), "ok")
            self.check_btn.configure(border_color=OK, text_color=OK)
        else:
            self._set_chip(t("check_fail", err=err), "err")
            self.check_btn.configure(border_color=ERR, text_color=ERR)
        if self._check_reset:
            self.root.after_cancel(self._check_reset)
        self._check_reset = self.root.after(4000, self._reset_check_btn)

    def _reset_check_btn(self):
        self.check_btn.configure(border_color=PRIMARY, text_color=PRIMARY)
        self._check_reset = None
        if self._chip_state in ("ok", "err"):
            self._set_chip(t("status_stopped") if not self.server
                           else t("status_running", port=self.cfg["port"]))

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
        if self._copied_reset:
            self.root.after_cancel(self._copied_reset)
        self.copy_btn.configure(text="✓ " + t("copied"), fg_color=OK, hover_color=OK_HOVER)
        self._copied_reset = self.root.after(1500, self._reset_copy_btn)

    def _reset_copy_btn(self):
        self.copy_btn.configure(text=t("copy"), fg_color=PRIMARY, hover_color=PRIMARY_HOVER)
        self._copied_reset = None

    def _on_docs(self):
        webbrowser.open(DOCS_URL)

    def _start_server(self):
        key = self.key_var.get().strip()
        if not key:
            messagebox.showwarning(APP_TITLE, t("key_required"))
            return False
        if not load_config().get("voices"):
            messagebox.showwarning(APP_TITLE, t("no_voices_warn"))
            return False
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
        self._set_chip(t("status_running", port=free), "ok")
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        return True

    def _on_start(self):
        self._start_server()

    def _on_stop(self):
        if self.server:
            self.server.stop()
            self.server = None
        self._set_chip(t("status_stopped"), "neutral")
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        if self.tray:
            self.tray.stop()
            self.tray = None

    # ---------- tray ----------
    def _start_tray(self):
        if not HAS_TRAY or self.tray is not None:
            return
        icon_path = _resource_path("assets/icon.png")
        if not icon_path.exists():
            log.warning("tray icon not found: %s", icon_path)
            return
        self.tray = TrayController(
            icon_path=str(icon_path),
            on_show=self._tray_show,
            on_quit=self._tray_quit,
            tooltip=t("tray_tooltip"),
            label_show=t("tray_show"),
            label_quit=t("tray_quit"),
        )
        if not self.tray.start():
            self.tray = None

    def _tray_show(self):
        self.root.after(0, self._do_show)

    def _do_show(self):
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        except Exception as e:
            log.error("show window: %s", e)

    def _tray_quit(self):
        self.root.after(0, self._do_quit)

    def _do_quit(self):
        if self.server:
            self.server.stop()
            self.server = None
        if self.tray:
            self.tray.stop()
            self.tray = None
        try:
            self.root.quit()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass

    def _auto_background_start(self):
        if not self.cfg.get("api_key") or not load_config().get("voices"):
            return
        if self._start_server():
            self.root.withdraw()
            self._start_tray()

    def _on_close(self):
        # If tray is active and server is running, hide instead of quit
        if HAS_TRAY and self.tray_var.get() and self.server is not None:
            self.root.withdraw()
            self._start_tray()
            log.info("Свёрнуто в трей. Правый клик по иконке → Выход.")
            return
        self._do_quit()

    # ---------- log pump ----------
    def _drain_log(self):
        try:
            while True:
                line = self.log_q.get_nowait()
                self.log_text.configure(state="normal")
                self.log_text.insert("end", line + "\n")
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except queue.Empty:
            pass
        self.root.after(200, self._drain_log)

    def run(self):
        self.root.mainloop()


def run_gui(background: bool = False) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    App(background=background).run()

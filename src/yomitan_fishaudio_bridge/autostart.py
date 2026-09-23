"""Cross-platform autostart toggle."""
import os
import sys
from pathlib import Path

APP_NAME = "YomitanFishAudioBridge"
LINUX_NAME = "yomitan-fishaudio-bridge"


def _launch_cmd() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --background'
    return f'"{sys.executable}" -m yomitan_fishaudio_bridge --background'


if sys.platform == "win32":
    import winreg
    RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

    def enable():
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, _launch_cmd())

    def disable():
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
                winreg.DeleteValue(k, APP_NAME)
        except FileNotFoundError:
            pass

    def is_enabled() -> bool:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
                winreg.QueryValueEx(k, APP_NAME)
                return True
        except FileNotFoundError:
            return False

elif sys.platform == "darwin":
    PLIST = Path.home() / "Library" / "LaunchAgents" / f"com.{LINUX_NAME}.plist"
    TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.{label}</string>
  <key>ProgramArguments</key>
  <array>
{args}
  </array>
  <key>RunAtLoad</key><true/>
</dict></plist>
"""

    def _args_xml() -> str:
        if getattr(sys, "frozen", False):
            return f"    <string>{sys.executable}</string>\n    <string>--background</string>"
        return (
            f"    <string>{sys.executable}</string>\n"
            "    <string>-m</string>\n"
            "    <string>yomitan_fishaudio_bridge</string>\n"
            "    <string>--background</string>"
        )

    def enable():
        PLIST.parent.mkdir(parents=True, exist_ok=True)
        PLIST.write_text(TEMPLATE.format(label=LINUX_NAME, args=_args_xml()), encoding="utf-8")
        os.system(f"launchctl unload {PLIST} 2>/dev/null; launchctl load {PLIST}")

    def disable():
        if PLIST.exists():
            os.system(f"launchctl unload {PLIST} 2>/dev/null")
            PLIST.unlink()

    def is_enabled() -> bool:
        return PLIST.exists()

else:
    AUTOSTART = Path.home() / ".config" / "autostart" / f"{LINUX_NAME}.desktop"

    def enable():
        AUTOSTART.parent.mkdir(parents=True, exist_ok=True)
        AUTOSTART.write_text(
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Yomitan FishAudio Bridge\n"
            f"Exec={_launch_cmd()}\n"
            "Terminal=false\n"
            "X-GNOME-Autostart-enabled=true\n",
            encoding="utf-8",
        )

    def disable():
        AUTOSTART.unlink(missing_ok=True)

    def is_enabled() -> bool:
        return AUTOSTART.exists()

"""Optional system tray integration."""
import logging
import threading

log = logging.getLogger("bridge.tray")

try:
    import pystray
    from PIL import Image
    HAS_TRAY = True
    _TRAY_ERR = None
except Exception as e:
    HAS_TRAY = False
    _TRAY_ERR = str(e)


def tray_status():
    return HAS_TRAY, _TRAY_ERR


class TrayController:
    def __init__(self, icon_path, on_show, on_quit,
                 tooltip="Yomitan FishAudio Bridge",
                 label_show="Show", label_quit="Quit"):
        self.icon_path = icon_path
        self.on_show = on_show
        self.on_quit = on_quit
        self.tooltip = tooltip
        self.label_show = label_show
        self.label_quit = label_quit
        self._icon = None
        self._thread = None

    def start(self) -> bool:
        if not HAS_TRAY:
            log.warning("tray unavailable: %s", _TRAY_ERR)
            return False
        if self._thread is not None and self._thread.is_alive():
            return True
        try:
            image = Image.open(self.icon_path)
        except Exception as e:
            log.warning("tray icon load failed: %s", e)
            return False

        def _show(icon, item):
            try:
                self.on_show()
            except Exception as e:
                log.error("tray show: %s", e)

        def _quit(icon, item):
            try:
                icon.stop()
            except Exception:
                pass
            try:
                self.on_quit()
            except Exception as e:
                log.error("tray quit: %s", e)

        menu = pystray.Menu(
            pystray.MenuItem(self.label_show, _show, default=True),
            pystray.MenuItem(self.label_quit, _quit),
        )
        self._icon = pystray.Icon(
            "yomitan-fishaudio-bridge", image, self.tooltip, menu,
        )
        self._thread = threading.Thread(
            target=self._icon.run, daemon=True, name="tray",
        )
        self._thread.start()
        return True

    def stop(self):
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None
        self._thread = None

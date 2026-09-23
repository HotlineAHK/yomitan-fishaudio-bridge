"""Very small RU/EN string table."""

LANGS = ("ru", "en")

_STRINGS = {
    "ru": {
        "app_title": "Yomitan FishAudio Bridge",
        "lang_label": "Язык:",
        "api_key_label": "API-ключ Fish Audio:",
        "api_key_hint": "Получить: https://fish.audio/app/api-keys/  (ключ показывается один раз)",
        "check": "Проверить",
        "port_label": "Порт:",
        "autostart": "Запускать при входе в систему",
        "url_label": "URL для Yomitan:",
        "copy": "Скопировать",
        "copied": "URL скопирован",
        "start": "Старт",
        "stop": "Стоп",
        "status_stopped": "Остановлено",
        "status_running": "Работает на порту {port}",
        "checking": "Проверяем…",
        "check_ok": "Ключ рабочий",
        "check_fail": "Ошибка: {err}",
        "key_required": "Введите API-ключ",
        "open_docs": "Инструкция для Yomitan",
        "log": "Журнал",
        "restart_hint": "Язык сохранён. Перезапустите окно, чтобы применить.",
        "port_busy": "Порт {old} занят, использую {new}",
        "warn_free_tier": "Напоминание: бесплатный тариф Fish Audio ограничен по кредиту.",
    },
    "en": {
        "app_title": "Yomitan FishAudio Bridge",
        "lang_label": "Language:",
        "api_key_label": "Fish Audio API key:",
        "api_key_hint": "Get one at: https://fish.audio/app/api-keys/  (shown only once)",
        "check": "Check",
        "port_label": "Port:",
        "autostart": "Start on login",
        "url_label": "Yomitan URL:",
        "copy": "Copy",
        "copied": "URL copied",
        "start": "Start",
        "stop": "Stop",
        "status_stopped": "Stopped",
        "status_running": "Running on port {port}",
        "checking": "Checking…",
        "check_ok": "Key works",
        "check_fail": "Error: {err}",
        "key_required": "Enter the API key",
        "open_docs": "Yomitan setup guide",
        "log": "Log",
        "restart_hint": "Language saved. Restart the window to apply.",
        "port_busy": "Port {old} busy, using {new}",
        "warn_free_tier": "Reminder: Fish Audio free tier is credit-limited.",
    },
}

_current = "ru"


def set_lang(lang: str) -> None:
    global _current
    if lang in _STRINGS:
        _current = lang


def get_lang() -> str:
    return _current


def t(key: str, **kw) -> str:
    s = _STRINGS.get(_current, _STRINGS["ru"]).get(key, key)
    return s.format(**kw) if kw else s

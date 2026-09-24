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

        "voices_section": "Голоса",
        "voices_empty": "Пока пусто. Нажмите «Добавить голос».",
        "add_voice": "+ Добавить голос",
        "voice_dialog_add": "Добавить голос",
        "voice_dialog_edit": "Изменить голос",
        "voice_name": "Имя",
        "voice_ref_id": "Reference ID или ссылка из Fish Audio",
        "voice_ref_hint": "Вставьте ID голоса (например, 8e468a7c…) или ссылку с fish.audio — ID определится автоматически.",
        "save": "Сохранить",
        "cancel": "Отмена",
        "confirm_delete_title": "Удаление",
        "confirm_delete": "Удалить голос «{name}»?",
        "name_required": "Введите имя голоса",
        "ref_id_required": "Введите Reference ID",
        "voice_saved": "Голос сохранён",
        "voice_deleted": "Голос удалён",
        "no_voices_warn": "Сначала добавьте хотя бы один голос",
        "minimize_to_tray": "Сворачивать в трей",
        "tray_show": "Показать",
        "tray_quit": "Выход",
        "tray_unavailable": "Трей недоступен в этой системе",
        "tray_tooltip": "Yomitan FishAudio Bridge",
        "minimize_to_tray": "Сворачивать в трей",
        "tray_show": "Показать",
        "tray_quit": "Выход",
        "tray_unavailable": "Трей недоступен в этой системе",
        "tray_tooltip": "Yomitan FishAudio Bridge",
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

        "voices_section": "Voices",
        "voices_empty": "Empty. Click \"Add voice\".",
        "add_voice": "+ Add voice",
        "voice_dialog_add": "Add voice",
        "voice_dialog_edit": "Edit voice",
        "voice_name": "Name",
        "voice_ref_id": "Reference ID or fish.audio link",
        "voice_ref_hint": "Paste the voice ID (e.g. 8e468a7c…) or a fish.audio link — the ID will be extracted automatically.",
        "save": "Save",
        "cancel": "Cancel",
        "confirm_delete_title": "Delete",
        "confirm_delete": "Delete voice \"{name}\"?",
        "name_required": "Enter a voice name",
        "ref_id_required": "Enter a Reference ID",
        "voice_saved": "Voice saved",
        "voice_deleted": "Voice deleted",
        "no_voices_warn": "Add at least one voice first",
        "minimize_to_tray": "Minimize to tray",
        "tray_show": "Show",
        "tray_quit": "Quit",
        "tray_unavailable": "Tray unavailable on this system",
        "tray_tooltip": "Yomitan FishAudio Bridge",
        "minimize_to_tray": "Minimize to tray",
        "tray_show": "Show",
        "tray_quit": "Quit",
        "tray_unavailable": "Tray unavailable on this system",
        "tray_tooltip": "Yomitan FishAudio Bridge",
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

# Yomitan FishAudio Bridge

Локальный TTS-мост между [Yomitan](https://github.com/yomitan/yomitan) и [Fish Audio](https://fish.audio/).
Работает как небольшой локальный HTTP-сервер с GUI, отдаёт озвучку по запросу Yomitan.

Local TTS bridge between Yomitan and Fish Audio. Runs as a small GUI app with an
embedded HTTP server, serves audio on demand to Yomitan.

---

## Русский

### Что это

Расширение Yomitan умеет воспроизводить аудио по нажатию на слово. Обычно оно берёт
озвучку с публичных источников. Этот мост позволяет использовать голоса Fish Audio —
в том числе клонированные — локально, без облачных прокси и сторонних серверов.

### Как устроено

- GUI на Python (tkinter), хранит API-ключ Fish Audio в конфиге.
- Локальный HTTP-сервер с эндпоинтами `/audio_list`, `/tts`, `/speakers`, `/health`.
- Кэш сгенерированного аудио — на диске, повторные запросы бесплатны.
- Автозапуск при входе в систему и фоновый режим.
- Поддержка Windows, Linux, macOS.

### Быстрый старт

1. Получите API-ключ: <https://fish.audio/app/api-keys/> → «Создать ключ API».
   Ключ показывается **один раз** — сразу скопируйте.
2. Запустите `Yomitan FishAudio Bridge`.
3. Вставьте ключ, нажмите **Проверить**.
4. Нажмите **Старт**.
5. Нажмите **Скопировать** рядом с URL.
6. В Yomitan: Настройки → Audio → **Configure audio playback sources…** →
   **Add** → выбрать созданный источник → тип **Custom URL (JSON)** →
   вставить скопированный URL во второе поле.

Подробнее: [`docs/YOMITAN.md`](docs/YOMITAN.md), [`docs/FISH_AUDIO.md`](docs/FISH_AUDIO.md).

### Важно

- **Бесплатный тариф Fish Audio ограничен по кредиту.** Когда он закончится,
  озвучка перестанет работать — это не баг приложения.
- **API-ключ хранится в открытом виде** в файле конфига. Не передавайте папку
  с конфигом третьим лицам.

### Где лежат файлы

| ОС      | Конфиг                                                  | Кэш                                               |
|---------|---------------------------------------------------------|---------------------------------------------------|
| Windows | `%APPDATA%\YomitanFishAudioBridge\config.json`          | `%LOCALAPPDATA%\YomitanFishAudioBridge\cache`     |
| Linux   | `~/.config/YomitanFishAudioBridge/config.json`          | `~/.cache/YomitanFishAudioBridge`                 |
| macOS   | `~/Library/Application Support/YomitanFishAudioBridge/` | `~/Library/Caches/YomitanFishAudioBridge`         |

---

## English

### What it is

Yomitan can play audio for a word on click. This bridge lets you plug Fish Audio
voices — including cloned ones — into Yomitan locally, without any cloud proxy.

### Quick start

1. Get an API key: <https://fish.audio/app/api-keys/> → "Create API Key".
   The key is shown **once** — copy it immediately.
2. Launch `Yomitan FishAudio Bridge`.
3. Paste the key, click **Check**.
4. Click **Start**.
5. Click **Copy** next to the URL.
6. In Yomitan: Settings → Audio → **Configure audio playback sources…** →
   **Add** → select the new source → type **Custom URL (JSON)** → paste the URL
   into the second field.

See [`docs/YOMITAN.md`](docs/YOMITAN.md) and [`docs/FISH_AUDIO.md`](docs/FISH_AUDIO.md).

### Note

- **The Fish Audio free tier is credit-limited.** When it runs out, TTS stops
  working — that is not a bug.
- **The API key is stored in plain text** in the config file. Do not share the
  config directory.

## Сборка / Build

### Локально (Linux)

```sh
./scripts/build.sh
./dist/yomitan-fishaudio-bridge
```

Бинарник в `dist/` не требует установленного Python.

### Через GitHub Actions

Workflow `.github/workflows/build.yml` собирает артефакты для Windows
и Linux при пуше тега вида `v*`:

```sh
git tag v0.1.0
git push origin v0.1.0
```

Готовые сборки появятся на странице Releases репозитория.

### Ограничения

- PyInstaller не умеет кросс-компиляцию — под каждую ОС нужен свой раннер.
  GitHub Actions делает это автоматически.
- **Windows:** сборка не подписана, SmartScreen может показать предупреждение
  («Неизвестный издатель»). Нужно нажать «Подробнее» → «Выполнить в любом случае».
- **Linux:** сборка — обычный ELF-бинарник, `.AppImage` пока не делаем.
- **macOS:** пока не поддерживается (сборка снимается с матрицы).

## Сборка / Build

### Локально (Linux)

```sh
./scripts/build.sh
./dist/yomitan-fishaudio-bridge
```

Бинарник в `dist/` не требует установленного Python.

### Через GitHub Actions

Workflow `.github/workflows/build.yml` собирает артефакты для Windows
и Linux при пуше тега вида `v*`:

```sh
git tag v0.1.0
git push origin v0.1.0
```

Готовые сборки появятся на странице Releases репозитория.

### Ограничения

- PyInstaller не умеет кросс-компиляцию — под каждую ОС нужен свой раннер.
  GitHub Actions делает это автоматически.
- **Windows:** сборка не подписана, SmartScreen может показать предупреждение
  («Неизвестный издатель»). Нужно нажать «Подробнее» → «Выполнить в любом случае».
- **Linux:** сборка — обычный ELF-бинарник, `.AppImage` пока не делаем.
- **macOS:** пока не поддерживается (сборка снимается с матрицы).

## License

MIT — see [`LICENSE`](LICENSE).

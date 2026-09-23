# Настройка Yomitan / Yomitan setup

## RU

1. Откройте настройки Yomitan (иконка шестерёнки в попапе).
2. В левом меню выберите раздел **Audio**.
3. Нажмите **Configure audio playback sources…**.
4. Нажмите **Add**.
5. В списке появится новый источник — выберите его.
6. Тип источника: **Custom URL (JSON)**.
7. Во второе поле (URL) вставьте ссылку, скопированную из приложения.
   Она выглядит так:

   ```
   http://127.0.0.1:47632/audio_list?term={term}&reading={reading}
   ```

   Порт может отличаться — берите точный URL из кнопки «Скопировать».

8. Сохраните настройки.
9. Нажмите на любое японское слово в браузере — в попапе появится
   кнопка воспроизведения с названием голоса (`Indian`).

`{term}` и `{reading}` — переменные Yomitan, они подставляются автоматически.
Не удаляйте их.

## EN

1. Open Yomitan settings (gear icon in the popup).
2. In the left menu choose **Audio**.
3. Click **Configure audio playback sources…**.
4. Click **Add**.
5. A new source appears — select it.
6. Set its type to **Custom URL (JSON)**.
7. In the second field (URL) paste the link copied from the app:

   ```
   http://127.0.0.1:47632/audio_list?term={term}&reading={reading}
   ```

   The port may differ — use the exact URL from the "Copy" button.

8. Save.
9. Click any Japanese word in the browser — a play button labelled
   `Indian` appears in the popup.

`{term}` and `{reading}` are Yomitan variables; they are substituted
automatically. Don't remove them.

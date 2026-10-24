# Инструменты создания звука

Нужен Python 3.10+; для MP3 нужен FFmpeg с `libmp3lame`. SoX и Audacity используются для ручной работы и не требуются генератору. Проверка доступности: `python3 --version`, `ffmpeg -version`, `sox --version`, `audacity --version`.

```bash
python3 tools/audio/generate_sfx.py ui.click --candidate a --variant 0
python3 tools/audio/validate_audio.py tools/audio/master/ui.click.a.0.wav
python3 tools/audio/build_audio.py ui.click
python3 tools/audio/build_audio.py --all
```

`generate_sfx.py` зависит только от стандартной библиотеки. `build_audio.py` требует FFmpeg и создаёт WAV master, mono MP3 в `frontend/public/assets/audio/<семейство>/` и типизированный `frontend/src/audio/soundManifest.ts`. `--ffmpeg /путь/к/ffmpeg` указывает локальный бинарник. Сборка одного ID не удаляет остальные записи manifest.

Ручная запись: `python3 tools/audio/build_audio.py ui.click --recording ui.click=tools/audio/recordings/wood_tap.wav`. Запись должна быть документирована в реестре. Если записи нет, тот же ID собирается синтезом. Подробности в [руководстве](../../docs/audio/production-guide.md).

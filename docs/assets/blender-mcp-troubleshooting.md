# Подключение Blender MCP

Сейчас проект использует системный Blender 5.2.2 в Linux. Аддон `blender_mcp.py` установлен в `~/.config/blender/5.2/scripts/addons`, а MCP-мост — в `~/.local/share/real-city-blender-mcp/venv`. Настройки подключения находятся в `.codex/config.toml`: `127.0.0.1:9876`. Blender должен быть запущен с графическим интерфейсом; режим `-b` не обрабатывает команды аддона.

Проверка подключения:

```bash
python3 tools/assets/blender_mcp_bootstrap.py
codex mcp list
```

После изменения MCP-конфига перезапусти клиент Codex, чтобы новые инструменты появились в его списке. Порт аддона должен совпадать с `BLENDER_PORT` в конфиге.

## Прежнее подключение через WSL/Windows

Codex работает внутри WSL Debian, а Blender обычно запущен в Windows. У них разные loopback-интерфейсы, поэтому из WSL нельзя использовать `127.0.0.1` или `localhost` для подключения к Windows-приложению.

## Правильный Host

Используй Windows host:

```text
172.28.192.1
```

Пример: если Blender MCP слушает порт `27123`, URL должен быть:

```text
http://172.28.192.1:27123
```

## Быстрая Диагностика

1. Проверить, что Blender запущен в Windows.
2. Проверить, что MCP addon включен и слушает ожидаемый порт.
3. Из WSL проверить доступность host/port:

```bash
curl http://172.28.192.1:27123
```

4. Если соединение сбрасывается, проверить Windows Firewall для этого порта.
5. Если Blender пишет файлы не в репозиторий WSL, использовать UNC-пути:

```text
\\wsl.localhost\Debian\home\nshib\projects\real-city\...
```

## Типовые Ошибки

| Симптом | Причина | Действие |
| --- | --- | --- |
| `Connection refused` | Blender/MCP не слушает порт | Запустить Blender, включить addon, проверить порт |
| `Connection reset by peer` | Blender завис или addon оборвал соединение | Перезапустить MCP addon или Blender, повторить с repair-режима |
| Файлы появились в `D:\home\...` | Windows Blender получил WSL-путь как Windows-путь | Передавать UNC-путь через path helpers |
| PNG/GLB не обновились в repo | Экспорт ушел в другой путь или не был сохранен | Проверить `generation-report.json`, лог Blender и timestamp файлов |
| `get_viewport_screenshot` не создал файл | Ограничение/сбой MCP screenshot | Использовать render review/contact sheet и явно записать ограничение в status |

## Bootstrap

Перед тяжелой генерацией запускай bootstrap:

```bash
python3 tools/assets/blender_mcp_bootstrap.py
```

Скрипт проверяет TCP-подключение к адресу и порту из `.codex/config.toml`. Проверка `get_scene_info` через MCP дополнительно подтверждает, что Blender обрабатывает команды. Если соединение недоступно, генерацию через Blender нужно повторить после восстановления MCP.

## Repair После Сбоя

Если генерация оборвалась после частичного экспорта, не запускай full без необходимости:

```bash
python3 tools/assets/generate_blender_asset.py <asset_id> --mode repair --target png
python3 tools/assets/generate_blender_asset.py <asset_id> --mode repair --target lod
python3 tools/assets/generate_blender_asset.py <asset_id> --mode repair --target manifest
python3 tools/assets/generate_blender_asset.py <asset_id> --mode repair --target contact-sheet
```

После repair обязательно прогнать соответствующий validator и обновить `docs/assets/asset-generation-status.md`.

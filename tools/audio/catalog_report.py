"""Сформировать русскоязычную таблицу звуков из manifest и SoundEvent."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
events_source = (ROOT / "frontend/src/audio/soundEvents.ts").read_text(encoding="utf-8")
manifest_source = (ROOT / "frontend/src/audio/soundManifest.ts").read_text(encoding="utf-8")
manifest = json.loads(manifest_source.split("// DATA:", 1)[1].splitlines()[0])

families = {}
for match in re.finditer(r"  (\w+): \{\s+bus: '(\w+)', priority: '(\w+)', ids: \[(.*?)\n    \],", events_source, re.S):
    family, bus, priority, block = match.groups()
    ids = re.findall(r"'([^']+)'", block)
    for sound_id in ids:
        families[sound_id] = (family, bus, priority)

overrides = {}
for sound_id, body in re.findall(r"  '([^']+)': \{([^}]+)\}", events_source.split("soundEventOverrides", 1)[1]):
    overrides[sound_id] = dict(re.findall(r"(bus|priority): '([^']+)'", body))

if set(families) != set(manifest):
    raise SystemExit(f"SoundEvent и manifest различаются: {set(families) ^ set(manifest)}")

source = {
    "ui": "Явное действие UI",
    "economy": "Подтверждение API или событие WS",
    "build": "Подтверждение API или событие WS",
    "world": "Выбор клетки / подтверждение API или WS",
    "combat": "Подтверждение атаки API или событие WS",
    "social": "Подтверждение API / опрос чата или союза",
    "ambience": "Видимый биом или активная постройка",
}
lines = [
    "# Итоговый каталог звуков",
    "",
    "Таблица сгенерирована `python3 tools/audio/catalog_report.py` из `soundEvents.ts` и `soundManifest.ts`. Конкретные условия срабатывания указаны в [матрице событий](event-matrix.md). Происхождение WAV и лицензии — в [реестре ассетов](asset-register.md).",
    "",
    "Шины и настройки: `ui` — интерфейс, `world` — игровой мир, `alerts` — предупреждения, `ambience` — атмосфера. Все зависят от `master` и общего mute; чат отдельно отключается настройкой `chat`, атмосфера — отдельным переключателем. Лимиты и cooldown определены в `soundCatalog.ts`.",
    "",
    "| `sound_id` | Первый MP3 (варианты в manifest) | Источник | Шина | Приоритет |",
    "|---|---|---|---|---|",
]
for sound_id in sorted(manifest):
    family, bus, priority = families[sound_id]
    bus = overrides.get(sound_id, {}).get("bus", bus)
    priority = overrides.get(sound_id, {}).get("priority", priority)
    lines.append(f"| `{sound_id}` | `{manifest[sound_id][0]}` | {source[family]} | `{bus}` | `{priority}` |")
lines += [
    "",
    "## Ограничения браузеров",
    "",
    "`AudioContext` разблокируется только после пользовательского жеста; `resume()` может быть отклонён. Декодирование и загрузка при медленной сети добавляют задержку первому проигрыванию. Отсутствующий MP3 переключается на следующий вариант, а при отсутствии всех вариантов звук молчит. В скрытой вкладке голоса останавливаются. Атмосферные петли работают через Web Audio; их стыки и баланс на телефоне требуют ручного прослушивания по [чек-листу](qa-checklist.md).",
    "",
]
(ROOT / "docs/audio/catalog.md").write_text("\n".join(lines), encoding="utf-8")
print(f"Записано {len(manifest)} sound_id")

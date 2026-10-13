# Конвенции Экспорта Анимаций

Документ фиксирует контракт между Blender-пайплайном, runtime manifest и frontend-рендерером карты. Мастер-источником остаются `.blend`/`.glb`, но массовая карта получает дешевые sprite/atlas-данные.

## Общие Правила

1. Все кадры рендерятся с той же изометрической камерой, что и статичные PNG ассета.
2. Для построек базовый sprite и overlay-кадры используют один anchor, обычно `[256, 292]` при размере `512x384`.
3. Для монстров допускается меньший кадр, но anchor должен быть указан явно в manifest.
4. Frame names должны быть стабильными, без пробелов и без локализованных слов.
5. Atlas JSON и image лежат рядом с runtime manifest ассета.
6. `revision` меняется при любом изменении atlas image, atlas json, кадров или anchor.

## Постройки

Постройки экспортируют статичные состояния и опциональные overlay-анимации. Overlay не должен менять силуэт здания: он добавляет дым, пыль, огонь, мерцание окон, вращение небольшого механизма или флаг.

Рекомендуемые overlay ids:

| Id | Когда используется | Тип |
| --- | --- | --- |
| `working` | активное производственное здание работает | `overlay` |
| `construction_dust` | строительство или апгрейд | `overlay` |
| `damaged_smoke` | повреждение или критическое повреждение | `shared_overlay` или `overlay` |
| `ready_to_collect` | урожай/поле готово к сбору | `overlay` |
| `under_attack` | короткий боевой эффект | `overlay` |

Имена кадров:

```text
<asset_id>_l<level>_<overlay_id>_<frame>.png
lumber_yard_l03_working_0000.png
lumber_yard_l03_working_0001.png
```

В runtime manifest overlay описывается так:

```json
{
  "animations": {
    "working": {
      "type": "overlay",
      "fps": 8,
      "frames": 12,
      "loop": true,
      "anchor": [256, 292],
      "framePrefix": "lumber_yard_l03_working_"
    }
  }
}
```

## Монстры

Монстры экспортируются как animated sprites. Минимальный набор действий:

| Action | Loop | Назначение |
| --- | --- | --- |
| `idle` | да | стоит или дышит |
| `walk` | да | движение между тайлами |
| `attack` | нет | удар или выстрел |
| `hit` | нет | получение урона |
| `death` | нет | смерть |

Минимальный набор направлений: `ne`, `nw`, `se`, `sw`. Расширение до восьми направлений допускается без изменения frontend-контракта.

Имена кадров:

```text
<monster_id>_<direction>_<action>_<frame>.png
ruins_guardian_ne_walk_0000.png
ruins_guardian_ne_walk_0001.png
```

В manifest можно использовать шаблон `{direction}`:

```json
{
  "directions": ["ne", "nw", "se", "sw"],
  "animations": {
    "walk": {
      "type": "sprite",
      "fps": 10,
      "frames": 12,
      "loop": true,
      "framePrefix": "ruins_guardian_{direction}_walk_"
    }
  }
}
```

## Contact Sheets

Каждая партия кадров должна иметь contact sheet для быстрой визуальной проверки. Сборка:

```bash
python3 tools/assets/make_animation_contact_sheet.py path/to/frames --columns 8
```

Contact sheet не является runtime-ассетом. Он нужен для ревью: порядок кадров, прыжки anchor, мерцание, лишние crop-поля, неправильное направление.

## Валидация

Перед подключением ассета к frontend registry нужно выполнить:

```bash
python3 tools/assets/validate_animation_manifests.py path/to/asset/manifest.json
```

Валидатор проверяет:

- наличие `anchor`;
- корректные `fps`, `frames`, `loop`;
- допустимые monster directions;
- наличие `atlas.image` и `atlas.json`;
- наличие нужного числа кадров в atlas JSON по `framePrefix`.

# Сгенерированные иконки ресурсов

Эта директория предназначена для PNG из Blender-генератора и runtime fallback-иконок. Иконки рендерятся крупным планом на прозрачном фоне, без нижней подложки:

```bash
blender --background --python tools/assets/blender/generate_resource_icons.py
```

Если Blender MCP/CLI недоступен, PNG для ресурсов из документации можно обновить
fallback-генератором:

```bash
python3 tools/assets/generate_resource_icon_pngs.py
```

`ResourceIcon` автоматически пробует загрузить `/assets/resources/icons/<resource-id>.png`. Если PNG еще не создан, интерфейс использует векторную fallback-иконку.

Старый набор хранится в `resource_icons.blend` с отдельными коллекциями ресурсов.
Дополнительные ресурсы из документации добавлялись как PNG-only fallback до полноценной Blender-пересборки.
Его проверка и контактные листы: `python3 tools/assets/validate_resource_models.py`.
`resource_icons_small_review.png` показывает каждый ресурс в размерах 24, 32 и 48 px.
`resource_icons_docs_fallback_review.png` и `resource_icons_docs_fallback_small_review.png`
показывают только fallback-партию.
Отдельная партия из девяти предметов категории `weapons` содержит собственные PNG, GLB и редактируемый `weapon_resources.blend`. Иконки зарегистрированы в `manifest.json` и используются реестром и верхней панелью ресурсов. Генератор: `tools/assets/blender/generate_weapon_resource_models.py`; проверка и обзор 24/32/48 px: `python3 tools/assets/validate_weapon_resource_models.py`. Подробности: `docs/assets/weapon-resource-models.md`.

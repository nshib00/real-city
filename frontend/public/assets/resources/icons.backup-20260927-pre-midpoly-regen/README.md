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

Набор содержит 74 PNG, 34 GLB и `resource_icons.blend` с отдельными коллекциями для Blender-набора.
Дополнительные ресурсы из `docs/resources-list.md` добавлены как PNG-only fallback до полноценной Blender-пересборки.
Полная проверка и контактные листы: `python3 tools/assets/validate_resource_models.py`.
`resource_icons_small_review.png` показывает каждый ресурс в размерах 24, 32 и 48 px.
`resource_icons_docs_fallback_review.png` и `resource_icons_docs_fallback_small_review.png`
показывают только fallback-партию.
Подробности: `docs/resource-model-regeneration.md`.

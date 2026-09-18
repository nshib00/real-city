# Иконки ресурсов

Иконки ресурсов генерируются в Blender единым набором:

```bash
blender --background --python tools/assets/blender/generate_resource_icons.py
```

Скрипт создает:

- `frontend/public/assets/resources/icons/resource_icons.blend` - исходная Blender-сцена со всеми ресурсами;
- `frontend/public/assets/resources/icons/<resource-id>.png` - прозрачные PNG-иконки 256x256;
- `frontend/public/assets/resources/icons/<resource-id>.glb` - отдельные модели с примененными transforms;
- `frontend/public/assets/resources/icons/resource_icons_contact_sheet.png` - общий лист для быстрой проверки набора;
- `frontend/public/assets/resources/icons/manifest.json` - список ресурсов и файлов.

Визуальный стиль: bright fantasy stylized mid-poly по `docs/visual-style-guide.md`: изометрическая камера, прозрачный фон без бейджа и подложки, читаемые материалы, аккуратные скосы и объемные детали. При добавлении ресурса обнови `RESOURCES` и `BUILDERS` в `tools/assets/blender/generate_resource_icons.py`; специализированные формы находятся в `regenerate_resource_models.py`.

После генерации выполни `python3 tools/assets/validate_resource_models.py`: проверяются полнота каталога, топология GLB, размеры и поля PNG. Валидатор создает контактный лист и проверочный лист размеров 24/32/48 px. Отчет обратного импорта записывается самим Blender-генератором.

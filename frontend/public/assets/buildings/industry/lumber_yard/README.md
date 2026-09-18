# Лесопильный двор

Сюда Blender-генератор сохраняет runtime-модели лесопилки:

```bash
blender --background --python tools/assets/blender/generate_lumber_yard_models.py
```

Ожидаемые файлы:

- `lumber_yard_levels.blend`;
- `lumber_yard_levels.glb`;
- `lumber_yard_l01_active.glb` ... `lumber_yard_l13_active.glb`;
- `lumber_yard_l01_construction.glb` ... `lumber_yard_l13_construction.glb`;
- `lumber_yard_l01_damaged.glb` ... `lumber_yard_l13_damaged.glb`;
- `lumber_yard_l01_active.png` ... `lumber_yard_l13_damaged.png`;
- `generation-report.json`.

Runtime-карта использует PNG-спрайты `lumber_yard_l<level>_<state>.png`, а GLB остаются мастер-ассетами и источником для инспекции.

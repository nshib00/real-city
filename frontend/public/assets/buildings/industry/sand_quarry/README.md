# Песчаный карьер

Сюда Blender-генератор сохраняет runtime-модели Песчаного карьера:

```bash
"/mnt/d/programs/Blender/5.2/blender.exe" --background --python tools/assets/blender/generate_sand_quarry_models.py
```

Ожидаемые файлы:

- `sand_quarry_levels.blend`;
- `sand_quarry_levels.glb`;
- `sand_quarry_l01_active.glb` ... `sand_quarry_l11_damaged.glb`;
- `sand_quarry_l01_active.png` ... `sand_quarry_l11_damaged.png`;
- `generation-report.json`;
- `roundtrip-validation.json`;
- `state-review.png`.

Runtime-карта использует PNG-спрайты `sand_quarry_l<level>_<state>.png`, а GLB остаются мастер-ассетами и источником для инспекции.

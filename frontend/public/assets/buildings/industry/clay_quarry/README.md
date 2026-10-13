# Глиняный карьер

Сюда Blender-генератор сохраняет runtime-модели Глиняного карьера:

```bash
"/mnt/d/programs/Blender/5.2/blender.exe" --background --python tools/assets/blender/generate_clay_quarry_models.py
```

Ожидаемые файлы:

- `clay_quarry_levels.blend`;
- `clay_quarry_levels.glb`;
- `clay_quarry_l01_active.glb` ... `clay_quarry_l12_damaged.glb`;
- `clay_quarry_l01_active.png` ... `clay_quarry_l12_damaged.png`;
- `generation-report.json`;
- `roundtrip-validation.json`;
- `state-review.png`.

Runtime-карта использует PNG-спрайты `clay_quarry_l<level>_<state>.png`, а GLB остаются мастер-ассетами и источником для инспекции.

# Шахта

Сюда Blender-генератор сохраняет runtime-модели Шахты:

```bash
"/mnt/d/programs/Blender/5.2/blender.exe" --background --python tools/assets/blender/generate_mine_models.py
```

Ожидаемые файлы:

- `mine_levels.blend`;
- `mine_levels.glb`;
- `mine_l01_active.glb` ... `mine_l12_damaged.glb`;
- `mine_l01_active.png` ... `mine_l12_damaged.png`;
- `generation-report.json`;
- `roundtrip-validation.json`;
- `state-review.png`.

Runtime-карта использует PNG-спрайты `mine_l<level>_<state>.png`, а GLB остаются мастер-ассетами и источником для инспекции.

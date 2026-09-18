# Ратуша

Исходный генератор: `tools/assets/blender/generate_town_hall_models.py`.

Генератор создает 10 уровней `town_hall_l01` ... `town_hall_l10` в трех состояниях:

- `active`;
- `construction`;
- `damaged`.

Ожидаемые файлы после запуска генератора в Blender:

- `town_hall_levels.blend`;
- `town_hall_levels.glb`;
- `town_hall_l01_active.glb` ... `town_hall_l10_damaged.glb`.

Все тяжелые `.blend` и `.glb` файлы игнорируются git согласно корневому `.gitignore`.

Runtime-карта использует PNG-спрайты из `frontend/public/assets/buildings/center/town_hall`, чтобы не запускать отдельный WebGL renderer для каждой постройки.

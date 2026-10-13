# Спрайты построек

Карта использует PNG-спрайты построек из этого каталога. GLB-модели остаются исходниками для более тяжелого 3D-представления, но не подключаются в основной runtime-рендер поля.

Локальный генератор PNG:

```bash
python3 tools/assets/generate_building_sprite_pngs.py
```

Ожидаемые runtime-спрайты:

- `center/town_hall/town_hall_l01_active.png` ... `town_hall_l10_damaged.png`;
- `housing/dugout/dugout_l01_active.png` ... `dugout_l05_damaged.png`;
- `housing/wood_house/wood_house_l01_active.png` ... `wood_house_l06_damaged.png`;
- `industry/lumber_yard/lumber_yard_l01_active.png` ... `lumber_yard_l13_damaged.png`.
- `industry/sand_quarry/sand_quarry_l01_active.png` ... `sand_quarry_l03_damaged.png`.

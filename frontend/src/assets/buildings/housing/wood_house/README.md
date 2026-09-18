# Деревянный дом

Исходный генератор: `tools/assets/blender/generate_wood_house_models.py`.

Текущие runtime-ассеты 1-3 уровней можно пересоздать без Blender:
`tools/assets/generate_wood_house_l01_glbs.py`.
Он генерирует:

- GLB в `frontend/src/assets/buildings/housing/wood_house`;
- PNG в `frontend/public/assets/buildings/housing/wood_house`;
- состояния `active`, `construction`, `damaged` для `wood_house_l01` ... `wood_house_l03`.

Визуальное направление ранних уровней: компактный светлый деревянный дом на 1x1
тайле, голубая двускатная крыша, труба, крыльцо, палисад, клумба и крупные
читаемые дворовые детали. 2 уровень выше и богаче за счет второго яруса,
белого палисада, балконной детали и садового инвентаря. 3 уровень получает
боковую пристройку с отдельной крышей и мощеную дорожку. Референсы
`reference/buildings/original-assets/images/5.png`, `6.png` и `51.png`
используются только как ориентир силуэта, прогрессии и плотности деталей, без
копирования исходных объектов.

Генератор создает 6 уровней `wood_house_l01` ... `wood_house_l06` в трех состояниях:

- `active` - рабочая модель;
- `construction` - рабочая модель со строительным оверлеем;
- `damaged` - поврежденная, но узнаваемая модель.

Ожидаемые экспортные файлы после запуска в Blender:

- `wood_house_levels.blend`;
- `wood_house_levels.glb`;
- `wood_house_l01_active.glb` ... `wood_house_l06_damaged.glb`.

Все тяжелые `.blend` и `.glb` файлы игнорируются git согласно корневому `.gitignore`.

Runtime-карта использует PNG-спрайты из `frontend/public/assets/buildings/housing/wood_house`, чтобы не запускать отдельный WebGL renderer для каждой постройки.

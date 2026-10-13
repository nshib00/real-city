# Real City Blender Components

Эта библиотека содержит переиспользуемые Python-фабрики деталей для
`Aeolian bright fantasy mid-poly strategy diorama`. Модули импортируются без
Blender; фактическое создание объектов происходит только при вызове функций,
которые используют общий `real_city.geometry`.

## Правила версионирования

- Текущая версия API: `2026.10.phase3.v5`.
- Новые функции добавляются без изменения поведения старых.
- Если меняются размеры, якорь, ориентация входа или смысл детали, заводится
  новая функция или явный параметр, а не скрытая правка существующей.
- Генератор должен фиксировать в своем report список использованных
  компонентов и версию библиотеки.

## Состав

- `housing.py` - землянка, деревянный дом, каменный дом, двор.
- `civic.py` - башни, ратуша, флаги, площадь, балкон, городская печать.
- `industry.py` - навесы, печи, шахтные порталы, отдельные шахтные арки
  (`wood`, `elite_wood`, `stone`, `stone_block`, `brick`, `metal`,
  `reinforced_concrete`, `crystal_reinforced`), тоннельная глубина,
  скальные щеки, рельсы, лампы, вагонетки, рудные кучи, подъемники,
  вентиляция, ящики взрывчатки, конвейеры, краны, стекольные панели и
  processing line.
- `fields.py` - грядки, почвенные ряды, log/plank walls, разные
  стилизованные основы грядок (`windleaf`, `flax`, `seed`, `mushroom`,
  `herb`, `reed`), столбы, доски, trellis и super-crop детали.
- `storage.py` - хранилища, vault body, safe cells, монеты, крыши и шипы.
- `roofs.py` - gable/hipped/shed roofs, pyramid, mansard, barrel, dome,
  stepped и asymmetric roofs, цветные крыши, черепица, `rune_tile` крыша,
  металлические/gold plate rows и roof spikes.
- `walls.py` - деревянные, каменные, металлические и золотые стены,
  cap-и, шипы, corner piers, wall-decor: S-scroll, резные/рунические
  орнаменты, белые наличники и медальоны.
- `foundations.py` - прямоугольные и круглые фундаменты разных материалов,
  высот и толщин.
- `props.py` - ящики, бочки, мешки, штабели досок, инструменты, верстаки,
  строительные леса, market bundle.
- `aeolian.py` - флюгеры, ленты, мягкие навесы, кристаллы, линзы.
- `towers.py` - круглые/квадратные башни и каменные башенки разной высоты
  и толщины, с флагом или без.
- `detail_kits.py` - facade overlays, bevel blocks, damage kit,
  texture-bake-friendly strips и readable prop clusters.
- `registry.py` - машинно-читаемый список основных компонентов для
  оркестратора и документации.

## Source `.blend` library

На текущей фазе все детали выражены Python-фабриками, поэтому бинарная
`real_city_components.blend` не обязательна. Если появятся сложные вручную
собранные collections, они должны храниться в
`tools/assets/blender/library/real_city_components.blend`, а их имена и версия
должны быть добавлены в `registry.py`.

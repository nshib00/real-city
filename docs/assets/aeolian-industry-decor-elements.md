# Декоративные элементы для industry-построек Эолии

Документ описывает 100 новых декоративных элементов для промышленных и ремесленных построек Real City: дворов, мастерских, карьеров, шахт, печей, переработки, ткацких и канатных производств. Эти элементы должны помогать читать функцию здания с карты и поддерживать bright fantasy mid-poly стиль Эолии без grimdark и без низкополигональных заглушек.

## Общие правила моделирования

- Industry-декор должен объяснять производство: входное сырье, рабочий узел, выходной продукт, энергию, безопасность или простой.
- Крупные функциональные элементы важнее микродеталей: пила, барабан, печь, желоб, стопка сырья или шкала должны читаться в 512x384.
- Ранние уровни: дерево, камень, веревка, ручные инструменты. Средние: кирпич, железо, ремни, простая механика. Поздние: бетон, сталь, медь, стеклянные шкалы, редкие золотистые калибровки.
- Не делать индустрию темной и грязной: пыль, копоть и масло допустимы локально, но карта остается светлой и читаемой.
- LOD1 удаляет болты, отдельные ручки и тонкие шланги; LOD2 оставляет главный станок/печь, сырье, выходной продукт и 1 сигнальный элемент.

## 100 элементов

1. **Стопка сырья на поддоне** - универсальный входной ресурс. В Blender сделать pallet из 3 досок и 2 поперечин, сверху 4-8 resource blocks/logs/bags по типу производства. Материалы зависят от ресурса. LOD1 - pallet и один merged stack.
2. **Маркированный выходной ящик** - готовая продукция. Crate with open top, внутри доски/слитки/мотки, на боку простая icon plate без текста. LOD1 - closed crate with colored top.
3. **Весовая платформа** - контроль партии. Low square slab, four corner bolts, small vertical dial/needle. Материалы: metal_worn, stone/concrete. LOD1 - slab and dial.
4. **Контрольная бирка качества** - rare output marker. Small hanging tag on stack, geometric star/line icon. Материалы: wood/copper/gold accent. LOD1 - tag removed.
5. **Сортировочная полка** - отделение сортов. 2-tier rack with 3 bins, each bin different material/color. LOD1 - rack with colored blocks.
6. **Рабочая тележка с ручками** - перевозка сырья. Box body, two wheels cylinders, two handles, optional resource load. LOD1 - body and wheels.
7. **Колесная тачка** - small industry prop. Bowl/tray mesh, single front wheel, two supports touching ground. LOD1 - tray and wheel.
8. **Ручной подъемный крюк** - погрузка. Vertical post, small boom, hanging hook from chain/rope; hook over load, not floating meaninglessly. LOD1 - post/boom/hook.
9. **Кран-балка малой мастерской** - поздний двор. Two posts, top I-beam, trolley block, hook. Materials metal/wood by level. LOD1 - frame and hook.
10. **Складская стойка для инструмента** - organized work. Board/rack with 3 silhouettes: hammer, tongs, saw; all oversized. LOD1 - rack with color strips.

11. **Ременная передача** - mechanical motion cue. Two cylinders as pulleys, belt as loop/curves or two strips, small axle caps. Материалы: rubber/cloth, metal/copper. LOD1 - pulleys and straight belt.
12. **Зубчатое колесо крупное** - механика поздних уровней. Gear disk with 8-12 teeth boxes around circumference, central hub. LOD1 - toothed disk simplified.
13. **Малый редукторный блок** - compact machine detail. Box casing, two gears/axles visible, bolts on corners. Материалы: metal_worn, copper. LOD1 - casing and one gear.
14. **Механический рычаг запуска** - state indicator. Base plate, angled lever, knob sphere; position can show active/idle. LOD1 - lever only.
15. **Педальный привод** - ранняя ремесленная механика. Small wheel, pedal arm, wooden frame; для ткацких/канатных. LOD1 - wheel/frame.
16. **Вал с подшипниками** - industrial structure. Cylinder shaft through two support blocks, metal rings. LOD1 - shaft and supports.
17. **Защитный кожух механизма** - safety/late upgrade. Rounded box over dangerous gear, slots as dark strips, warning stripe. LOD1 - box with stripe.
18. **Масленка на станке** - small maintenance detail. Tiny can body, long spout, handle; use near gears. LOD1 - remove.
19. **Смазочное пятно под валом** - operation wear. Irregular dark glossy plane on floor, localized and small. LOD1 - dark spot.
20. **Набор крупных болтов крепления** - readable hardware. 4-8 cylinders/disks on plates, bevel; avoid tiny microbolts. LOD1 - 2 bolts.

21. **Каменная печь с топкой** - early heat source. Block/brick body, dark arched opening, warm ember plane, chimney stub. LOD1 - body/opening.
22. **Кирпичная топка с дверцей** - mid-tier furnace. Brick rows as strips, metal door with handle, amber slit. LOD1 - furnace and slit.
23. **Металлическая печь-барабан** - компактное производство. Cylinder horizontal/vertical, legs, riveted door, short pipe. LOD1 - cylinder and pipe.
24. **Тигель на стойке** - glass/foundry detail. Small bowl/cup mesh held by metal frame, glowing contents. LOD1 - bowl and frame.
25. **Ковш разливки** - металлургия. Bucket shape with side pins, handle/chain, tilted variant for active. LOD1 - bucket.
26. **Форма для слитков** - output mold. Row of 3-5 rectangular cavities on slab, some filled metal. LOD1 - slab with colored rectangles.
27. **Охлаждающий бак** - post-processing. Open trough with water/steam hint, metal/wood sides. LOD1 - trough.
28. **Искровой щиток** - safety prop. Curved metal plate near furnace with 2 supports. LOD1 - plate.
29. **Куча угля/топлива** - input for heat. Irregular black/dark stones with small highlights, contained by low boards. LOD1 - dark mound.
30. **Зольный ящик** - waste cue. Low box with grey ash mound and small shovel. LOD1 - box/mound.

31. **Высокая труба с обручами** - silhouette for industry. Cylinder or square stack, 2-4 metal bands, dark top. LOD1 - stack and bands.
32. **Колено трубы** - pipe network. Two cylinders joined by torus/curve bend, supports touch wall/floor. Материалы: metal_worn/copper. LOD1 - bent pipe.
33. **Трубный вентиль** - readable control. Pipe with circular valve wheel 8 segments, central knob. LOD1 - pipe and wheel.
34. **Манометр со стрелкой** - late precision. Small disk on pipe, tiny needle and color zone; face should be oversized. LOD1 - disk.
35. **Стеклянный уровень жидкости** - alchemy/oil/glass. Vertical glass tube with colored liquid section and metal caps. LOD1 - colored cylinder.
36. **Фильтр-цилиндр** - cement/chemical/late craft. Vertical cylinder with perforation dots as few dark disks, top cap. LOD1 - cylinder.
37. **Вытяжной короб** - workshop roof detail. Rectangular hood above hot zone, pipe upward, brackets. LOD1 - hood and pipe.
38. **Паровыпускной клапан** - active cue. Small capped pipe, optional translucent puff only for render. LOD1 - pipe.
39. **Топливная бочка** - oil/fuel input. Cylinder 12 segments, two bands, warning color stripe. LOD1 - cylinder/bands.
40. **Канистра с носиком** - small fuel prop. Rectangular bevelled can, cap, angled spout, handle. LOD1 - can.

41. **Желоб подачи сырья** - quarry/cement/sawmill. U-shaped trough angled down, side supports; bottom end touches receiver. LOD1 - simple angled box.
42. **Деревянный лоток сортировки** - early processing. Shallow box with separators, resource pieces inside. LOD1 - tray.
43. **Каменный желоб дробилки** - mineral production. Stone U channel with chipped edges, dust plane below. LOD1 - stone trough.
44. **Металлический конвейер короткий** - late production. Two rollers, belt strip, side rails, small supports. LOD1 - belt and rollers.
45. **Роликовая направляющая** - sawmill/factory. Row of 3-5 cylinders between side beams. LOD1 - side beams and 2 rollers.
46. **Подающий барабан** - rope/textile/sawmill. Cylinder with ridges, axle supports, maybe material strip wrapped. LOD1 - cylinder.
47. **Отбойная заслонка** - quarry/ore split. Hinged plate in trough, lever handle. LOD1 - plate.
48. **Ссыпная воронка** - bulk storage. Inverted truncated cone/pyramid with legs and small outlet. LOD1 - hopper.
49. **Мешкозашивочная стойка** - packaging. Vertical post, small clamp, bag below. LOD1 - post and bag.
50. **Выходная горка продукта** - ready cue. Small pile of planks/bricks/ore/rope near output edge, shape and material specific. LOD1 - mound/stack.

51. **Ручная пила на козлах** - sawmill early. Two sawhorses, log, saw blade as thin metal plane with handle. LOD1 - log and saw silhouette.
52. **Рамная пила** - mid sawmill. Rectangular frame, vertical blade strip, guide rails, log below. LOD1 - frame/blade/log.
53. **Ленточная пила с кожухом** - late sawmill. Two pulley housings, continuous blade strip, table. LOD1 - housing/table.
54. **Штабель бревен с торцами** - wood input. 5-9 cylinders stacked, cut ends light disks, side chocks. LOD1 - merged log stack.
55. **Пачка досок с ремнями** - wood output. 6-10 boards stacked, two rope/metal straps, aligned but slight offsets. LOD1 - block with straps.
56. **Сушильная стойка досок** - processing state. Two side frames, vertical boards leaning with gaps. LOD1 - frame and board block.
57. **Премиум-доска на отдельной полке** - rare result. Small shelf with 2 polished boards, golden edge, quality tag. LOD1 - shelf/bright board.
58. **Щепа и опилки** - ground detail. Low irregular yellow-brown patches around saw, not under entire footprint. LOD1 - one patch.
59. **Топор в пне-колоде** - wood workshop prop. Short stump cylinder, axe blade/handle inserted; all supported. LOD1 - stump/axe silhouette.
60. **Мерная линейка на станке** - precision. Thin strip with 3-5 notch blocks, no numbers/text. LOD1 - strip.

61. **Стойка канатной скрутки** - rope yard core. Vertical post with hook, base block, top cap; hooks large enough. LOD1 - post/hook.
62. **Натянутые волокна льна** - active state. 3-5 parallel curves from hook to drum, bevel 0.01-0.018, not too thin. LOD1 - 2 curves.
63. **Большая бухта веревки** - ready/output. Torus/coil with 2-3 nested loops, loose end. LOD1 - torus.
64. **Катушка веревки на оси** - mechanized rope. Cylinder spool with side disks, rope material around center. LOD1 - spool.
65. **Стопка льна** - input for textile. Bundle of straw-colored cylinders/leaf strips tied with rope. LOD1 - straw block.
66. **Ткацкая рама малая** - textile workshop. Rectangular frame with vertical threads and shuttle block. LOD1 - frame/threads plane.
67. **Рулон ткани** - textile output. Horizontal cylinder with visible rolled end spiral as material or curve. LOD1 - cylinder.
68. **Красильная ванна** - dye industry. Open tub with colored liquid and cloth strip hanging over edge. LOD1 - tub/liquid.
69. **Сушильная веревка ткани** - ready state. Rope between posts, 2 cloth strips, bottom waves. LOD1 - one cloth.
70. **Бирка качественной веревки** - rare craft. Small copper/gold tag tied to clean coil. LOD1 - remove tag.

71. **Кирпичная стопка** - brick yard output. 8-14 small bricks in stepped stack, bevel, red-orange variants. LOD1 - brick block.
72. **Форма для кирпича** - clay processing. Wooden frame with 3 rectangular wet clay cells. LOD1 - frame with colored top.
73. **Глиняная яма-лоток** - clay quarry detail. Shallow warm-brown depression with glossy wet patches and shovel. LOD1 - wet patch.
74. **Камнедробильный молот** - quarry/mine. Heavy block hammer on pivot arm, resting over stone slab. LOD1 - arm/hammer.
75. **Куча каменных блоков** - output. 4-8 cuboid blocks, chipped corners, aligned by size. LOD1 - stone stack.
76. **Рудная вагонетка** - mine. Small cart with 4 wheels, ore chunks, front handle. LOD1 - cart and ore mound.
77. **Рельсовый короткий сегмент** - mine/industry. Two metal rails on 3 sleepers, flush on ground. LOD1 - rails/sleepers.
78. **Кирка у камня** - mining prop. Handle and metal pick head leaning on rock pile; contact points visible. LOD1 - pick silhouette.
79. **Пыльный мешок цемента** - cement output. Sack with grey dust patches, tied top, icon plate optional. LOD1 - sack.
80. **Бетонный блок-образец** - concrete plant. Clean cuboid with bevel, metal rebar tips optional. LOD1 - block.

81. **Стеклянные листы на стойке** - glass workshop output. 3-5 transparent blue-green planes in rack, thickness via bevel/solidify. LOD1 - colored planes.
82. **Пузырчатый стеклянный шар** - glass craft detail. Small translucent sphere/ellipsoid on stand, few highlights. LOD1 - remove or simple sphere.
83. **Линзовый держатель** - optical/late production. Ring frame, glass lens disk, adjustable side knobs. LOD1 - ring/disk.
84. **Медная трубка охлаждения** - glass/foundry. Curved copper tube around vessel, 2 supports. LOD1 - curve.
85. **Набор колб без алхимии** - chemical/processing. 2-3 simple glass vessels with muted liquid, placed in rack. LOD1 - colored cylinders.
86. **Светокристальный индикатор** - rare late indicator. Thin amethyst hex crystal in metal socket, weak emission, only where justified. LOD1 - crystal/socket.
87. **Изумрудный пылевой контейнер** - rare material storage. Small sealed jar with green powder plane and metal lid. LOD1 - jar as colored cylinder.
88. **Золотой калибровочный винт** - prestige, not luxury. Small screw/knob on precision machine, muted gold. LOD1 - gold dot/knob.
89. **Медная шкала настройки** - late machine. Arc plate with 3 tick marks as raised strips and pointer. LOD1 - arc and pointer.
90. **Защитный стеклянный экран** - safety. Transparent pane in metal frame before hot/fast component. LOD1 - frame only or pane.

91. **Предупреждающая полосатая кромка** - safety readability. Yellow/amber strips on edge of platform or machine guard; geometry bands, no text. LOD1 - material stripe.
92. **Ограждение рабочей зоны** - platform boundary. Low posts with 2 rails, height below main machine, no floating gaps. LOD1 - rail segment.
93. **Съемная ремонтная панель** - maintenance. Rectangular metal plate with 4 bolts and one handle, attached to machine casing. LOD1 - plate.
94. **Открытый люк обслуживания** - idle/repair. Hinged panel angled open, dark cavity inside, panel still attached. LOD1 - dark rectangle.
95. **Разбросанные инструменты ремонта** - damaged/repair. 2-4 oversized tools on ground: wrench, hammer, pry bar. LOD1 - one tool silhouette.
96. **Сломанный ремень** - damaged state. Belt strip collapsed on floor, one end still on pulley. LOD1 - dark strip.
97. **Погнутый поручень** - damaged industry. Rail segment tilted but connected at one post, second post broken on ground. LOD1 - tilted rail.
98. **Дымный след простоя** - idle_no_fuel/damaged render detail. Dark soot patch near furnace/pipe, optional translucent puff only in PNG source. LOD1 - soot patch.
99. **Контейнер брака** - failed output/damaged. Small bin with broken pieces: cracked bricks, snapped boards, bad rope. LOD1 - bin.
100. **Модуль состояния производства** - reusable status cluster. Комбинировать входной ресурс, рабочий рычаг, маленький gauge и выходной ящик в один prefab; visibility переключает `active`, `ready`, `idle_no_input`, `damaged`. LOD1 - resource + output box + gauge.

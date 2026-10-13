# Декоративные элементы для домов Эолии

Документ описывает 100 новых декоративных элементов для жилых построек Real City: землянок, деревянных домов, каменных домов, городских домов и поздних жилых апгрейдов. Цель - дать компонентной библиотеке набор деталей, из которых можно собирать более богатые mid-poly дома без перехода в перегруженную или чужую стилистику.

## Общие правила моделирования

- Дом должен оставаться домом: декор усиливает обжитость, материал апгрейда и эолийский мотив ветра, но не превращает жилье в мастерскую, храм или склад.
- Окна, двери, трубы и рамы моделировать встроенными в стены: сначала темная ниша или inset-плоскость, затем рама, стекло/дверь и только потом мелкий декор.
- Для деревянных домов обязательно читать доски: отдельные панели, швы, торцевые накладки, видимые балки и крепеж, но без микродосок, которые сольются в шум.
- Для поздних домов использовать богатство через качество материалов: полированные элитные доски, ровную кладку, стекло, медь, аккуратные фонари, а не чрезмерное золото.
- LOD1 удаляет ручки, мелкие гвозди и отдельные цветы; LOD2 оставляет силуэт крыши, трубу, 1-2 окна, дверь и крупный двор.

## 100 элементов

1. **Утопленная деревянная дверь с нишей** - базовая входная деталь. В Blender сделать темный прямоугольный inset на стене, внутрь поставить 3-5 вертикальных досок с bevel, две поперечины и ручку. Материалы: wood_warm, shadow_dark, metal_worn. LOD1 - цельная дверь и ниша.
2. **Арочная дверь землянки** - вход в склон/дерн. Моделировать темную арку как half-cylinder opening, вокруг 5-7 бревен/камней; дверь слегка глубже фасада. Материалы: earth_shadow, log_brown, wood. LOD1 - арка и дверная плоскость.
3. **Каменная дверная арка** - для каменных домов. Собрать 7 клиновидных блоков вокруг входа, нижние блоки крупнее, швы темные. Материалы: stone_light variants. LOD1 - цельная арка.
4. **Дверь с верхним окошком** - развитое жилье. Дощатая дверь, сверху маленькая glass inset с 2 перекладинами; стекло утоплено на 0.01 м. Материалы: wood_dark, glass_bluegreen. LOD1 - дверь и цветное окно.
5. **Дверь из элитных досок** - поздний жилой апгрейд. 4 широкие темные полированные доски, тонкая медная рамка, маленькие заклепки по краям. Материалы: premium_wood, copper_clean. LOD1 - панель с рамкой.
6. **Металлическая квартирная дверь** - городское позднее жилье. Rectangular inset, металлическое полотно, 3 horizontal ribs, маленький смотровой slit. Материалы: metal_worn, iron_dark. LOD1 - полотно и ribs.
7. **Дверная ручка-кольцо на шайбе** - читаемый входной акцент. Torus 12-16 segments, disk washer, pin; ставить на дверь, не на стену. Материалы: iron_dark. LOD1 - диск.
8. **Кованая дверная петля** - боковая функциональная деталь. Два коротких metal strips с круглыми pivot disks, крепятся к раме и двери. LOD1 - один strip.
9. **Дверной козырек на кронштейнах** - защищенный вход. Small sloped roof plane/box, две triangular side braces, нижний край не перекрывает дверь. Материалы: roof/wood/metal по дому. LOD1 - roof and braces.
10. **Порог из трех плит** - связь дома с ground. 3 beveled stone slabs перед дверью, высота 0.04-0.07 м, касаются земли. Материалы: stone_light, moss edge. LOD1 - одна плита.

11. **Прямоугольное окно с глубокой рамой** - основной оконный модуль. Сделать темную нишу, 4 деревянные рейки с bevel, стекло глубже рамы, 1 вертикальная перекладина. Материалы: wood, glass. LOD1 - рама и стекло.
12. **Квадратное окно землянки** - маленькая ранняя деталь. Ниша в фасаде, простая рама из 4 коротких beams, glass/amber plane. Материалы: dark wood, warm glass. LOD1 - квадратная цветная вставка.
13. **Круглое чердачное окно** - сказочный фронтон. Torus/ring 16 segments, glass disk, crossbar; крепить к фронтону. Материалы: wood_dark or metal, glass_cyan. LOD1 - ring and disk.
14. **Овальное окно с медной рамкой** - поздний эолийский акцент. Oval curve bevel или scaled torus, 2 thin crossbars, glass slightly blue-green. LOD1 - oval disk.
15. **Двойное окно с общей ставней** - средние дома. Две ниши рядом, общая верхняя балка, боковые ставни. Материалы: wood_warm, glass. LOD1 - two glass rectangles.
16. **Окно с цветочным ящиком** - обжитость. Под рамой box-planter с 3 leaf clumps и 2 flowers; ящик крепится к стене и не висит. LOD1 - planter with green plane.
17. **Ставни с прорезью-ветром** - мотив Эолии. Две ставни из 2 boards, на каждой светлая/темная swirl-like накладка без boolean. LOD1 - simple shutters.
18. **Оконная решетка из дерева** - ранняя защита. 2 vertical и 1 horizontal thin beams перед стеклом, с небольшим выступом. Материалы: wood_dark. LOD1 - cross.
19. **Металлическая оконная рама** - позднее жилье. Thin metal frame, 2 crossbars, маленькие rivets по углам. Материалы: metal_worn, glass. LOD1 - frame only.
20. **Теплая внутренняя подсветка окна** - вечерний уют. Добавить behind-glass amber plane/emission low strength; не заливать стену. LOD1 - amber material only.

21. **Дощатая вертикальная обшивка** - деревянный фасад. 6-10 beams/boxes с разной шириной и микроглубиной, без пустых дыр. Материалы: 3 wood tones. LOD1 - панель с material slots.
22. **Горизонтальная бревенчатая стена** - раннее жилье. 4-6 half cylinders/logs stacked, торцы видны на углу, швы темные. LOD1 - grooved panel.
23. **Косая дощатая заплатка** - ремонт/обжитость. 2-3 boards под углом поверх стены, гвозди крупными дисками. Материалы: fresh wood, metal. LOD1 - одна board.
24. **Элитная фасадная панель** - поздний деревянный дом. Large polished panel, inset border, subtle diagonal trim, copper pins. Материалы: premium_wood. LOD1 - panel with border.
25. **Каменная кладка крупными блоками** - каменный дом. 5-9 irregular blocks on фасад, bevel 0.02-0.04, darker grout. LOD1 - blocky panel.
26. **Кирпичный пояс между этажами** - городской рост. Row of 8-12 bricks or segmented strip, slightly protruding. Материалы: brick_warm. LOD1 - single strip.
27. **Угловая деревянная стойка** - конструктивная логика. Vertical beam на углу здания, bevel, top/bottom caps. Материалы: wood_dark. LOD1 - beam.
28. **Угловая каменная лопатка** - каменный укрепленный угол. Stack of 3-5 blocks with alternating sizes, slightly protruding. LOD1 - tall block.
29. **Металлическая скоба ремонта** - damaged/repaired detail. U/L-shaped strips over crack, 2-4 bolts. Материалы: iron_dark. LOD1 - strip.
30. **Фасадная трещина с раскрытым краем** - damaged only. Dark thin irregular strip plus 2 offset stone/wood chips; не использовать как обычный декор. LOD1 - dark line.

31. **Двускатная крыша из досок** - эталон деревянного дома. Делать два roof planes/mesh thickness 0.08-0.14 м, поверх 5-9 broad planks вдоль ската, торцы разной длины. Материалы: wood roof tones. LOD1 - roof with 2 color bands.
32. **Крыша из дранки** - ранний апгрейд. Small overlapping rows of rectangular shingles, 3-5 рядов на скат, без слишком мелкой сетки. Материалы: shingle_brown variants. LOD1 - row strips.
33. **Трапециевидная крыша** - компактный силуэт. Mesh with wider lower edge, short ridge, thickness; добавить raised end caps. Материалы: tile/wood. LOD1 - simple roof.
34. **Плоская крыша с бортиком** - городской поздний дом. Low slab, parapet beams around edges, small drain. Материалы: stone/concrete/metal. LOD1 - slab and parapet.
35. **Мансардная крыша** - развитое жилье. Two-tier roof slope per side, lower steep plane, upper shallow plane; добавить dormer window. LOD1 - simplified two-slope mesh.
36. **Дерновая крыша землянки** - раннее жилье. Low mound mesh with grass patches and leaf clusters, входная часть укреплена. Материалы: earth, grass. LOD1 - mound.
37. **Листовая крыша ветролиста** - переход от землянки. Large overlapping leaves, 5-11 pieces, central ridge, visible stems. LOD1 - 5 leaves.
38. **Руническая черепичная полоса** - редкая кровля. 3-7 tiles as beveled boxes along ridge/edge, 1-2 with simple rune geometry. Материалы: muted blue/green tile. LOD1 - strip.
39. **Изогнутый конек крыши** - эолийский верх. Beam along ridge, two upturned tips from short curved/angled beams. Материалы по крыше. LOD1 - beam.
40. **Торцевые доски фронтона** - аккуратный край крыши. 3-5 vertical boards on gable, uneven ends, nail disks. LOD1 - single gable plate.

41. **Каменная труба землянки** - ранний дымоход. Stack 3-5 irregular stones around dark center, small cap stone. Материалы: stone, soot. LOD1 - block chimney.
42. **Кирпичная труба с обручем** - деревянный дом. Rectangular prism with 3-4 brick rows as strips, metal band, dark top. LOD1 - prism and top.
43. **Дымник с ветровым колпаком** - эолийский силуэт. Chimney base plus thin post and sloped cap, cap повернуть по ветру. Материалы: brick/metal. LOD1 - chimney and cap.
44. **Двойная труба позднего дома** - городской объем. Two connected chimneys on shared base, different height, metal caps. LOD1 - two prisms.
45. **Малый вентиляционный грибок** - roof detail. Short cylinder, flattened cap, base ring; for kitchens/late houses. LOD1 - cylinder and cap.
46. **Теплый дымовой шлейф** - render-only optional. 2-3 translucent puffs above chimney, use only PNG/source, not heavy GLB runtime. LOD - отключать.
47. **Сажа у выхода трубы** - material decal geometry. Dark irregular plane/strip around top or roof contact. LOD1 - material darkening.
48. **Трубная подпорка** - конструктивная логика. Thin metal/wood brace from chimney to roof, ends touch both surfaces. LOD1 - one brace.
49. **Каменный дымоходный фартук** - защита крыши. 4 small slabs around chimney base, slight overlap roof. LOD1 - one base plate.
50. **Декоративная искрогасительная сетка** - late detail. Small cage of 4 posts and top ring over chimney. LOD1 - cap only.

51. **Крыльцо из двух ступеней** - входной объем. 2 rectangular steps, side beams, top platform; align with door threshold. Материалы: wood/stone. LOD1 - 2 steps.
52. **Каменное крыльцо с плитами** - поздний дом. 3 slabs, side low walls, bevel; мох по краям. LOD1 - one slab block.
53. **Деревянные перила крыльца** - обжитость. 2 posts, top rail, 1 diagonal support, no gaps from posts. LOD1 - posts and rail.
54. **Коврик из ветролиста** - бытовой акцент. Thin rectangle with 3 leaf strips and light veins before door. LOD1 - green rectangle.
55. **Домашний фонарь у двери** - теплое жилье. Wall bracket, hanging lantern hex cylinder, amber glass. LOD1 - bracket and lantern.
56. **Поленница у стены** - ранний дом. 4-8 log cylinders stacked, side supports. Материалы: bark_dark, cut_light. LOD1 - 3 logs.
57. **Ящик с домашними вещами** - двор. Crate with lid slightly open, cloth roll visible. LOD1 - closed crate.
58. **Маленькая лавка у стены** - жилой уют. Seat board, two legs, optional backrest, touches ground/wall. LOD1 - simple bench.
59. **Керамический горшок у двери** - двор. Small pot cylinder, plant leaves/flower. LOD1 - pot with green top.
60. **Подвесной горшок под карнизом** - vertical decor. Hook, short rope, bowl pot, trailing leaves; rope touches hook/pot. LOD1 - pot and hook.

61. **Флюгер-лист** - домовой силуэт. Thin pole, leaf-shaped plate, small pivot sphere; на конек/трубу. Материалы: metal/patina. LOD1 - pole and leaf.
62. **Мини-ветроколесо на фронтоне** - мотив ветра. Hub cylinder, 4 leaf-like blades, diameter 0.18-0.3 м. LOD1 - cross.
63. **Ленточка на карнизе** - мягкий movement cue. Cloth strip 2-3 segments, attached to small nail/peg. LOD1 - one strip.
64. **Семейный флажок без герба** - владелец/уют. Small pole and triangular flag with color only, no copyrighted symbols/text. LOD1 - flag plane.
65. **Ветровая подвеска из трех пластин** - эолийский звук. Bracket, three small metal/wood plates hanging at different heights. LOD1 - one plate.
66. **Дуга-орнамент над окном** - soft architecture. Curved beam/strip above window, ends touch wall. Материалы: wood/stone. LOD1 - arc.
67. **Спиральная накладка на ставне** - late motif. Thin raised strip shaped like simple curl; avoid text/runes. LOD1 - remove.
68. **Парусный боковой навес** - wind shelter. Triangular cloth plane between wall and two posts, slight sag. LOD1 - triangle cloth.
69. **Фасадная лента праздника** - rare decorative state. 3-5 small cloth triangles on rope under roof, for ready/upgrade celebration. LOD1 - rope only.
70. **Каменный ветровой носик-водосток** - utility decor. Short U-shaped spout from roof edge, angled outward. LOD1 - block spout.

71. **Малый балкончик** - поздний дом. Platform slab/wood, 2 supports, low rail, door/window behind. Footprint не расширять слишком сильно. LOD1 - platform and rail.
72. **Чердачный слуховой проем** - roof detail. Small dormer box, tiny roof, window inset. LOD1 - dormer block with glass.
73. **Боковая пристройка-кладовка** - silhouette growth. Small attached volume with own roof, door/vent; shares wall. LOD1 - attached block.
74. **Крытая дровница** - service side. Two posts, tiny roof, stack logs below. LOD1 - roof and log block.
75. **Низкая каменная ограда двора** - house boundary. 5-8 stones/blocks, height below window, broken opening at path. LOD1 - 3 block line.
76. **Деревянный палисадник** - garden edge. Short pickets connected by two rails, gaps controlled, not defensive wall. LOD1 - rail panel.
77. **Маленькая садовая грядка у дома** - domestic food patch. 2 rows plants, tiny border, no production marker. LOD1 - green patch.
78. **Колодезный ведерный уголок** - не полноценный колодец. Small bucket, rope coil, stone slab, placed near house. LOD1 - bucket and slab.
79. **Почтовая/объявительная доска** - city life. Small board on post near door, 2 pinned paper planes without text. LOD1 - board.
80. **Настенный крюк с плащом** - lived-in facade. Hook and cloth shape hanging by door, cloth touches hook and wall. LOD1 - cloth patch.

81. **Сломанная ставня** - damaged house. One shutter tilted, lower hinge detached but upper touches frame; add splinter. LOD1 - tilted shutter.
82. **Выбитое стекло с осколками** - damaged. Window frame with missing glass, 2-4 triangular glass shards on sill/ground. LOD1 - dark empty window.
83. **Обвалившийся край крыши** - damaged silhouette. Remove/shorten roof corner, add broken boards supported by wall/ground debris. LOD1 - broken roof plane.
84. **Сгоревшая доска фасада** - damage material. Dark plank with charred edge geometry/plane; not just color on whole wall. LOD1 - dark strip.
85. **Треснувшая труба** - damaged. Chimney separated into tilted blocks, but lower block remains supported. LOD1 - tilted chimney.
86. **Рассыпанная черепица** - damaged/repair. 3-6 roof tiles on ground near wall, bevel boxes. LOD1 - tile patch.
87. **Временная подпорка стены** - repair/construction. Diagonal beam from ground to wall, both ends touch surfaces, plus wedge at base. LOD1 - beam.
88. **Строительные леса у дома** - construction. 2 vertical poles, 2 horizontal rails, plank platform; no finished facade hidden entirely. LOD1 - frame.
89. **Незакрытый оконный проем** - construction. Dark opening, rough frame beams, no glass; add plank leaning nearby. LOD1 - opening.
90. **Сложенные доски апгрейда** - construction/yard. Stack 4-7 boards with straps, near wall, all grounded. LOD1 - stack block.

91. **Птичья полка без птиц** - roof life detail. Tiny shelf under eave, triangular support, small straw pad. LOD1 - shelf.
92. **Сушащаяся ткань на веревке** - household detail. Rope between wall posts, 2 cloth rectangles with slight wave. LOD1 - rope and one cloth.
93. **Ковер на перилах** - rich house. Rectangular cloth draped over rail, two sides visible, simple border pattern via material stripes. LOD1 - cloth.
94. **Медная номерная пластина без цифр** - urban marker. Small plate near door with geometric notch, no text. LOD1 - plate.
95. **Малый дворовый фонтанчик-чаша** - high-tier residential. Stone bowl, tiny water disk, 2-3 stones; keep below windows. LOD1 - bowl.
96. **Стеклянная теплая вставка крыши** - late comfort. Small skylight frame on roof, blue-green glass, 2 crossbars. LOD1 - glass rectangle.
97. **Наружная лестница к мансарде** - compact vertical detail. 2 side beams, 4-6 steps, leans against wall; bottom on ground, top at platform. LOD1 - ladder plane.
98. **Декоративный каменный цоколь** - foundation richness. Row of large stones around base, bevel, moss; avoid raised thick platform. LOD1 - stone strip.
99. **Теплая подвальная решетка** - lower facade detail. Small dark inset near foundation with 2 bars, amber hint. LOD1 - dark rectangle.
100. **Домовой комплект обжитости** - prefab cluster. Комбинировать коврик, горшок, маленький ящик и фонарь в один reusable module у двери; каждый элемент имеет contact point и может отключаться по LOD. LOD1 - коврик и горшок.

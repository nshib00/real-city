# Статус генерации ассетов

Документ служит короткой рабочей памятью для следующих итераций генерации
моделей. Обновляй его после каждой крупной партии ассетов, чтобы не повторять
в чате длинную историю требований, логов и проверок.

## Как использовать

- В новых запросах можно писать: "продолжи по `docs/assets/asset-generation-status.md`".
- Подробные правила стиля держи в `skills/real-city-blender-models/SKILL.md`.
- Большие Blender-логи не вставляй в чат; проверяй конкретный локальный файл лога и пересказывай только итог или ошибку.
- Финальный ответ по ассетам проси в коротком формате: что изменено, куда
  сохранено, какие проверки прошли, что осталось.

## Правила Обновления Status И Логов

Обновляй этот файл после каждой крупной партии, repair-сессии, изменения пайплайна или незавершенного сбоя. Запись должна быть короткой и пригодной для продолжения без чтения всей истории чата.

Фиксируй:

- `asset_id`, category, уровни, состояния или shape-варианты;
- входной spec и генератор/orchestrator;
- runtime-папку, master `.blend`, manifest, generation report и contact sheet;
- количество созданных PNG/GLB и наличие LOD0/LOD1/LOD2;
- triangle count/bounds только диапазоном или ссылкой на report;
- проверки: MCP bootstrap, visual review, manifest, PNG, LOD, roundtrip, frontend tests;
- ограничения: `mcp_unavailable`, `generation_failed`, `export_failed`, `visual_review_failed`, `validation_failed`;
- следующий практический шаг.

Не фиксируй здесь длинные Blender tracebacks, JSON reports целиком, списки всех объектов сцены и полные списки файлов, если их можно восстановить из manifest. Длинные логи оставляй в `/tmp` или рядом с ассетной партией и указывай путь.

Минимальный шаблон записи:

```text
## <Название партии>

Рабочие файлы:
- Spec: `docs/assets/specs/.../<asset_id>.yaml`.
- Генератор: `tools/assets/...`.
- Runtime-папка: `frontend/public/assets/buildings/.../<asset_id>/`.
- Contact sheet: `...`.

Состояние на YYYY-MM-DD:
- Создано: <N> PNG, <N> GLB, LOD: <да/нет/частично>.
- Preview/full/repair: <режим>.
- Проверки: <список>.
- Ограничения: <если есть>.
- Следующий шаг: <если есть>.
```

## Общий статус

- Стиль Real City для Blender-моделей закреплен в
  `skills/real-city-blender-models/SKILL.md` и `docs/art/visual-style-guide.md`.
- Для построек используются active/construction/damaged состояния.
- Для construction/damaged основание земли должно совпадать с active того же
  уровня по геометрии, материалам, UV, положению, камере и anchor.
- Construction должен показывать неполностью построенный объект, а не готовую
  модель с добавленными лесами.
- Damaged должен показывать крупные реальные разрушения, а не только пятна или
  перекраску.
- Видимые материалы модели должны отражать ресурсы, использованные при
  строительстве или апгрейде.

## Завершенные партии

- Землянки: модели всех уровней пересобирались в стиле Real City; поздние
  уровни должны явно показывать постепенный апгрейд, ветролист и деревянный
  фундамент у 5 уровня.
- Деревянные дома: уровни 1-6 пересобирались с активными состояниями и
  вариантами construction/damaged.
- Ратуши: уровни 1-10 пересобирались отдельным пайплайном.
- Terrains: модели terrain пересобирались отдельным пайплайном.
- Ресурсы: GLB-модели и PNG-иконки игровых ресурсов пересобирались отдельным
  пайплайном; ресурсы из документации, которых еще нет в игровом каталоге,
  получили runtime PNG-only fallback-иконки.
- Грядки ветролиста: уровни 1-3 пересобраны через Blender MCP в стиле Real
  City fantasy/mid-poly. Есть мастер `.blend`, runtime GLB/PNG для обычных
  стадий 1-4, active, construction, damaged и супер-стадий 1-6 на всех трех
  уровнях.
- Грунтовая дорога: создан модульный Blender-набор всех форм автосшивки
  `single`, тупиков, прямых, углов, Т-узлов и `cross` для состояний
  `active`, `construction`, `damaged`, `ruined`.
- Дороги и стены без грунтовой/глиняной дороги: создан модульный Blender-набор
  `common_road`, `paved_road`, `wooden_wall`, `stone_wall`,
  `reinforced_wall` для всех форм автосшивки и состояний.
- Глиняный карьер: уровни 1-12 созданы через Blender MCP; есть 36 GLB, 36 PNG,
  мастер `.blend`, combined GLB, manifest, generation report и contact sheet.
- Для построек ранее добавлялось правило совпадения земли у active,
  construction и damaged состояний.

## Грунтовая дорога

Рабочие файлы:

- Blender-пайплайн: `tools/assets/blender/generate_ground_road_models.py`.
- Runtime-папка: `frontend/public/assets/buildings/roads/ground_road/`.
- Мастер-сцена: `frontend/public/assets/buildings/roads/ground_road/ground_road.blend`.
- Manifest: `frontend/public/assets/buildings/roads/ground_road/manifest.json`.
- Визуальный обзор:
  `frontend/public/assets/buildings/roads/ground_road/ground_road_contact_sheet.png`.

Состояние на 2026-09-22:

- Создано 64 GLB и 64 PNG: 16 форм автосшивки x 4 состояния.
- Формы: `single`, `end_n`, `end_e`, `end_s`, `end_w`, `straight_ns`,
  `straight_ew`, `corner_ne`, `corner_es`, `corner_sw`, `corner_wn`,
  `t_nes`, `t_esw`, `t_swn`, `t_wne`, `cross`.
- Состояния: `active`, `construction`, `damaged`, `ruined`.
- PNG имеют размер 512x512, RGBA, прозрачный фон вне изометрической клетки.
- Визуальный стиль: темно-коричневая глиняная дорога с колеями,
  шероховатостями, мелкими камнями, травой по краям, свежими кучками глины в
  construction и выбоинами/заросшими участками в damaged/ruined.
- Проверки: локальная проверка manifest, существования всех PNG/GLB, размера и
  непустоты PNG, GLB header, максимального числа треугольников
  (`triangles_max: 3596`) и `git diff --check`.
- Blender MCP подтвердил сцену `Real_City_Ground_Road`, но
  `get_viewport_screenshot` не создал файл; визуальная проверка выполнена по
  runtime contact sheet.

## Обычные дороги, мостовые и стены

Рабочие файлы:

- Blender-пайплайн:
  `tools/assets/blender/generate_roads_and_walls_models.py`.
- Runtime-папки:
  - `frontend/public/assets/buildings/roads/common_road/`;
  - `frontend/public/assets/buildings/roads/paved_road/`;
  - `frontend/public/assets/buildings/roads/wooden_wall/`;
  - `frontend/public/assets/buildings/roads/stone_wall/`;
  - `frontend/public/assets/buildings/roads/reinforced_wall/`.

Состояние на 2026-09-29:

- Сгенерированы все типы дорог и стен, кроме уже готовой грунтовой/глиняной
  дороги:
  - `common_road` - Обычная дорога;
  - `paved_road` - Мостовая;
  - `wooden_wall` - Деревянная стена;
  - `stone_wall` - Каменная стена;
  - `reinforced_wall` - Усиленная стена.
- У каждого семейства есть 64 GLB и 64 PNG: 16 форм автосшивки x 4 состояния.
- Формы: `single`, `end_n`, `end_e`, `end_s`, `end_w`, `straight_ns`,
  `straight_ew`, `corner_ne`, `corner_es`, `corner_sw`, `corner_wn`,
  `t_nes`, `t_esw`, `t_swn`, `t_wne`, `cross`.
- Состояния: `active`, `construction`, `damaged`, `ruined`.
- У каждого семейства есть `.blend`, `manifest.json` и
  `roundtrip-validation.json` на 64 GLB.
- Проверки прошли: Blender MCP `get_addon_status`/`get_scene_info`, генерация
  через Blender MCP, сверка manifest против PNG/GLB, roundtrip-импорт всех GLB
  без non-manifold ошибок.
- `get_viewport_screenshot` снова не создал файл в Blender MCP. Визуальная
  проверка выполнена через Blender render review-сцены
  `/tmp/roads_walls_review.png`.
- Ограничение текущей партии: ассеты пока не подключены к frontend runtime
  renderer/catalog lookup; создан именно модельный/runtime-набор файлов.

## Шахта

Рабочие файлы:

- Blender-пайплайн: `tools/assets/blender/generate_mine_models.py`.
- Runtime-папка:
  `frontend/public/assets/buildings/industry/mine/`.
- Мастер-сцена:
  `frontend/public/assets/buildings/industry/mine/mine_levels.blend`.
- Combined GLB:
  `frontend/public/assets/buildings/industry/mine/mine_levels.glb`.
- Manifest:
  `frontend/public/assets/buildings/industry/mine/manifest.json`.
- Отчет генерации:
  `frontend/public/assets/buildings/industry/mine/generation-report.json`.
- Визуальный обзор:
  `frontend/public/assets/buildings/industry/mine/state-review.png`.

Состояние на 2026-10-10:

- Пересобрано 36 GLB и 36 PNG: уровни 1-12, состояния `active`,
  `construction`, `damaged`.
- Наружная арка шахты заменена на компонентную
  `real_city.components.industry.add_mine_arch`, масштабируется по размеру
  скалы и сохраняет один внешний портал без второй внутренней арки.
- Скальная масса стала более угловатой: добавлены острые фронтальные каменные
  выступы, верхние гребни, сколы и отдельные фасеточные глыбы; модель остается
  компактной в 1x1 footprint.
- Прогрессия уровней усилена: дерево и веревки на ранних уровнях, камень,
  кирпич и железные крепления на средних, бетон/железобетон, вентиляция,
  защищенные ящики взрывчатки, супер-механизмы, светокристаллы и бронепластины
  на поздних.
- Проверки прошли: Blender MCP `get_addon_status`/`get_scene_info`,
  preview уровней 1/6/12, full Blender generation, визуальный review
  `state-review.png`, manifest validation с triangles/bounds, PNG sprite
  validation, ground validation, встроенный roundtrip генератора, внешний
  `validate_glb_roundtrip.py`, frontend tests
  `buildingModelAssets.test.ts` и `buildingSpriteAssets.test.ts`, `git diff --check`.
  Диапазон треугольников: 4868-11876.
  Ограничений нет.

## Глиняный карьер

Рабочие файлы:

- Spec: `docs/assets/specs/industry/clay_quarry.yaml`.
- Blender-пайплайн: `tools/assets/blender/generate_clay_quarry_models.py`.
- Runtime-папка:
  `frontend/public/assets/buildings/industry/clay_quarry/`.
- Мастер-сцена:
  `frontend/public/assets/buildings/industry/clay_quarry/clay_quarry_levels.blend`.
- Combined GLB:
  `frontend/public/assets/buildings/industry/clay_quarry/clay_quarry_levels.glb`.
- Manifest:
  `frontend/public/assets/buildings/industry/clay_quarry/manifest.json`.
- Отчет генерации:
  `frontend/public/assets/buildings/industry/clay_quarry/generation-report.json`.
- Визуальный обзор:
  `frontend/public/assets/buildings/industry/clay_quarry/state-review.png`.

Состояние на 2026-10-12:

- Создано 36 GLB и 36 PNG: уровни 1-12, состояния `active`,
  `construction`, `damaged`.
- Визуальная прогрессия: ранний мокрый глиняный котлован с ручными
  инструментами, средние уровни добавляют настилы, блоки, лебедку и
  сушильные/сортировочные узлы, с 7 уровня появляются бензиновый мотор, бочки
  топлива, трубопроводы и скребковая техника.
- Проверки прошли: Blender MCP `get_addon_status`/`get_scene_info`, full
  Blender generation, визуальный review `state-review.png`, manifest
  validation, PNG sprite validation, asset spec validation, ground validation и
  внешний `validate_glb_roundtrip.py`. Диапазон треугольников: 4156-16940.
- Ограничения: `tools/assets/validate_building_lods.py` не проходит, потому что
  текущий legacy-пайплайн экспортирует один GLB на уровень/состояние без
  LOD0/LOD1/LOD2 записей. `get_viewport_screenshot`/`look` в Blender MCP не
  создал файл в `/tmp`; визуальная проверка выполнена по runtime contact sheet.
- Runtime-интеграция: `clay_quarry` добавлен в
  `frontend/src/game/renderers/buildingAssetManifests.ts`, а 12 уровней
  синхронизированы в `shared/catalog/buildings.ts`.

## Нефтяная скважина / Нефтяной тайл

Рабочие файлы:

- Blender-пайплайн: `tools/assets/blender/generate_terrain_tile_models.py`.
- Legacy PNG fallback: `tools/assets/generate_terrain_tile_pngs.py`.
- Runtime-папка: `frontend/public/assets/terrain/tiles/`.
- Мастер-сцена: `frontend/public/assets/terrain/tiles/terrain_tiles.blend`.
- Manifest: `frontend/public/assets/terrain/tiles/manifest.json`.
- Визуальный обзор:
  `frontend/public/assets/terrain/tiles/terrain_tiles_contact_sheet.png`.
- MCP QA render: `/tmp/oil_well_mcp_review.png`.

Состояние на 2026-10-10:

- Пересобран terrain `oil_well` как нейтральная нефтяная точка до постройки
  вышки: ровная травяная клетка, неровная черная нефтяная яма, глиняный край,
  камни, пузыри/блики нефти, маленькие survey-колышки и трава; насос-качалка и
  бетонная плита убраны.
- Полный terrain-набор пересобран: 9 PNG и 9 GLB, включая плотности леса.
  `oil_well`: 33 объекта, 2444 треугольника.
- Worldgen переведен на фиксированные нефтяные координаты в текущей
  тестовой карте.

  160x160 wrap-карте: `(24,18)`, `(91,73)`, `(126,35)`, `(38,124)`,
  `(142,116)`, `(76,139)`. Memory resource nodes `node_oil_1-node_oil_6`
  стоят на тех же координатах.
- Проверки прошли: Blender MCP `get_addon_status`/`get_scene_info`,
  full Blender generation, встроенный GLB roundtrip генератора, MCP import/render
  QA-сцена, visual review PNG и contact sheet, terrain manifest/PNG/GLB
  validation без before-tar сравнения, Go tests `worldgen`, `service`,
  `memory`, frontend tests `terrainTextures`, `resources`, `MapWidget`,
  `placement`.
- Ограничение: штатный `tools/assets/validate_terrain_models.py` требует
  отсутствующий временный `/tmp/real-city-terrain-before.tar`; проверка
  выполнена тем же набором assert без сравнения с before-tar.

Состояние на 2026-10-13:

- По пользовательскому уточнению `oil_well` снова трактуется как terrain-клетка
  нефтяной скважины, а не постройка: ассет сохранен только в
  `frontend/public/assets/terrain/tiles/`.
- Визуальная модель усилена компактной металлической качалкой, устьем,
  трубами, моторным блоком, двумя бочками, темным нефтяным пятном, камнями,
  травой и survey-метками. Клетка остается 1x1 terrain tile без
  building-состояний.
- Полный terrain-набор пересобран через Windows Blender CLI:
  `terrain_tiles.blend`, 9 GLB и 9 PNG. `oil_well`: 53 объекта,
  3388 треугольников.
- Проверки прошли: Blender generation, встроенный GLB roundtrip генератора,
  MCP `get_addon_status`/`get_scene_info`, live MCP import `oil_well.glb`,
  topology scene-info, Blender render review `/tmp/oil_well_mcp_review.png`,
  manifest/PNG/GLB validation без before-tar сравнения.
- Ограничение: MCP `look` не смог записать `/tmp/blender_look_*.png`, поэтому
  screenshot-review выполнен через явный Blender render в `/tmp`.

## Нефтяная вышка / Runtime-подключение

Рабочие файлы:

- Генератор: `tools/assets/blender/generate_oil_well_models.py`.
- Runtime-папка: `frontend/public/assets/buildings/industry/oil_well/`.
- Мастер-сцена: `frontend/public/assets/buildings/industry/oil_well/oil_well_levels.blend`.
- Manifest: `frontend/public/assets/buildings/industry/oil_well/manifest.json`.
- Отчет генерации:
  `frontend/public/assets/buildings/industry/oil_well/generation-report.json`.
- Roundtrip report:
  `frontend/public/assets/buildings/industry/oil_well/roundtrip-validation.json`.
- Визуальный обзор:
  `frontend/public/assets/buildings/industry/oil_well/state-review.png`.
- MCP QA render: `/tmp/oil_well_mcp_review.png`.

Состояние на 2026-10-13:

- Перегенерировано 12 PNG и 12 GLB: уровни 1-3, состояния `active`,
  `construction`, `damaged`, `ruined`.
- Уровень 1 собран как ранняя деревянная вышка с настилом, веревками,
  простым насосом и бочками. Уровень 2 переходит в серую металлическую ферму
  с бетонными опорами, трубами, механикой и резервуаром. Уровень 3 использует
  темный усиленный металл, защищенные резервуары, янтарные предупреждающие
  акценты и голубую эоловую линию.
- `construction` оставляет верхнюю часть недостроенной и добавляет свободные
  балки/материалы; `damaged` наклоняет ферму, ломает трубы и добавляет свежие
  протечки; `ruined` схлопывает вышку в обломки над нефтяной точкой.
- Frontend registry обновлен: `oil_well` добавлен в
  `frontend/src/game/renderers/buildingAssetManifests.ts`, превью добавлено в
  build menu, каталог переименован в `Нефтяная вышка`.
- Placement-логика обновлена: обычные здания по-прежнему запрещены на
  `oil_well` и `ruins`, но постройка `oil_well` разрешена только на terrain
  `oil_well`.
- Terrain `oil_well` и `ruins` уже подключены через
  `frontend/src/game/renderer/terrainTextures.ts` и используют PNG из
  `frontend/public/assets/terrain/tiles/`; GLB terrain-модели лежат рядом как
  мастер/runtime-preview ассеты.
- Проверки прошли: `python3 -m py_compile` генератора, Blender CLI generation,
  manifest validation с triangles/bounds, contact sheet generation, встроенный
  GLB roundtrip по 12 файлам без loose vertices, Blender MCP
  `get_addon_status`/`get_scene_info`, загрузка мастер `.blend` в live Blender,
  explicit MCP render review. Диапазон треугольников: 1382-2346.
- Ограничения: `mcp.look` в этой среде нестабилен для записи в `/tmp`;
  визуальная проверка выполнена через runtime contact sheet и явный Blender
  render в `/tmp`.

Обновление на 2026-10-14:

- Нефтяные вышки L1-L3 во всех состояниях повторно перегенерированы и
  подключены в runtime, чтобы соответствовать общему стилю построек Real City.
- Предыдущий runtime-набор сохранен как backup:
  `frontend/public/assets/buildings/industry/oil_well/backup_2026-10-14_pre_style_regen/`.
- Генератор `tools/assets/blender/generate_oil_well_models.py` обновлен:
  задан revision `aeolian-style-runtime-2026-10-14`, увеличен экранный footprint
  модели до уровня остальных построек, расширена рабочая площадка, добавлены
  светлый гравий, более теплые дерево/металл/бетон, цветные панели, крупные
  трубы, резервуары, болтовые пластины и более читаемая качалка.
- Кадр остается стандартным для building layer: PNG `512x384`, anchor
  `[256,292]`; alpha width активных состояний теперь примерно 295-309 px вместо
  мелкого старого диапазона около 165-173 px.
- `OIL_WELL_ASSET_REVISION` обновлен на
  `aeolian-style-runtime-2026-10-14`, runtime `manifest.json` и
  `generation-report.json` синхронизированы.
- Проверки прошли: Blender MCP generation через UNC-путь, `get_addon_status` и
  `get_scene_info`, GLB roundtrip по 12 файлам без loose vertices, runtime
  manifest/file/PNG validation, визуальный review экспортированных PNG и
  `state-review.png`, targeted frontend tests `buildingSpriteAssets.test.ts`,
  `buildingModelAssets.test.ts`, `buildingRegistry.test.ts`. Ограничение:
  `mcp.look` по-прежнему не смог записать `/tmp/blender_look_7644.png`, поэтому
  screenshot-review выполнен по экспортированным render PNG из того же
  изометрического пайплайна.

## Грядки ветролиста

Рабочие файлы:

- Blender-пайплайн: `tools/assets/blender/regenerate_windleaf_beds_blender.py`.
- Старый fallback-генератор: `tools/assets/blender/regenerate_windleaf_beds.py`.
- Runtime-папка:
  `frontend/public/assets/buildings/fields/windleaf_bed/`.
- Мастер-сцена:
  `frontend/public/assets/buildings/fields/windleaf_bed/windleaf_bed_l01_l03.blend`.
- Отчет генерации:
  `frontend/public/assets/buildings/fields/windleaf_bed/generation-report.json`.
- Визуальный обзор:
  `frontend/public/assets/buildings/fields/windleaf_bed/windleaf_bed_l01_l03_review.png`.
- Лог последнего запуска: `/tmp/real-city-windleaf-bed-generation.log`.

Состояние на 2026-09-17:

- Создано 39 GLB и 39 PNG:
  - `windleaf_bed_l01-l03_stage01-stage04`;
  - `windleaf_bed_l01-l03_active`;
  - `windleaf_bed_l01-l03_construction`;
  - `windleaf_bed_l01-l03_damaged`;
  - `windleaf_bed_l01-l03_super_stage01-super_stage06`.
- PNG имеют размер 512x384 и общий anchor `[256, 292]`.
- `field_bed` подключен к map sprite/model asset lookup для уровней 1-3.
- Набор пересобран через Blender MCP как fantasy/mid-poly модельный набор:
  добавлены объемные стойки, строительный земляной тайл в масштабе ранних
  построек, камни, доски, льняные
  подвязки, таблички, подпорки для 3 уровня, более крупные листья с жилками,
  читаемые строительные материалы и поврежденные детали.
- Светло-зеленая подложка убрана: все обычные и супер-стадии стоят только на
  общем тайле земли, совпадающем по размеру с тайлами ратуши, деревянного дома
  и других ранее созданных построек.
- Размер самой грядки увеличен внутри стандартного тайла коэффициентом `1.28`,
  чтобы по footprint она читалась как полноценная постройка рядом с домами и
  ратушей.
- Уровни читаются как апгрейды: 1 уровень - грубые деревянные колышки и
  простая грядка; 2 уровень - аккуратнее рамка, лен и табличка; 3 уровень -
  дощатая рамка, подпорки, веревка и ветровая лента.
- Проверки последней пересборки:
  Blender MCP `get_addon_status`/`get_scene_info`,
  локальная проверка 39 GLB/PNG/`.blend`,
  визуальный обзор `windleaf_bed_l01_l03_review.png` и
  `npm test -- buildingModelAssets.test.ts buildingSpriteAssets.test.ts`.
- Важное исправление: при запуске из Windows Blender все export/render/save
  пути должны идти через UNC `\\wsl.localhost\Debian\home\...`; иначе Blender
  пишет в Windows-путь вида `D:\home\...`, а PNG/GLB в WSL-репозитории остаются
  прежними.
- Замечание: `get_viewport_screenshot` в Blender MCP не создал файл, поэтому
  визуальная проверка выполнена по runtime-рендерам PNG в contact sheet.

## Семенной огород

Рабочие файлы:

- Blender/MCP-генератор:
  `tools/assets/blender/regenerate_seed_garden_blender.py`.
- Старый fallback-генератор:
  `tools/assets/blender/regenerate_seed_garden.py` не используется для
  production-пересборки.
- Runtime-папка:
  `frontend/public/assets/buildings/fields/seed_garden/`.
- Мастер-сцена:
  `frontend/public/assets/buildings/fields/seed_garden/seed_garden_l01_l03.blend`.
- Manifest:
  `frontend/public/assets/buildings/fields/seed_garden/manifest.json`.
- Визуальный обзор:
  `frontend/public/assets/buildings/fields/seed_garden/seed_garden_l01_l03_review.png`.
- Лог последнего запуска: `/tmp/real-city-seed-garden-generation.log`.

Состояние на 2026-10-08:

- Перегенерировано через Blender MCP: 39 GLB и 39 PNG:
  - `seed_garden_l01-l03_stage01-stage03`;
  - `seed_garden_l01-l03_active`;
  - `seed_garden_l01-l03_construction`;
  - `seed_garden_l01-l03_damaged`;
  - `seed_garden_l01-l03_ruined`;
  - `seed_garden_l01-l03_super_stage01-super_stage06`.
- PNG имеют размер 512x384 и anchor `[256, 292]`.
- `seed_garden` подключен к frontend asset lookup для уровней 1-3 через
  `frontend/src/game/renderers/seedGarden.ts`,
  `buildingAssetManifests.ts` и `buildingRegistry.ts`.
- Визуальная логика: низкая 1x1 семенная делянка с параллельными рядами,
  деревянным/дощатым бортиком, мешками семян, лотками, бирками сортов,
  веревочной разметкой и редкими зеленовато-золотыми super-стадиями.
- Уровни читаются как апгрейды: 1 уровень - простая деревянная рамка и
  сортовые метки; 2 уровень - больше мешков, лоток сушки и веревочная
  разметка; 3 уровень - редкий ряд, веревочные стойки, флажок и защищенный
  контейнер супер-семян.
- Проверки прошли: Blender MCP `get_addon_status`/`get_scene_info`,
  генерация GLB/PNG/`.blend` через `execute_blender_code`, manifest validation
  с `--require-triangles` и `--require-bounds-metadata`, PNG sprite validation,
  GLB roundtrip validation (`roundtrip-validation.json`), frontend tests
  `buildingModelAssets.test.ts` и `buildingSpriteAssets.test.ts`, визуальный
  review по Blender runtime contact sheet.
- Ограничение: MCP `look`/viewport screenshot снова не смог записать файл в
  `/tmp/blender_look_*.png`, поэтому screenshot-review выполнен по runtime PNG,
  сгенерированным Blender, а не по fallback-рендерам.

Состояние на 2026-10-09:

- Перегенерировано через Blender MCP: 130 GLB и 130 PNG:
  - `seed_garden_l01-l10_stage01-stage03`;
  - `seed_garden_l01-l10_active`;
  - `seed_garden_l01-l10_construction`;
  - `seed_garden_l01-l10_damaged`;
  - `seed_garden_l01-l10_ruined`;
  - `seed_garden_l01-l10_super_stage01-super_stage06`.
- Runtime-файлы:
  `frontend/public/assets/buildings/fields/seed_garden/`.
- Мастер-сцена:
  `frontend/public/assets/buildings/fields/seed_garden/seed_garden_l01_l10.blend`.
- Manifest/report:
  `frontend/public/assets/buildings/fields/seed_garden/manifest.json`,
  `frontend/public/assets/buildings/fields/seed_garden/generation-report.json`.
- Визуальный обзор:
  `frontend/public/assets/buildings/fields/seed_garden/seed_garden_l01_l10_review.png`.
- Генератор расширен под уровни 1-10: постепенно выше бортики, больше
  резных/цветных узоров, каменные углы, двойные рейки, металлические стяжки,
  сортировочные банки, тканевые панели, ledger-доска, латунный сундук и
  праздничные seed-маркеры.
- Frontend lookup обновлен под 10 уровней:
  `frontend/src/game/renderers/seedGarden.ts` и
  `frontend/src/game/renderers/buildingAssetManifests.ts`.
- Проверки прошли: Blender MCP `get_addon_status`/`get_scene_info`, генерация
  GLB/PNG/`.blend` через `execute_blender_code`, manifest validation с
  `--require-triangles` и `--require-bounds-metadata`, PNG sprite validation,
  frontend tests `buildingModelAssets.test.ts` и `buildingSpriteAssets.test.ts`,
  визуальный review по runtime contact sheet.
- Ограничение: полный GLB roundtrip 130 файлов через текущую MCP-сессию ушел в
  timeout и не обновил `roundtrip-validation.json`; manifest GLB-header проверка
  прошла, но roundtrip нужно повторить отдельной короткой Blender-сессией или
  батчами.

## Льняное поле

Рабочие файлы:

- Blender/MCP-генератор:
  `tools/assets/blender/regenerate_flax_field_blender.py`.
- Старый fallback-генератор:
  `tools/assets/blender/regenerate_flax_field.py` не используется для
  production-пересборки.
- Runtime-папка:
  `frontend/public/assets/buildings/fields/flax_field/`.
- Мастер-сцена:
  `frontend/public/assets/buildings/fields/flax_field/flax_field_l01_l10.blend`.
- Manifest:
  `frontend/public/assets/buildings/fields/flax_field/manifest.json`.
- Визуальный обзор:
  `frontend/public/assets/buildings/fields/flax_field/flax_field_l01_l10_review.png`.
- Лог последнего запуска: `/tmp/real-city-flax-field-generation.log`.

Состояние на 2026-10-08:

- Перегенерировано через Blender MCP: 130 GLB и 130 PNG:
  - `flax_field_l01-l10_stage01-stage03`;
  - `flax_field_l01-l10_active`;
  - `flax_field_l01-l10_construction`;
  - `flax_field_l01-l10_damaged`;
  - `flax_field_l01-l10_ruined`;
  - `flax_field_l01-l10_super_stage01-super_stage06`.
- PNG имеют размер 512x384 и anchor `[256, 292]`.
- `flax_field` подключен к frontend asset lookup для уровней 1-10 через
  `frontend/src/game/renderers/flaxField.ts`,
  `buildingAssetManifests.ts` и `buildingRegistry.ts`.
- Визуальная логика: компактная 1x1 льняная делянка с тонкими холодными
  сине-зелеными стеблями, голубыми цветками, светлой льняной рамой,
  продольными рейками, синими волоконными вставками, угловыми бобинами,
  веревочной разметкой, резными панелями, диагональными волоконными стежками,
  соломенными пучками, сушильными стойками и редкими голубовато-светлыми
  super-стадиями. Рамы специально отличаются от семенного огорода: это не
  сортировочные секции, а вытянутая ремесленная грядка для волокна.
- Уровни читаются как апгрейды и постепенно растут по высоте стенок: 1 уровень
  - низкая светлая рама с пазами; 2 уровень - более высокий дощатый бортик с
  голубыми вставками и tie-blocks; 3 уровень - резные панели, диагональные
  стежки и двойные верхние рейки; 4 уровень - дополнительные перекрестные
  льняные направляющие; 5 уровень - каменные угловые подпятники и грузики;
  6 уровень - кирпичные вставки и тканевые детали; 7 уровень - тканевые опоры
  и вторичная сушильная стойка; 8 уровень - премиальное темное дерево и
  металлические бандажи; 9 уровень - золотые метки качества; 10 уровень -
  super-seed case, золотая защелка, светящийся seed-акцент и самый богатый
  elite-frame декор.
- Последняя итерация: расширена production-генерация до уровней 1-10 и
  усилена прогрессия уровней в стенках/бортиках грядок в
  `tools/assets/blender/regenerate_flax_field_blender.py`.
- Проверки прошли: Blender MCP `get_addon_status`/`get_scene_info`, генерация
  130 GLB/PNG/`.blend` через Blender production script без fallback,
  инспекция `flax_field_l01_l10.blend` через MCP
  `execute_blender_code`, manifest validation с `--require-triangles`, PNG
  sprite validation, `py_compile`, JSON validation,
  `npm test -- buildingModelAssets.test.ts buildingSpriteAssets.test.ts`,
  обновление `flax_field_l01_l10_review.png`, визуальный review по runtime PNG
  `flax_field_l01_active.png`, `flax_field_l04_active.png`,
  `flax_field_l07_active.png`, `flax_field_l10_active.png` и
  `flax_field_l10_damaged.png`.
- Ограничение: MCP `look`/viewport screenshot снова не смог записать файл в
  `/tmp/blender_look_*.png`, поэтому screenshot-review выполнен по runtime PNG,
  сгенерированным Blender, а не по fallback-рендерам.

## Масличное поле

Рабочие файлы:

- Blender/MCP-генератор:
  `tools/assets/blender/regenerate_oilseed_field_blender.py`.
- Asset spec:
  `docs/assets/specs/fields/oilseed_field.yaml`.
- Runtime-папка:
  `frontend/public/assets/buildings/fields/oilseed_field/`.
- Мастер-файл:
  `frontend/public/assets/buildings/fields/oilseed_field/oilseed_field_l01_l07.blend`.
- Generation report:
  `frontend/public/assets/buildings/fields/oilseed_field/generation-report.json`.
- Manifest:
  `frontend/public/assets/buildings/fields/oilseed_field/manifest.json`.
- Визуальный обзор:
  `frontend/public/assets/buildings/fields/oilseed_field/oilseed_field_l01_l07_review.png`;
  ключевые состояния:
  `frontend/public/assets/buildings/fields/oilseed_field/oilseed_field_key_states_review.png`.
- Лог планового запуска:
  `/tmp/real-city-oilseed-field-generation.log`.

Состояние на 2026-10-09:

- Полный production-прогон выполнен через Windows Blender CLI под 7 уровней и
  13 runtime-состояний:
  `stage01-stage03`, `active`, `construction`, `damaged`, `ruined`,
  `super_stage01-super_stage06`.
- Сгенерировано 91 GLB и 91 runtime PNG, плюс `manifest.json`,
  `generation-report.json`, мастер-файл `oilseed_field_l01_l07.blend` и оба
  review contact sheets.
- Визуальная логика генератора: сухая теплая восьмиугольная грядка для
  масличных культур с желтыми семенными головками, толстыми press-style
  стойками, резными seed-дисками на стенках, корзинами семян, сушильными
  рейками, тканевыми стяжками, железными кольцами, мини-прессом поздних
  уровней и небольшими масляными желобами.
- Уровни отличаются конструктивно: борта постепенно становятся выше, появляются
  верхние восьмиугольные рейки, каменные подпятники, железные бандажи, больше
  подвешенных seed-дисков, сушильные рейки, прессовый декор, золотые метки и
  `super-seed` sample tray на поздних super-состояниях.
- Blender MCP live gate прошел для `get_addon_status` и `get_scene_info`
  против Windows host `172.28.192.1:9877`; production-экспорт выполнен
  отдельным background-запуском Blender CLI.
- Проверки прошли: `python3 -m py_compile
  tools/assets/blender/regenerate_oilseed_field_blender.py`,
  `validate_building_manifests.py`, `validate_building_sprites.py`,
  `validate_glb_roundtrip.py` по 48 GLB без ошибок, генерация full/key-state
  contact sheets, ручной визуальный просмотр contact sheets,
  `npm --prefix frontend test -- buildingModelAssets.test.ts
  buildingSpriteAssets.test.ts`.
- `validate_asset_specs.py docs/assets/specs/fields/oilseed_field.yaml`
  проверяет ресурсные id; единственная ожидаемая ошибка сейчас связана не с
  ассетами, а с каталогом: `levels mismatch`.
- Дополнительный sync-долг: `docs/assets/specs/fields/oilseed_field.yaml` уже
  описывает 7 уровней, а `shared/catalog/buildings.ts` пока содержит только
  1 уровень `oilseed_field`, поэтому `validate_asset_specs.py` сейчас ожидаемо
  сообщает `levels mismatch`.

## Грибница

Рабочие файлы:

- Blender/MCP-генератор:
  `tools/assets/blender/regenerate_mushroom_grove_blender.py`.
- Asset spec:
  `docs/assets/specs/fields/mushroom_grove.yaml`.
- Runtime-папка:
  `frontend/public/assets/buildings/fields/mushroom_grove/`.
- Плановый мастер-файл:
  `frontend/public/assets/buildings/fields/mushroom_grove/mushroom_grove_l01_l10.blend`.
- Лог планового запуска:
  `/tmp/real-city-mushroom-grove-generation.log`.

Состояние на 2026-10-10:

- Production-набор перегенерирован для 10 уровней и 13 runtime-состояний:
  `stage01-stage03`, `active`, `construction`, `damaged`, `ruined`,
  `super_stage01-super_stage06`.
- В runtime-папке созданы `130` GLB, `130` runtime PNG, `manifest.json`,
  `generation-report.json`, мастер-файл `mushroom_grove_l01_l10.blend` и
  review-листы `mushroom_grove_l01_l10_review.png`,
  `mushroom_grove_key_states_review.png`.
- Уровни 5-10 дополнительно переработаны под читаемость грибов сверху:
  грядки стали больше по площади, грибные группы разнесены шире, навесы теперь
  покрывают всю грядку, подняты выше грибов и используют полупрозрачный
  материал, чтобы шляпки оставались видны в изометрическом ракурсе.
- Поздняя прогрессия сохранена, но адаптирована под игровую камеру: на 5
  уровне появляется высокий тонкий тканевый навес над расширенной грядкой; с 6
  уровня добавляются калитки под цвет стен; на 7-10 уровнях стены сделаны ниже
  и плотнее покрыты декором, чтобы не закрывать внутренние грибы; на 9-10
  уровнях калитки заменены металлическими дверями с накладками, боссами и
  декоративными вставками.
- Конструкция стен и декора поздних уровней различается по материалам:
  камень, кирпич, каменные блоки, полированные премиум-доски, металлические
  стойки, металлические декоративные ремни, элементы из шляпок супер-грибов и
  отделка фундамента изумрудной пылью. Уровни 7-10 получили дополнительные
  настенные точки, смоляные потеки, металлические ремни и полочные грибные
  элементы.
- Проверки прошли: `py_compile`, `validate_building_manifests.py`,
  `validate_building_sprites.py`, `validate_glb_roundtrip.py` (`48` GLB,
  ошибок `0`), генерация обоих contact sheets, визуальный review по ним и
  frontend-тесты `buildingModelAssets.test.ts`, `buildingSpriteAssets.test.ts`
  (`12` тестов).
- Blender MCP live gate прошел через Windows host `172.28.192.1`:
  `get_addon_status` вернул Blender `5.2.1 LTS`, protocol `13`, addon
  `[1, 8]`, telemetry disabled; `get_scene_info` доступен.
- MCP screenshot-review свежего мастер-файла не выполнялся: auto-review
  отклонил открытие `mushroom_grove_l01_l10.blend` в живой Blender-сцене как
  потенциально рискованное для текущей несохраненной сцены. Безопасная
  визуальная проверка выполнена по двум contact sheets.
- `validate_asset_specs.py docs/assets/specs/fields/mushroom_grove.yaml`
  теперь падает только на ожидаемом `levels mismatch`, потому что spec уже
  описывает 10 уровней, а игровой каталог пока содержит 1 уровень.
- Техническая заметка: самые детальные GLB поздних super-состояний 10 уровня
  доходят примерно до `25.8k` треугольников; runtime-рендер использует PNG,
  поэтому это не влияет на текущую 2D-карту, но отдельный optimization pass
  может снизить вес GLB.
- Дополнительный sync-долг: `docs/assets/specs/fields/mushroom_grove.yaml`
  уже описывает 10 уровней, а `shared/catalog/buildings.ts` пока содержит
  только 1 уровень `mushroom_grove`, поэтому `validate_asset_specs.py` сейчас
  ожидаемо сообщает `levels mismatch`.

## Травяная грядка

Рабочие файлы:

- Blender/MCP-генератор:
  `tools/assets/blender/regenerate_herb_bed_blender.py`.
- Asset spec:
  `docs/assets/specs/fields/herb_bed.yaml`.
- Runtime-папка:
  `frontend/public/assets/buildings/fields/herb_bed/`.
- Плановый мастер-файл:
  `frontend/public/assets/buildings/fields/herb_bed/herb_bed_l01_l09.blend`.
- Лог планового запуска:
  `/tmp/real-city-herb-bed-generation.log`.

Состояние на 2026-10-09:

- Полный production-прогон выполнен через Windows Blender CLI под 9 уровней и
  13 runtime-состояний:
  `stage01-stage03`, `active`, `construction`, `damaged`, `ruined`,
  `super_stage01-super_stage06`.
- Сгенерировано 117 GLB и 117 runtime PNG, плюс `manifest.json`,
  `generation-report.json`, мастер-файл `herb_bed_l01_l09.blend` и review
  contact sheets `herb_bed_l01_l09_review.png` /
  `herb_bed_key_states_review.png`.
- Визуальная логика генератора: скругленная аптекарская грядка с плетеными
  лозовыми стенками, раздвоенными `Y`-стойками, веревочными узлами, мягкими
  рядами трав, бирками, сушильными пучками, тканевыми полосами, каменным
  цоколем поздних уровней, мини-лейкой, стеклянными колпаками редких цветков и
  изумрудными super-акцентами.
- Уровни отличаются конструктивно: борт постепенно выше, появляются вторые
  плетеные ряды, сушильная рама, верхние резные планки, каменные подпятники,
  железные детали, полка для бирок, стеклянные колпаки и защищенный
  super-seed/sample декор.
- Blender MCP live gate прошел для `get_addon_status` и `get_scene_info`
  против `172.28.192.1:9877`; сам production-экспорт выполнен отдельным
  background-запуском Blender CLI.
- Проверки прошли: `python3 -m py_compile
  tools/assets/blender/regenerate_herb_bed_blender.py`,
  `validate_building_manifests.py`, `validate_building_sprites.py`,
  `validate_glb_roundtrip.py` по 48 GLB без ошибок, генерация full/key-state
  contact sheets и ручной визуальный просмотр contact sheets.
- `validate_asset_specs.py` проверяет ресурсные id после уточнения
  `generation_report.notes`; единственная ожидаемая ошибка сейчас связана не с
  ассетами, а с каталогом: `levels mismatch`.
- Дополнительный sync-долг: `docs/assets/specs/fields/herb_bed.yaml` уже
  описывает 9 уровней, а `shared/catalog/buildings.ts` пока содержит только
  1 уровень `herb_bed`, поэтому `validate_asset_specs.py` сейчас ожидаемо
  сообщает `levels mismatch`.

## Тростниковая грядка

Рабочие файлы:

- Blender/MCP-генератор:
  `tools/assets/blender/regenerate_reed_bed_blender.py`.
- Asset spec:
  `docs/assets/specs/fields/reed_bed.yaml`.
- Runtime-папка:
  `frontend/public/assets/buildings/fields/reed_bed/`.
- Мастер-файл:
  `frontend/public/assets/buildings/fields/reed_bed/reed_bed_l01_l10.blend`.
- Generation report:
  `frontend/public/assets/buildings/fields/reed_bed/generation-report.json`.
- Manifest:
  `frontend/public/assets/buildings/fields/reed_bed/manifest.json`.
- Визуальный обзор:
  `frontend/public/assets/buildings/fields/reed_bed/reed_bed_l01_l10_review.png`;
  ключевые состояния:
  `frontend/public/assets/buildings/fields/reed_bed/reed_bed_key_states_review.png`.
- Лог запуска:
  `/tmp/real-city-reed-bed-generation.log`.

Состояние на 2026-10-09:

- Сгенерировано 130 GLB и 130 runtime PNG: 10 уровней x 13 состояний:
  `stage01-stage03`, `active`, `construction`, `damaged`, `ruined`,
  `super_stage01-super_stage06`.
- Создан мастер `.blend` `reed_bed_l01_l10.blend`, `manifest.json`,
  `generation-report.json`, полный contact sheet и review-лист ключевых
  состояний.
- Визуальная логика генератора: холодная влажная лодкообразная ванна с
  узкими глиняными стенками, тонкими ребристыми кольями, вертикальными
  пучками тростника, водными канавками, мерными планками, мокрыми
  веревочными стяжками, мостиком-доской, угловым сливом, каменными
  подпятниками, железными лентами и поздними синими/светокристальными
  водными маркерами.
- Уровни отличаются конструктивно: борт постепенно выше, появляются
  кирпичные вставки, тканевые метки уровня воды, вторичные желобки, каменная
  кромка, железные скобы, редкие светокристальные маркеры и защищенный
  sample/super декор. Силуэт специально тонкий и вертикальный, чтобы не
  совпадать с сахарной, травяной, семенной или льняной грядкой.
- Генерация: MCP live gate и preview прошли через `get_addon_status`,
  `get_scene_info` и `execute_blender_code`; full MCP-прогон уперся в
  180-секундный socket timeout, поэтому тот же production-генератор был
  завершен через Windows Blender CLI в background-режиме.
- Проверки прошли: `python3 -m py_compile
  tools/assets/blender/regenerate_reed_bed_blender.py`,
  `validate_building_manifests.py --require-triangles
  --require-bounds-metadata`, `validate_building_sprites.py`,
  `make_asset_contact_sheet.py`, визуальный review PNG/contact sheet,
  `validate_glb_roundtrip.py` на 48 GLB (`failures: 0`).
- Asset spec проверен через `tools/assets/validate_asset_specs.py`; единственное
  оставшееся сообщение - ожидаемый `levels mismatch`, потому что spec уже
  описывает 10 уровней, а `shared/catalog/buildings.ts` пока содержит только
  1 уровень `reed_bed`. Legacy-ресурс `wood` из текущего каталога добавлен в
  `material_map` как временная совместимость.
- Ограничения: MCP `look`/screenshot снова не смог записать файл в WSL `/tmp`,
  поэтому screenshot-review выполнен по runtime PNG/contact sheets. Каталог
  `shared/catalog/buildings.ts` еще не синхронизирован с 10 уровнями
  `reed_bed`.

## Канатный двор

Рабочие файлы:

- Генератор: `tools/assets/blender/regenerate_rope_yard.py`.
- Runtime-папка:
  `frontend/public/assets/buildings/industry/rope_yard/`.
- Manifest:
  `frontend/public/assets/buildings/industry/rope_yard/manifest.json`.
- Визуальный обзор:
  `frontend/public/assets/buildings/industry/rope_yard/rope_yard_l01_l08_review.png`.
- Лог последнего запуска: `/tmp/real-city-rope-yard-generation.log`.

Состояние на 2026-10-08:

- Создано 56 GLB и 56 PNG:
  - `rope_yard_l01-l08_active`;
  - `rope_yard_l01-l08_ready`;
  - `rope_yard_l01-l08_idle_no_input`;
  - `rope_yard_l01-l08_idle_no_workers`;
  - `rope_yard_l01-l08_construction`;
  - `rope_yard_l01-l08_damaged`;
  - `rope_yard_l01-l08_ruined`.
- PNG имеют размер 512x384 и anchor `[256, 292]`.
- Source `.blend`: `rope_yard_l01_l08.blend`.
- Пайплайн: `blender_mcp_midpoly`; старый fallback-генератор
  `tools/assets/blender/regenerate_rope_yard.py` больше не является
  production-источником для текущего набора.
- `rope_yard` подключен к frontend asset lookup для уровней 1-8 через
  `frontend/src/game/renderers/ropeYard.ts`,
  `buildingAssetManifests.ts` и `buildingRegistry.ts`.
- Визуальная логика: открытая 1x1 промышленная площадка с длинной линией
  скрутки, стойками с крючьями, натянутыми волокнами, входными стопками льна,
  бухтами готовой веревки, навесом, барабанами и поздними механическими,
  медными и золотистыми калибровочными деталями.
- Проверки прошли: Blender MCP bootstrap (`get_addon_status`,
  `get_scene_info`), generation через live Blender, manifest validation с
  `--require-triangles` и `--require-bounds-metadata`, PNG sprite validation,
  GLB roundtrip validation (`roundtrip-validation.json`), frontend tests
  `buildingModelAssets.test.ts` и `buildingSpriteAssets.test.ts`, визуальный
  review по Blender runtime contact sheet.
- Ограничение: MCP `look`/viewport screenshot снова не смог записать файл в
  `/tmp/blender_look_*.png`, поэтому screenshot-review выполнен по runtime PNG,
  сгенерированным Blender, а не по live viewport capture.

## Хранилище монет

Рабочие файлы:

- Генератор: `tools/assets/blender/generate_coin_storage_models.py`.
- Runtime-папка: `frontend/public/assets/buildings/storage/coin_storage/`.
- Source blend: `frontend/public/assets/buildings/storage/coin_storage/coin_storage_levels.blend`.
- Manifest: `frontend/public/assets/buildings/storage/coin_storage/manifest.json`.
- Визуальный обзор текущего прогона: `/tmp/coin_storage_l04_l12_contact_sheet.png`.

Состояние на 2026-09-29:

- Сгенерирована цепочка `coin_storage` уровней 1-12 для состояний
  `active`, `construction`, `damaged`, `ruined`.
- По текущему запросу пересобраны уровни 4-12 во всех 4 состояниях:
  36 GLB и 36 PNG.
- Дополнительно исправлены ранние уровни 1-3, потому что предыдущий прогон
  оставил часть GLB пустыми после скрытия коллекций между рендерами.
- Всего в runtime-папке сейчас 48 GLB и 48 PNG.
- Manifest собран на 48 записей по фактически экспортированным runtime-файлам.
- Визуальная прогрессия: уровни 4-6 - каменная/кирпичная казна, уровни 7-8 -
  железобетон и сталь, уровни 9-12 - бронеплиты, механический счетчик,
  золотая печать и светокристальный индикатор на поздних уровнях.
- Проверки пройдены:
  `python3 -m py_compile tools/assets/blender/generate_coin_storage_models.py`,
  наличие всех файлов, GLB v2 header/chunk validation для уровней 4-12,
  `git diff --check` для генератора и manifest,
  визуальный review contact sheet уровней 4-12.
- Ограничение: после длинного сохранения Blender MCP перестал отвечать на
  `get_scene_info`, поэтому полноценный Blender roundtrip-import отчет
  `roundtrip-validation.json` для этого набора еще не создан. Runtime GLB не
  пустые и структурно валидны, но re-import через Blender нужно повторить после
  перезапуска MCP.

## Ресурсы

Рабочие файлы:

- Blender-пайплайн: `tools/assets/blender/regenerate_resource_models.py`.
- PNG fallback-пайплайн: `tools/assets/generate_resource_icon_pngs.py`.
- Runtime-папка: `frontend/public/assets/resources/icons/`.
- Основной обзор: `frontend/public/assets/resources/icons/resource_icons_contact_sheet.png`.
- Fallback-обзор: `frontend/public/assets/resources/icons/resource_icons_docs_fallback_review.png`.
- Малые размеры fallback:
  `frontend/public/assets/resources/icons/resource_icons_docs_fallback_small_review.png`.
- Отчет fallback:
  `frontend/public/assets/resources/icons/docs-fallback-validation.json`.
- Лог последнего fallback-запуска:
  `/tmp/real-city-resource-icons-fallback.log`.

Состояние на 2026-09-17:

- В `manifest.json` сейчас 74 PNG-ресурса.
- Существующий Blender-набор сохранил 34 GLB и `resource_icons.blend`.
- Добавлены PNG-only иконки для ресурсов из `docs/game-design/resources-list.md`, которых
  еще нет в игровом каталоге, а также для новых игровых ресурсов без прежних
  иконок: `flax`, `premium_planks`, `rope`, `iron_ingot`, `gold_ingot`,
  `super-windleaf`, `emerald_dust`.
- Обновлена `aeolian-crystal.png`: кристаллы стали детальнее, с более
  стеклянными аметистовыми гранями.
- Проверка `tools/assets/validate_resource_models.py` допускает, что manifest
  является супермножеством игрового каталога; GLB-топология проверяется только
  у ресурсов с `model`.
- Ограничение: Blender MCP на этой итерации снова сбросил соединение
  (`Connection reset by peer`), поэтому новые документированные ресурсы пока
  без `.glb`/`.blend` мастер-геометрии.

## Руины / Terrain-Варианты

Рабочие файлы:

- Генератор:
  `tools/assets/blender/generate_ruins_terrain_models.py`.
- Runtime-папка:
  `frontend/public/assets/terrain/tiles/`.
- Папка семейства:
  `frontend/public/assets/terrain/tiles/ruins_variants/`.
- Мастер-сцена:
  `frontend/public/assets/terrain/tiles/ruins_variants/ruins_variants.blend`.
- Manifest:
  `frontend/public/assets/terrain/tiles/ruins_variants/manifest.json`.
- Root manifest-копия:
  `frontend/public/assets/terrain/tiles/ruins_variants_manifest.json`.
- Contact sheet:
  `frontend/public/assets/terrain/tiles/ruins_variants/ruins_variants_contact_sheet.png`.
- MCP QA render:
  `/tmp/ruins_variants_mcp_review.png`.

Состояние на 2026-10-13:

- Создано 12 подтипов захватываемых руин из дизайн-дока: старая ратушная
  площадь, архив чертежей, монетный двор, складской узел, оранжерея, водяная
  станция, каменный бастион, мастерская механизмов, святилище ветра, залежный
  обелиск, разломная сторожевая и речной маяк.
- У каждого подтипа есть PNG и GLB в `ruins_variants/`, а также root-копия
  `ruins_<type>.png/.glb` прямо в `frontend/public/assets/terrain/tiles/`.
- Все PNG имеют формат 512x512, anchor `[256,320]`, footprint 480 px и ту же
  terrain-камеру, что базовые тайлы.
- Проверки прошли: Blender MCP `get_addon_status`/`get_scene_info`,
  Blender generation, встроенный Blender roundtrip-import, локальный
  `python3 tools/assets/validate_ruins_terrain_variants.py`, contact sheet,
  MCP import всех 12 GLB в live-сцену и explicit render review.
- Диапазон треугольников: 1408-3896 на модель.
- Ограничение: `mcp.look` снова не смог записать файл
  `/tmp/blender_look_7644.png`; визуальная MCP-проверка выполнена явным
  Blender render в UNC-путь `/tmp/ruins_variants_mcp_review.png`.

## Лесопильные дворы

Текущая активная тема: полная пересборка `lumber_yard` 1-13 уровней во всех
состояниях, потому что предыдущие лесопилки выглядели не изометрично и не в
стиле землянок/деревянных домов.

Рабочие файлы:

- Генератор: `tools/assets/blender/regenerate_sawmills.py`.
- Старый entry point направлен в новый пайплайн:
  `tools/assets/blender/generate_lumber_yard_models.py`.
- Художественный brief: `docs/assets/sawmill-housing-style-revision.md`.
- Runtime-папка: `frontend/public/assets/buildings/industry/lumber_yard/`.
- Staging последней полной пересборки: `/tmp/real-city-sawmill-final/`.
- Preview уровней 1, 6, 13: `/tmp/real-city-sawmill-preview/`.

Состояние на 2026-09-16:

- Preview уровней 1, 6, 13 был сгенерирован для active/construction/damaged.
- Полный staging на 39 файлов GLB и 39 PNG был сгенерирован в
  `/tmp/real-city-sawmill-final/`; лог завершился `SAWMILL_COMPLETE 39`.
- Staging нужно дополнительно провалидировать и визуально проверить перед
  продвижением в runtime-папку, если эта работа еще не завершена отдельным
  шагом.

Обязательные проверки перед завершением лесопилок:

- Все 13 уровней и 3 состояния существуют как `.glb` и `.png`.
- PNG: 512x384, одинаковый anchor с домами, читаемый изометрический вид.
- Ground: construction/damaged используют то же основание, что active уровня.
- Topology: нет не-манихолдных разрывов, применены transforms, нормали
  корректны.
- Construction: неготовый объект с частичным настилом, стенами, стропилами,
  недостающей крышей и строительными материалами.
- Damaged: крупно разрушенные крыша/стены/опоры, обломки лежат на земле.
- Нет висящих в воздухе деталей стен, крыши, лесов или обломков.

## Песчаный карьер

Рабочие файлы:

- Генератор: `tools/assets/blender/generate_sand_quarry_models.py`.
- Runtime-папка: `frontend/public/assets/buildings/industry/sand_quarry/`.
- Обзор состояний: `frontend/public/assets/buildings/industry/sand_quarry/state-review.png`.
- Manifest: `frontend/public/assets/buildings/industry/sand_quarry/manifest.json`.
- Отчет: `frontend/public/assets/buildings/industry/sand_quarry/generation-report.json`.

Состояние на 2026-09-24:

- Сгенерирован полный набор `sand_quarry` 1-11 уровней для состояний
  `active`, `construction`, `damaged`: 33 GLB и 33 PNG.
- Runtime-резолверы frontend обновлены на диапазон 1-11 и revision
  `mcp-midpoly-l01-l11-2026-09-24`.
- Проверки прошли: manifest на 11 уровней, PNG 512x384 с ненулевой альфой,
  GLB-заголовки `glTF`, `roundtrip-validation.json` на 33 модели,
  renderer/assets тесты frontend.
- Ограничение: после генерации Blender MCP сбросил соединение
  (`Connection reset by peer`), поэтому live `get_viewport_screenshot()` для
  финального post-review нужно повторить после перезапуска MCP-сервера в
  Blender. Локальный `state-review.png` визуально проверен.

## Детальные Горы И Шахта L1, Staging

Рабочие файлы:

- Генератор:
  `tools/assets/blender/generate_mountain_detail_models.py`.
- Валидатор:
  `tools/assets/validate_mountain_detail_staging.py`.
- Staging-папка:
  `frontend/public/assets/terrain/tiles/mountain_detail_staging/`.
- Мастер-сцена:
  `frontend/public/assets/terrain/tiles/mountain_detail_staging/mountain_detail_staging.blend`.
- Contact sheet:
  `frontend/public/assets/terrain/tiles/mountain_detail_staging/mountain_detail_contact_sheet.png`.
- Manifest:
  `frontend/public/assets/terrain/tiles/mountain_detail_staging/manifest.json`.

Состояние на 2026-10-13:

- Создано 4 отдельных staging-ассета, не подключенных к игре и не заменяющих
  текущие terrain/building модели:
  `mountain_detail_ridge`, `mountain_detail_spire`,
  `mountain_detail_snowcap`, `mine_l01_active_mountain_detail`.
- Горы собраны как фасеточные пиковые меши с одним доминирующим пиком,
  боковыми гребнями, светлыми ребрами, осыпью, мхом/травой и умеренным снегом.
  Это тест нового подхода вместо старого `mountain()` из округлых валунов.
- Шахта L1 active использует тот же каменный kit: компактная скала, один
  наружный деревянный портал, темная глубина штольни, рельсы, вагонетка,
  лампы и осыпь; в runtime `mine_l01_active` не заменялась.
- Диапазон треугольников: 1536-2328 на модель.
- Проверки прошли: Blender MCP `get_addon_status`/`get_scene_info`,
  Blender generation, встроенный Blender roundtrip-import, локальный
  `python3 tools/assets/validate_mountain_detail_staging.py`, contact sheet,
  MCP загрузка `.blend` и explicit render review в
  `/tmp/mountain_detail_mcp_review.png`.
- Ограничение: `mcp.look` снова не смог записать файл
  `/tmp/blender_look_7644.png`; визуальная MCP-проверка выполнена явным
  Blender render в UNC-путь.

Обновление на 2026-10-13:

- Все 4 staging-ассета перегенерированы по правке: горы стали шире по площади
  и выше, основные скальные массы теперь занимают почти всю 1x1 клетку.
- Осыпные камни вокруг гор разложены нерегулярными кластерами вместо ровной
  линии.
- У `mine_l01_active_mountain_detail` удалена отдельная серая каменная
  подстилка; осталась базовая grass-клетка. Скальные щеки и задняя масса
  утолщены, портал встроен в каменную стену через backing/seam/socket-детали.
- Новый диапазон треугольников: 1988-2776 на модель.
- Проверки после правки прошли: Blender generation, встроенный roundtrip,
  `python3 tools/assets/validate_mountain_detail_staging.py`, MCP загрузка
  `.blend`, `get_scene_info` и explicit render review
  `/tmp/mountain_detail_mcp_review_updated.png`.

Обновление 2 на 2026-10-13:

- Версии предыдущих 4 staging-моделей сохранены как backup:
  `frontend/public/assets/terrain/tiles/mountain_detail_staging/backup_2026-10-13_thicker_v1/`.
- Старые файлы `mountain_detail_ridge`, `mountain_detail_spire`,
  `mountain_detail_snowcap` и `mine_l01_active_mountain_detail` не
  перезаписывались. Новая партия сохранена рядом отдельными именами и
  отдельным manifest/report:
  `frontend/public/assets/terrain/tiles/mountain_detail_staging/manifest_massive.json`,
  `generation-report-massive.json`, `roundtrip-validation-massive.json`,
  `validation_massive.json`.
- Новый генератор:
  `tools/assets/blender/generate_mountain_detail_massive_models.py`.
  Новый валидатор:
  `tools/assets/validate_mountain_detail_massive_staging.py`.
- Создано 36 новых staging-ассетов:
  3 массивные горы `*_massive` и шахты уровней 2-12 в состояниях
  `active`, `construction`, `damaged`.
- Горы стали примерно вдвое выше предыдущих staging-версий; основные скальные
  массы используют 90-95% площади клетки, оставляя только узкую видимую кромку
  grass-тайла.
- Шахты L2-L12 сделаны по образцу L1: толстая компактная скала почти на всю
  клетку, один наружный портал, прикрепленный к каменной стене, темная
  глубина штольни, рельсы и рабочие props. Прогрессия уровней добавляет
  каменную/кирпичную крепь, железо, механизмы, взрывчатку, вентиляцию,
  железобетон, супер-механизмы и светокристалл на поздних уровнях.
- Проверки прошли: `python3 -m py_compile` для генератора/валидатора, Blender
  CLI generation, встроенный Blender roundtrip-import, локальный
  `python3 tools/assets/validate_mountain_detail_massive_staging.py`,
  contact sheet `mountain_detail_massive_contact_sheet.png`, MCP загрузка
  `mountain_detail_massive_staging.blend`, `get_scene_info` и explicit MCP
  render review `/tmp/mountain_detail_massive_mcp_review.png`.
  Диапазон треугольников: 2216-4336.
- Ограничение: партия остается staging-набором, не подключенным к игре и не
  заменяющим production terrain/building ассеты.

Обновление 3 на 2026-10-13:

- Предыдущая massive-партия с перекрытым входом сохранена как backup:
  `frontend/public/assets/terrain/tiles/mountain_detail_staging/backup_2026-10-13_massive_blocked_entrance/`.
- Исправлены шахты L2-L12 во всех состояниях: цельный
  `portal_stone_backing`, визуально закрывавший вход, заменен на раздельные
  боковые скальные щеки, верхнюю скальную бровку и утопленный темный
  `cave_far_shadow`. Центральный проем теперь остается открытым как у модели
  L1.
- Наружная арка получила отдельную сменяемую отделку по уровням: дерево/канат
  на ранних уровнях, камень, кирпич с металлом, медно-железные детали,
  бетонно-стальные усиления и late-game усиленная отделка со светокристаллом.
- Перегенерированы `manifest_massive.json`, `generation-report-massive.json`,
  `roundtrip-validation-massive.json`, `validation_massive.json`, контакт-лист,
  PNG/GLB и `mountain_detail_massive_staging.blend`.
- Проверки прошли: `python3 -m py_compile`, Blender CLI generation, встроенный
  Blender roundtrip-import, `python3
  tools/assets/validate_mountain_detail_massive_staging.py`, `git diff
  --check`, визуальный contact sheet и explicit MCP render review
  `/tmp/mountain_detail_massive_open_entrance_mcp_review.png`.
  Итог: 36 assets, 33 шахты, loose vertices 0, диапазон треугольников
  2216-4952.

Обновление 4 на 2026-10-14:

- Предыдущая massive-партия с открытым входом сохранена как backup:
  `frontend/public/assets/terrain/tiles/mountain_detail_staging/backup_2026-10-13_massive_open_entrance_v1/`.
- Шахты L2-L12 во всех состояниях перегенерированы еще раз: основные
  скальные массы сделаны толще и шире, а `peak_mesh` получил параметры
  `pointiness` и `crag` для более естественных острых пиков и выраженных
  вертикальных граней.
- У входа убран нижний загромождающий серый камень: единый широкий
  `mine_front_lip` заменен на два боковых уступа
  `mine_front_lip_left/right`, уменьшены нижний `cave_floor_depth` и
  каменные `post_socket`, чтобы центральный низ штольни оставался свободным.
- Перегенерированы `manifest_massive.json`, `generation-report-massive.json`,
  `roundtrip-validation-massive.json`, `validation_massive.json`, контакт-лист,
  PNG/GLB и `mountain_detail_massive_staging.blend`.
- Проверки прошли: `python3 -m py_compile`, Blender CLI generation, встроенный
  Blender roundtrip-import, `python3
  tools/assets/validate_mountain_detail_massive_staging.py`, `git diff
  --check`, визуальный contact sheet и explicit MCP render review
  `/tmp/mountain_detail_massive_sharper_entrance_mcp_review.png`.
  Итог: 36 assets, 33 шахты, loose vertices 0, диапазон треугольников
  2216-5344.

Обновление 5 на 2026-10-14:

- Предыдущая massive-партия с более острыми и толстыми горами сохранена как
  backup:
  `frontend/public/assets/terrain/tiles/mountain_detail_staging/backup_2026-10-14_massive_sharper_v1/`.
- Шахты L2-L12 во всех состояниях перегенерированы так, чтобы скальная часть
  совпадала с горой шахты L1: добавлен отдельный `mine_l01_peak_mesh` и общий
  `add_l01_mine_rock_shell`, повторяющий четыре L1-компонента
  `mine_back_mountain`, `mine_left_cheek`, `mine_right_cheek`,
  `mine_front_lip` с теми же размерами, twist и lean.
- Уровневые отличия L2-L12 сохранены только в портале, отделке арки,
  рельсах, лампах, механизмах, ящиках, вентиляции и поздних decorative props;
  базовый горный силуэт теперь не меняется от уровня к уровню.
- Перегенерированы `manifest_massive.json`, `generation-report-massive.json`,
  `roundtrip-validation-massive.json`, `validation_massive.json`, контакт-лист,
  PNG/GLB и `mountain_detail_massive_staging.blend`.
- Проверки прошли: `python3 -m py_compile`, Blender CLI generation, встроенный
  Blender roundtrip-import, `python3
  tools/assets/validate_mountain_detail_massive_staging.py`, `git diff
  --check`, визуальный contact sheet. Blender MCP подключение проверено; MCP
  render review был остановлен соединением после повторной загрузки сцены, но
  файлы уже прошли roundtrip-валидацию и локальный валидатор.
  Итог: 36 assets, 33 шахты, loose vertices 0, диапазон треугольников
  2036-4060.

Обновление 6 на 2026-10-14:

- Новые модели шахт подключены в runtime вместо старого набора:
  `mine_l01_active` взят из `mountain_detail_staging`, а
  `mine_l02`-`mine_l12` во всех состояниях взяты из
  `mountain_detail_massive_staging` и скопированы в
  `frontend/public/assets/buildings/industry/mine/` под стандартными именами
  `mine_lXX_<state>.png/.glb`.
- Старый runtime-набор не удален и сохранен как backup:
  `frontend/public/assets/buildings/industry/mine/backup_2026-10-14_pre_mountain_detail_runtime/`.
- `MINE_ASSET_REVISION` обновлен на
  `mountain-detail-runtime-2026-10-14`, чтобы frontend не использовал старый
  кеш PNG/GLB.
- Building renderer теперь читает `render.size` и `anchor` из
  `buildingAssetManifests`; для шахты задан формат `512x512` с anchor
  `[256,320]`, соответствующий staging terrain-camera. Сохраненные старые
  `mine_l01_construction` и `mine_l01_damaged` допакованы из `512x384` в
  `512x512` с offset `[0,28]`, чтобы не растягиваться при новом anchor.
- Обновлены runtime `manifest.json` и `generation-report.json`.
- Проверки прошли: сверка наличия 36 manifest items и PNG/GLB файлов, проверка
  PNG-размеров, targeted frontend tests `buildingSpriteAssets.test.ts`,
  `buildingModelAssets.test.ts`, `buildingRegistry.test.ts`,
  `objectDrawData.test.ts`.

Обновление 7 на 2026-10-14:

- Для шахты L1 созданы недостающие новые состояния
  `mine_l01_construction_mountain_detail` и
  `mine_l01_damaged_mountain_detail` в
  `frontend/public/assets/terrain/tiles/mountain_detail_staging/`.
- Massive staging manifest расширен до 38 ассетов: активная L1-шахта остается в
  исходном `manifest.json`, а construction/damaged L1 теперь лежат в
  `manifest_massive.json` рядом с L2-L12. Состояния используют ту же L1-скалу,
  открытый портал и внешнюю арку; construction показывает частично собранную
  крепь, damaged - поврежденную крепь, обломки и темные сколы без перекрытия
  входа.
- Новые L1 construction/damaged подключены в runtime вместо временно
  сохраненных старых файлов:
  `frontend/public/assets/buildings/industry/mine/mine_l01_construction.*` и
  `frontend/public/assets/buildings/industry/mine/mine_l01_damaged.*`.
- Предыдущие runtime-файлы этих двух состояний сохранены в backup:
  `frontend/public/assets/buildings/industry/mine/backup_2026-10-14_pre_l01_state_replacement/`.
- `MINE_ASSET_REVISION` обновлен на
  `mountain-detail-runtime-l01-states-2026-10-14`; runtime `manifest.json` и
  `generation-report.json` больше не помечают L1 construction/damaged как
  `retained_from_backup`.
- Проверки прошли: Blender MCP generation через UNC-путь, визуальный review
  сохраненных PNG в игровом ракурсе, `python3
  tools/assets/validate_mountain_detail_massive_staging.py` на 38 ассетах.

## Нефтяная вышка / Spec И Active L1

Рабочие файлы:

- Spec: `docs/assets/specs/industry/oil_well.yaml`.
- Документация: `docs/buildings/resource-buildings/oil-well.md`.
- Генератор: `tools/assets/blender/generate_oil_well_models.py`.
- Runtime-папка: `frontend/public/assets/buildings/industry/oil_well/`.
- Мастер-сцена: `frontend/public/assets/buildings/industry/oil_well/oil_well_levels.blend`.
- Визуальный обзор:
  `frontend/public/assets/buildings/industry/oil_well/state-review.png`.

Состояние на 2026-10-14:

- Добавлен catalog-bound spec для текущего уровня 1 `oil_well` с
  `style_profile: aeolian_fantasy_midpoly`, общей flat ground-клеткой,
  стандартным building PNG `512x384`, anchor `[256,292]`, material map
  `metal/planks/oil`, states `active/construction/damaged/ruined` и
  правилами изометрического стиля Real City.
- В `docs/buildings/resource-buildings/oil-well.md` уточнен раздел
  моделирования: нефтяная вышка должна использовать общий стиль построек,
  яркую плоскую ground-клетку, локальное нефтяное пятно, крупные readable
  props и материалы из стоимости.
- Существующий runtime-набор пересобран через Windows Blender CLI:
  12 PNG и 12 GLB для уровней 1-3 и состояний
  `active/construction/damaged/ruined`. Для текущего запроса проверен
  `oil_well_l01_active`: 2286 triangles, bounds
  `[[-1.8,-1.8,0.0],[1.8,1.8,1.603]]`, PNG `512x384`, alpha bounds
  `[102,157,411,364]`.
- Генератор обновлен: `generation-report.json` теперь фиксирует
  `material_resources`, а `alpha_bounds` считается и без PIL внутри Windows
  Blender.
- Проверки прошли: Blender MCP `get_addon_status`/`get_scene_info`,
  visual review по runtime PNG и `state-review.png`,
  `python3 tools/assets/validate_asset_specs.py
  docs/assets/specs/industry/oil_well.yaml`,
  `python3 tools/assets/validate_building_manifests.py
  frontend/public/assets/buildings/industry/oil_well/manifest.json`,
  `python3 tools/assets/validate_building_sprites.py
  frontend/public/assets/buildings/industry/oil_well/manifest.json`,
  `python3 -m py_compile tools/assets/blender/generate_oil_well_models.py`,
  roundtrip report без loose vertices, `git diff --check`.
- Ограничения: MCP `look` снова не создал `/tmp/blender_look_*.png`;
  screenshot-review выполнен по экспортированным runtime PNG/contact sheet.
  `validate_building_lods.py` для `oil_well` ожидает новый manifest-формат с
  LOD0/LOD1/LOD2 records, а текущий генератор нефтяной вышки экспортирует один
  GLB на состояние.

## Экономный шаблон следующего запроса

```text
$real-city-blender-models продолжи по docs/assets/asset-generation-status.md.
Задача: <коротко, что именно изменить>.
Объем: <уровни/состояния/папка>.
Отчет: кратко - изменено, пути, проверки, что осталось.
Логи не вставлять в чат; проверяй файлы логов сам.
```

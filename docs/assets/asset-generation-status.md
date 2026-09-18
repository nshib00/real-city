# Статус генерации ассетов

Документ служит короткой рабочей памятью для следующих итераций генерации
моделей. Обновляй его после каждой крупной партии ассетов, чтобы не повторять
в чате длинную историю требований, логов и проверок.

## Как использовать

- В новых запросах можно писать: "продолжи по `docs/assets/asset-generation-status.md`".
- Подробные правила стиля держи в `skills/real-city-blender-models/SKILL.md`.
- Большие Blender-логи не вставляй в чат; проси проверить конкретный файл лога.
- Финальный ответ по ассетам проси в коротком формате: что изменено, куда
  сохранено, какие проверки прошли, что осталось.

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
- Для построек ранее добавлялось правило совпадения земли у active,
  construction и damaged состояний.

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

## Экономный шаблон следующего запроса

```text
$real-city-blender-models продолжи по docs/assets/asset-generation-status.md.
Задача: <коротко, что именно изменить>.
Объем: <уровни/состояния/папка>.
Отчет: кратко - изменено, пути, проверки, что осталось.
Логи не вставлять в чат; проверяй файлы логов сам.
```

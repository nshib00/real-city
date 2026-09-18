# Model Brief Workflow

Use this structure when preparing a Blender-ready building brief.

## 1. Identify the Object

- Russian display name.
- Internal id if it exists in `shared/catalog/buildings.ts`.
- Category: housing, fields, industry, defense, roads, storage, social, trade, center.
- Footprint in tiles.
- Place in upgrade chain.
- Required gameplay states: planned, building, active, damaged, ruined, upgrading.

## 2. Define Map Readability

Answer these before describing details:

- What should the player recognize in 0.5 seconds?
- What makes this building different from neighboring buildings of the same category?
- What single silhouette feature survives at low zoom?
- Which details can be exaggerated for isometric readability?

Recommended height classes:

| Class | Use | Notes |
| --- | --- | --- |
| Very low | roads, fields, small ruins | Should not hide adjacent tiles |
| Low | dugouts, walls, small storage | Strong roof/ground silhouette |
| Medium | wooden/stone houses, workshops | Clear facade and roof |
| Tall | town hall, towers, factories | Use sparingly as landmarks |
| Very tall | skyscrapers, late monuments | Needs special camera/readability checks |

## 3. Build Level Progression

For each level, specify:

- Core shape change.
- Material upgrade.
- New readable prop or structural element.
- Color/accent change.
- Animation/state difference if any.

Progression should feel cumulative:

- Level 1: rough, temporary, low detail.
- Level 2: reinforced, cleaner footprint.
- Level 3: recognizable permanent function.
- Level 4: visibly advanced, extra props or annexes.
- Level 5+: prestige, complexity, stronger materials, production/status signals.

## 4. Blender Modeling Notes

Include:

- Primitive base shapes to start from.
- Approximate proportions by tile size.
- Main mesh parts and which should be separate objects.
- Bevel needs and edge softness.
- Material slots.
- Optional procedural details.
- What not to model because it will not read in-game.

## 5. State Variants

At minimum:

- `active`: normal completed model.
- `construction`: незавершенная конструкция, открытый каркас, частичные стены и кровля; дополнительные леса и материалы. Для нескольких стадий последовательно достраивать основание, каркас, стены, крышу и отделку.
- `damaged`: крупные проломы, обрушенные части, сломанные опоры и обломки материалов; трещины и потемнение только дополняют геометрию разрушений.
- Материалы: сопоставить каждый материальный ресурс стоимости и предыдущих апгрейдов с видимой частью здания; например, ветролист с лиственным покрытием, сталь с креплениями. Монеты не требуют изображения.

Optional:

- `ruined`: collapsed but identifiable.
- `working`: smoke, wheel motion, glow, liquid, crop sway.
- `upgrading`: stronger construction overlay than initial build.

## 6. Export Notes

Use stable names:

- `<building_id>_l01_active`
- `<building_id>_l01_construction`
- `<building_id>_l01_damaged`
- `<building_id>_l02_active`

Prefer `.glb` for runtime delivery unless the project pipeline specifies otherwise. Keep source `.blend` files organized by category and chain.

# Asset Type Rules

Use these rules to keep different Real City model types consistent. Project docs in `docs/` remain the source of truth; `docs/visual-style-guide.md` is the primary 3D art bible. These rules only convert that documentation into modeling decisions.

## Buildings

- Use `docs/buildings/` as the source of truth.
- Each upgrade level needs its own model or clearly separate mesh variant.
- Show progression through material, massing, props, height, roof complexity, and detail density.
- Use optimized stylized mid-poly detail, not primitive low-poly blockouts: shaped massing, bevels, roof thickness, facade layers, readable doors/windows, and functional props are expected.
- Keep one recognizable anchor across upgrades: doorway, foundation, chimney, footprint edge, courtyard, or road connection.
- Required states for gameplay assets: `active`, `construction`, `damaged`.
- Construction показывает реально незавершенную конструкцию с открытым каркасом и отсутствующими частями стен, кровли и отделки. Леса и временные запасы дополняют здание, таймер остается интерфейсным элементом.
- Damaged показывает крупные проломы, обрушение части крыши, сломанные опоры и обломки; косметические пятна недостаточны.
- Материальные ресурсы стоимости уровня и накопленной цепочки апгрейдов должны быть видимы в конструкции. Для каждого ресурса укажи соответствующую часть здания; монеты и нематериальные затраты исключаются.
- Keep the footprint obvious. A 1x1 building should not visually occupy neighboring tiles; 2x2 and larger buildings need clear base edges.
- Use `shared/catalog/buildings.ts` for ids, names, categories, build times, population, costs, and upgrade chain if runtime integration is involved.

## Housing

- Use `docs/buildings/houses/` first.
- Early housing: low, practical, earth/wood-heavy.
- Землянка: low earth mound, turf roof, wooden entrance, chimney, gradual transition to a proper wooden house.
- Землянки: уровень 2 заметно укреплен бревнами; на уровнях 3-5 растет плотность крупных зеленых листьев ветролиста согласно стоимости (2, 5 и 11). Уровень 4 получает дощатый фасад и навес, уровень 5 обязательно имеет деревянную обвязку основания по периметру, включая заднюю и боковые стороны, с проходом у входа.
- Wooden homes: warm, domestic, stable, with readable roofs, doors, windows, chimneys, small yards.
- Stone homes: sturdier, cleaner, more urban.
- Dense city housing: vertical, compact, balconies and repeated windows.
- Prestige housing: gardens, terraces, symmetry, brighter materials, decorative details.

## Industry

- Use `docs/buildings/industry/` first.
- Functional silhouette first: chimney, tanks, pipes, belts, cranes, loading zones.
- Mid/late production can show fuel use through pipes, barrels, dark tanks, and amber lights.
- Oil wells must be rare and visually black/dark on the map.
- Нефтеперерабатывающий завод should show tanks, pipes, distillation column, barrels, and controlled steam/light.
- Avoid making industry grimy enough to dominate the tone. It should read as clean stylized production inside a bright rebuilding world.

## Fields and Crops

- Use `docs/buildings/fields/` first.
- Stay low so they do not hide the map.
- Model growth stages: planting, early, middle, late, ready.
- Super crops need larger scale, unusual color, glow, or rare product detail.
- Fields produce resources and coins, not food.
- If a field has a super-version, make every super growth stage distinct enough to notice on the map.

## Nature

- Forests: bright, dense, readable groups of stylized trees; avoid individual tiny leaves. Provide three chop-density models when the forest tile is interactive:
  - dense: many trees, full canopy, no buildable ground;
  - thinned once: fewer trees, visible stumps and gaps;
  - thinned twice: sparse trees, more stumps, mostly visible grass;
  - cleared state is ordinary meadow/grass and can use the normal grass tile.
- Mountains: chunky stylized silhouettes with readable large planes, bevels and material breaks, grey stone palette, usable as blockers. Do not make them too tall to hide adjacent buildings.
- Rivers: clear blue path with bright edges; keep flow readable from above. Segment edges should tile cleanly.
- Oil wells: rare strategic cells, black/dark resource identity, pumpjack/tower silhouette, oil stains, pipes or barrels.
- Resource nodes: signal extractability, not decoration. Use material cues from `shared/catalog/resources.ts` and the resource list in `docs/visual-style-and-setting-options.md`.
- Base terrain colors for temporary material passes: light green meadow, dark green forest, grey mountain, blue river, black oil well, orange ruins.

## Ruins

- Ruins are capturable objects with buffs.
- They need states: neutral, guarded, clearing, captured, contested, restored, damaged.
- Use broken but useful silhouettes: foundations, arches, columns, old machines, overgrowth.
- Add banners or markers only for ownership/state, not as permanent visual clutter.
- Ruins are very rare on the map, so they may be more visually distinctive than normal props. Use orange/warm markers, pale old stone, moss, cracks, and restrained magical accents.
- A ruin must not look like a random destroyed player building. It needs an ancient civic, industrial, archive, garden, water, bastion, shrine, or obelisk identity.

## Roads and Walls

- Use `docs/buildings/roads/` and defense catalog entries first.
- Roads are flat and readable: ground, improved, paved/masonry.
- Walls evolve by material: wooden, stone, concrete, modern.
- Each wall stage has internal levels and should show reinforcement, not just color changes.
- Wall levels should connect cleanly in straight lines and corners if the runtime later supports adjacency variants.

## Monsters and Threats

- Must read as hostile at map scale.
- Use distinct silhouettes and warning colors without making the whole world dark.
- Keep geometry optimized enough for many map objects, but avoid primitive placeholder anatomy in final models.

## Materials and Resource Cues

- Монеты: warm gold/yellow metal, simple coin stack or stamped token if modeled.
- Эолийские кристаллы: thin elongated amethyst hexagonal crystals, clean highlights, restrained glow.
- Древесина/доски: pale warm wood; keep logs and planks visually distinct.
- Камень/каменные блоки: light grey stone; blocks have clearer cut edges.
- Кирпич: warm red/orange masonry.
- Стекло: pale cyan transparent or glossy panels.
- Нефть: black glossy liquid and dark tanks.
- Бензин: amber liquid, cans, pipes, or warning-colored small tanks.

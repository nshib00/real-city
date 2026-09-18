---
name: real-city-blender-buildings
description: Create, review, or refine Blender-ready building model briefs and implementation plans for Real City. Use when Codex needs to design buildings, upgrade chains, modular asset requirements, stylized fantasy mid-poly/isometric visual rules, Blender modeling instructions, material palettes, export checklists, or prompt/modeling specs that must match the Real City setting, especially for housing, town hall, factories, fields, walls, roads, alliance buildings, ruins, and resource structures.
---

# Real City Blender Buildings

Use this skill to produce Blender-ready building specifications for Real City, not generic fantasy houses.

## Required Context

Before writing a model brief or changing asset docs, inspect the current project sources:

- `docs/visual-style-guide.md` - primary 3D art bible: bright fantasy stylized mid-poly, Aeolian motifs, material language, budgets, states, and quality gate.
- `docs/visual-style-and-setting-options.md` - primary setting and building direction.
- `docs/plans/plan.md` - planned asset/modeling phases and progress.
- `shared/catalog/buildings.ts` - current building names, categories, levels, costs, and upgrade chains.
- Existing `frontend/src/assets/` or `reference/images/` files if the task mentions implementation, screenshots, or visual continuity.

Read only the relevant sections. Prefer `rg "Землянка|Ратуша|стена|..."` over opening large files from the start.

Also use local Blender skills from `skills/blender-skills/` when the brief touches modeling execution:

- Always relevant: `blender-director`, `fantasy-worlds`, `stylized-style`, `isometric-style`, `asset-optimization`.
- Add by need: `materials`, `uv-workflow`, `texture-workflow`, `export-pipeline`, `environment-artist`, `prop-artist`, `vegetation-artist`, `animation`.
- Do not use `lowpoly-style` as Real City art direction. It is allowed only for distant LOD, collision/proxy meshes, or throwaway blockouts.

## Output Standard

For each building or upgrade chain, produce:

1. Gameplay role: why the object exists and how it reads on the map.
2. Tile and scale: footprint, height class, silhouette, camera readability.
3. Level-by-level visual progression: each level must look like an upgrade of the previous one.
4. Modeling brief: base forms, proportions, materials, details, anchors, optional modular parts.
5. Animation/state requirements: construction overlay, active state, damaged state, idle motion, production hints.
6. Resource and cost table when balance is part of the request.
7. Export requirements: file naming, pivot/origin, scale, LOD, material slots, texture constraints.

When the user asks to create actual Blender files, first check whether Blender or a project asset pipeline exists. If not, create a precise model brief and an implementation plan rather than inventing unverified files.

## Real City Style Rules

- Keep the game surface readable from an isometric strategy camera.
- Prefer compact, expressive, optimized stylized mid-poly forms with strong silhouettes.
- Do not produce primitive low-poly buildings as final assets. A valid Real City model needs shaped massing, visible bevels, volumetric doors/windows/roof thickness, readable facade layers, functional props, and hand-painted-like material treatment.
- Use warm, readable materials: earth, grass, pale wood, stone, brick, metal, glass, concrete, fuel/oil details, and restrained amethyst accents for eolian crystals.
- Avoid copying Gnomgrad names, characters, exact object forms, UI, icons, or copyrighted assets.
- Do not make buildings look like generic grimdark fantasy props. Real City is bright, practical, rebuild-after-silence fantasy with gradual industrialization.
- Do not use decorative purple glow everywhere. Eolian crystal accents should be rare, intentional, and tied to premium/magical systems.
- Every upgrade level needs its own model or at least its own clearly distinct mesh variant.
- Клетка земли в `construction` и `damaged` копируется из `active` соответствующего уровня: одинаковые грунт, покрытие, дорожки, геометрия, материалы, UV и положение. Не перекрашивай и не центрируй основание по габаритам разрушенного здания. Обломки и стройматериалы остаются отдельными объектами; фундамент здания не следует путать с клеткой земли. У спрайтов сохраняй камеру, масштаб, anchor, свет и цветовой профиль active; проверяй совпадение основания в GLB и рендерах.
- Стройка показывает незавершенную конструкцию: недостроенные стены, открытые стропила, частичную крышу, неустановленные окна. Леса и запасы материалов дополняют ее; готовая active-модель с лесами не подходит.
- Повреждения должны быть крупными и геометрическими: проломы, обрушенная кровля, сломанные опоры и обломки. Темные пятна или небольшие трещины не заменяют разрушение. Тип постройки остается узнаваемым по сохранившимся частям.
- Перед моделированием составь соответствие материальных ресурсов стоимости уровня и предшествующих апгрейдов видимым частям здания. Все строительные материалы должны читаться в конструкции: доски, каменные блоки, ветролист, сталь и другие ресурсы. Не заменяй это одними запасами во дворе; монеты не изображай буквально. Новые ресурсы должны заметно менять апгрейд.
- Damaged/ruined versions should preserve the silhouette enough for identification.

## Blender Modeling Defaults

- Work in meters or a consistent project unit; keep one map tile as the base scale reference.
- Set origin/pivot to the tile footprint base center unless the project asset pipeline says otherwise.
- Keep transforms applied before export.
- Use named collections by object and level, for example `dugout_l01`, `dugout_l02`.
- Separate major semantic parts when useful: base, roof, door, chimney, props, construction overlay, damage overlay.
- Use simple materials first; texture detail can come later.
- Keep small props oversized enough to read from the game camera.
- Avoid fine geometry that disappears at gameplay zoom.
- Use the triangle-budget bands in `docs/visual-style-guide.md`; optimize with LOD and atlases instead of stripping the model down to primitive forms.

## Reference Files

- For full Real City art direction, read `../../docs/visual-style-guide.md`.
- For step-by-step model brief structure, read `references/model-brief-workflow.md`.
- For Real City visual language and material direction, read `references/setting-visual-rules.md`.
- For Blender/export validation checklists, read `references/blender-export-checklist.md`.

## Decision Rules

- If gameplay data conflicts with art direction, preserve gameplay readability first.
- If docs and code conflict, mention the mismatch and prefer the latest explicit user request.
- If a building belongs to an upgrade chain, describe the full chain context enough to prevent a disconnected one-off model.
- If the model is for an early-game object, keep it modest and practical; save height, glass, metal, and magical polish for later stages.
- If the user asks for multiple variants, make each variant differ by gameplay identity, not only decoration.

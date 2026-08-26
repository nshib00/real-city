---
name: real-city-blender-buildings
description: Create, review, or refine Blender-ready building model briefs and implementation plans for Real City. Use when Codex needs to design buildings, upgrade chains, modular asset requirements, low-poly/isometric visual rules, Blender modeling instructions, material palettes, export checklists, or prompt/modeling specs that must match the Real City setting, especially for housing, town hall, factories, fields, walls, roads, alliance buildings, ruins, and resource structures.
---

# Real City Blender Buildings

Use this skill to produce Blender-ready building specifications for Real City, not generic fantasy houses.

## Required Context

Before writing a model brief or changing asset docs, inspect the current project sources:

- `docs/visual-style-and-setting-options.md` - primary setting and building direction.
- `docs/plans/plan.md` - planned asset/modeling phases and progress.
- `shared/catalog/buildings.ts` - current building names, categories, levels, costs, and upgrade chains.
- Existing `frontend/src/assets/` or `reference/images/` files if the task mentions implementation, screenshots, or visual continuity.

Read only the relevant sections. Prefer `rg "Землянка|Ратуша|стена|..."` over opening large files from the start.

## Output Standard

For each building or upgrade chain, produce:

1. Gameplay role: why the object exists and how it reads on the map.
2. Tile and scale: footprint, height class, silhouette, camera readability.
3. Level-by-level visual progression: each level must look like an upgrade of the previous one.
4. Modeling brief: primitive forms, proportions, materials, details, anchors, optional modular parts.
5. Animation/state requirements: construction overlay, active state, damaged state, idle motion, production hints.
6. Resource and cost table when balance is part of the request.
7. Export requirements: file naming, pivot/origin, scale, LOD, material slots, texture constraints.

When the user asks to create actual Blender files, first check whether Blender or a project asset pipeline exists. If not, create a precise model brief and an implementation plan rather than inventing unverified files.

## Real City Style Rules

- Keep the game surface readable from an isometric strategy camera.
- Prefer compact, expressive, low-to-mid poly forms with strong silhouettes.
- Use warm, readable materials: earth, grass, pale wood, stone, brick, metal, glass, concrete, fuel/oil details, and restrained amethyst accents for eolian crystals.
- Avoid copying Gnomgrad names, characters, exact object forms, UI, icons, or copyrighted assets.
- Do not make buildings look like generic grimdark fantasy props. Real City is bright, practical, rebuild-after-silence fantasy with gradual industrialization.
- Do not use decorative purple glow everywhere. Eolian crystal accents should be rare, intentional, and tied to premium/magical systems.
- Every upgrade level needs its own model or at least its own clearly distinct mesh variant.
- Construction visuals must sit on top of the building model: scaffold, beams, dust, worker markers, progress timer, then removal when complete.
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

## Reference Files

- For step-by-step model brief structure, read `references/model-brief-workflow.md`.
- For Real City visual language and material direction, read `references/setting-visual-rules.md`.
- For Blender/export validation checklists, read `references/blender-export-checklist.md`.

## Decision Rules

- If gameplay data conflicts with art direction, preserve gameplay readability first.
- If docs and code conflict, mention the mismatch and prefer the latest explicit user request.
- If a building belongs to an upgrade chain, describe the full chain context enough to prevent a disconnected one-off model.
- If the model is for an early-game object, keep it modest and practical; save height, glass, metal, and magical polish for later stages.
- If the user asks for multiple variants, make each variant differ by gameplay identity, not only decoration.

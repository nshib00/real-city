# Model Quality Checklist

Use before final response after creating or editing a model.

## Documentation Match

- Target object documentation was inspected.
- Relevant local references in `reference/buildings/` and/or `reference/images/` were inspected for buildings.
- Reference material was used only for readability/style principles, not copied as names, exact forms, UI, icons, images, or identity.
- Internal id and display name are correct.
- Category and upgrade chain are correct.
- Required levels and states match docs/catalog.
- Для каждого материального ресурса стоимости уровня и предыдущих апгрейдов найдена читаемая часть конструкции; новые материалы заметны на модели, а не только в запасах рядом.
- If docs and catalog disagree, the mismatch was reported and the latest explicit user requirement was followed.
- The model does not copy Gnomgrad-specific visual identity, names, UI, or copyrighted assets.
- The model follows `docs/visual-style-guide.md`: bright fantasy Real City style, optimized stylized mid-poly, Aeolian motifs where appropriate, and no primitive low-poly final look.

## Blender Scene Quality

- Collections are organized by asset, level, and state.
- Object names are deterministic and lowercase where possible.
- Origin is at tile footprint base center.
- Transforms are applied.
- Meshes have no accidental duplicates or hidden test leftovers.
- Materials are named and assigned.
- Visible model edges use deliberate bevels or shaped stylized forms where needed.
- Doors, windows, roofs, supports, facade layers, and key props are volumetric enough for final assets, not flat placeholder marks.
- Small details are large enough for isometric camera readability.
- Silhouette is recognizable without UI text.
- Footprint boundaries are readable and do not spill into neighboring tiles unless the documented footprint is larger than 1x1.
- Palette matches Эолия: bright, practical, readable, not grimdark.
- The asset does not look like a simple blockout made from basic primitives.

## Gameplay State Quality

- Active model is clean and readable.
- Земля, покрытие и дорожки construction/damaged совпадают с active того же уровня в экспортированных GLB: геометрия, материалы, UV и положение. В PNG совпадают ракурс, масштаб и anchor клетки; различия естественных теней допустимы. Проверка текущего набора: `python3 tools/assets/validate_building_ground.py`.
- Construction имеет реальные недостроенные стены, открытый каркас и частичную крышу; леса отделены от незавершенного здания. Сравнение с active показывает недостающие конструктивные части.
- Damaged имеет крупные геометрические разрушения и обломки, заметные на маленьком спрайте, сохраняя узнаваемый тип здания. Одних темных пятен недостаточно.
- Resource nodes show neutral/claimed/depleted states.
- Oil wells are dark/black and rare-looking.
- Fields show crop stage differences.
- Forest tiles show three chop-density states when forest chopping is part of the requested asset.
- Ruins show capture-relevant states when the requested ruin is gameplay-active.
- Roads/walls connect cleanly enough for repeated placement.

## Export Quality

- `.blend` source saved.
- `.glb` export created when requested.
- Export re-import or validation was performed when MCP tools allow it.
- File paths are reported exactly.
- Any unvalidated assumption is stated clearly.

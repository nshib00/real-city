# Model Quality Checklist

Use before final response after creating or editing a model.

## Documentation Match

- Target object documentation was inspected.
- Internal id and display name are correct.
- Category and upgrade chain are correct.
- Required levels and states match docs/catalog.
- Resource/material cues match the economy where relevant.
- If docs and catalog disagree, the mismatch was reported and the latest explicit user requirement was followed.
- The model does not copy Gnomgrad-specific visual identity, names, UI, or copyrighted assets.

## Blender Scene Quality

- Collections are organized by asset, level, and state.
- Object names are deterministic and lowercase where possible.
- Origin is at tile footprint base center.
- Transforms are applied.
- Meshes have no accidental duplicates or hidden test leftovers.
- Materials are named and assigned.
- Small details are large enough for isometric camera readability.
- Silhouette is recognizable without UI text.
- Footprint boundaries are readable and do not spill into neighboring tiles unless the documented footprint is larger than 1x1.
- Palette matches Эолия: bright, practical, readable, not grimdark.

## Gameplay State Quality

- Active model is clean and readable.
- Construction overlay sits on top of the model and can be removed.
- Damaged model remains identifiable.
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

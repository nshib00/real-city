# Blender Export Checklist

Use this checklist before considering a building model ready for implementation.

## Scene Hygiene

- Object names are stable and match the building id and level.
- Collections are organized by building and state.
- Transforms are applied.
- Origin is at tile footprint base center.
- Scale matches the project tile size.
- No hidden stray meshes, lights, cameras, or test objects are exported accidentally.
- Normals face outward.
- Bevels are intentional and not excessive.

## Gameplay Readability

- Silhouette is recognizable from isometric camera distance.
- Door/entry or functional face is readable.
- Footprint does not visually invade unrelated tiles unless intended.
- Important props are large enough to see.
- Materials differ enough between levels.
- Upgrade level is recognizable without UI text.
- Construction overlay does not fully hide the completed model.
- Timer/progress UI has a clear space and does not collide with tall geometry.

## Performance

- Mesh complexity matches object importance.
- Repeated small props are instanced or simple.
- Materials are limited and named.
- Texture sizes are modest.
- Transparent materials are avoided unless necessary.
- Animated parts are few and separable.

## State Variants

Required states:

- active
- construction
- damaged

Recommended states for important objects:

- ruined
- upgrading
- working/producing

## Export

- Prefer `.glb` for runtime asset delivery.
- Keep `.blend` as source.
- Use one exported file per building level/state if the runtime pipeline is simple.
- Use one file with named collections/animations if the runtime pipeline supports it.
- Confirm that exported files re-import correctly.
- Confirm material names survive export.
- Confirm scale and pivot after import.

# Blender MCP Procedure

Use this when actually working with Blender through MCP.

## Tool Discovery

- First discover available Blender MCP tools if they are not already loaded.
- Use the MCP tools for scene inspection, object creation, material setup, save/export, and screenshots/previews when available.
- Do not use shell automation to pretend Blender work happened if no Blender MCP connection exists.

## Connection

- Prefer discovered Blender MCP tools over shell automation.
- From WSL, do not connect to Windows Blender services through `localhost` or `127.0.0.1`.
- Use `172.28.192.1` as the Windows host address when a host must be configured.
- If connection fails, check whether Blender is running, whether its MCP add-on/server is active, which port it listens on, and whether Windows Firewall allows WSL connections.

## Scene Inspection

Before edits, inspect:

- units and scale;
- existing collections;
- selected object;
- object origins;
- material list;
- cameras/lights;
- export settings or custom pipeline notes.

Do not clear a scene unless the user asked for a new clean file or the current scene is clearly disposable.

If the scene contains existing Real City assets, preserve their naming, scale, material style, and collection hierarchy unless the requested model explicitly changes the convention.

## Creation Workflow

1. Create a collection named after the asset id.
2. Add level/state collections if needed:
   - `asset_id_l01_active`
   - `asset_id_l01_construction`
   - `asset_id_l01_damaged`
3. Block out the main silhouette first.
4. Add large readable secondary forms.
5. Add props only after silhouette and scale work.
6. Assign simple named materials.
7. Apply transforms.
8. Set origin to tile footprint base center.
9. Add optional camera only for preview, not as required runtime data.

For upgrade chains, create a visible progression in separate level collections before adding fine details. Each level should be understandable as the same object upgraded through construction and resources, not as unrelated buildings.

For nature/resource tiles, create tileable or repeatable variants where useful. Forests need density/chop variants; rivers and roads need clean segment continuity; ruins need state variants if capture gameplay is involved.

## Validation

Validate in Blender before final response:

- object names are stable;
- collection structure is clean;
- no accidental hidden test meshes;
- origin and scale are correct;
- materials are assigned;
- model reads from an isometric camera angle;
- construction/damaged variants do not obscure identification;
- `.blend` is saved;
- `.glb` is exported if requested.

If validation cannot be performed through MCP, state that explicitly.

When screenshots or preview renders are possible, inspect the model from an isometric camera angle and at a small gameplay-like size. Fix details that disappear, overlap, or confuse the silhouette.

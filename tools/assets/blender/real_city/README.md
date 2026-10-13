# Real City Blender API

Этот пакет — общий слой для генераторов Blender-ассетов Real City. Он нужен,
чтобы новые модели создавались через один API, одну камеру, одну палитру,
одинаковые ground-правила, одинаковый экспорт и одинаковые отчеты.

## Публичные модули

- `constants.py` — размер спрайта `512x384`, anchor `[256, 292]`, tile size,
  состояния и dataclass-и для output/render profile.
- `paths.py` — корень проекта, public/src директории, `blender_path()` для
  Windows Blender из WSL.
- `scene.py` — очистка сцены, новая сцена, изометрическая камера, свет,
  прозрачный PNG, Cycles/AgX.
- `materials.py` — единая палитра и создание материалов через node type
  `BSDF_PRINCIPLED`.
- `geometry.py` — коллекции, box/cylinder/sphere/cone/beam/roof/flag,
  clean mesh, bounds и triangle count.
- `ground.py` — стандартная плоская ground-клетка с именами
  `earth_tile`, `grass_tile`, `path_stone`, совместимыми с валидаторами.
- `state.py` — show/select helpers для collection-per-state генераторов.
- `export.py` — `.blend`, `.glb`, PNG render, manifest/report helpers.
- `validation.py` — легкие проверки GLB/manifest без запуска Blender.
- `spec.py` — загрузка и нормализация YAML/JSON asset specs без зависимости от
  Blender: levels, states, material map, style/skill profile, LOD и PNG policy.
- `components/` — reusable component library: крыши, стены, props, housing,
  civic, industry, fields, storage, aeolian accents и mid-poly detail kits.

## Минимальный шаблон генератора

```python
from tools.assets.blender.real_city import AssetOutput, RenderProfile, project_root
from tools.assets.blender.real_city import scene, materials, geometry, ground, export

root = project_root()
output = AssetOutput("example_building", "industry", root, use_public_glb=True)
profile = RenderProfile()

scene.clear_scene()
asset_scene = scene.new_scene("example_building_generation")
scene.configure_asset_scene(asset_scene, profile, light_prefix="example_building")
mats = materials.create_palette("MAT_example_building")

collection = geometry.create_collection("example_building_l01_active")
ground.add_ground_tile(collection, mats, prefix="example_building")
geometry.box("example_body", collection, (0, 0, 0.45), (1.2, 1.0, 0.8), mats["wood_pale"])
geometry.clean_meshes(collection)

output.runtime_dir.mkdir(parents=True, exist_ok=True)
export.export_state_assets("example_building_l01_active", collection, output.runtime_dir)
export.save_blend(output.blend_path)
```

## Asset specs

Новые фабричные генераторы должны читать короткую спецификацию из
`docs/assets/specs/**/*.yaml` через `load_asset_spec()`, а не держать все
правила уровня и стиля в большом prompt или локальном генераторе.

Минимальный smoke-прогон спецификаций:

```bash
python3 tools/assets/validate_asset_specs.py docs/assets/specs/housing/dugout.yaml docs/assets/specs/housing/wood_house.yaml docs/assets/specs/center/town_hall.yaml
```

## Правила миграции старых генераторов

1. Сначала заменить локальные `setup_camera`, `clear_scene`, `palette` и
   export helpers на API из этого пакета.
2. Затем заменить повторяющиеся primitive helpers на `geometry.py`.
3. Ground переносить через `ground.add_ground_tile()` и больше не генерировать
   отдельно для construction/damaged.
4. После миграции генератора прогнать профильные валидаторы и сравнить contact
   sheet с предыдущей партией.

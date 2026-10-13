"""Windows/Blender entry point for regenerating Real City coin storage assets."""

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
GENERATOR = HERE / "generate_coin_storage_models.py"

spec = importlib.util.spec_from_file_location("real_city_coin_storage_models", str(GENERATOR))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print(module.generate())

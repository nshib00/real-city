"""Preserve the first villa prototype and build a second, 20% larger version."""

from __future__ import annotations

import math
from contextlib import contextmanager

from tools.assets.blender import build_villa_l01_test as original


SCALE_FROM_SAVED_VERSION = math.sqrt(1.2)
ASSET_NAME = "villa_l01_active_v2"
OUTPUT = original.ROOT / "frontend/public/assets/buildings/housing/villa_v2_test"
SOURCE_REL = "frontend/public/assets/buildings/housing/villa_v2_test"


@contextmanager
def _variant_settings():
    previous = original.ASSET_NAME, original.OUTPUT, original.SOURCE_REL
    original.ASSET_NAME = ASSET_NAME
    original.OUTPUT = OUTPUT
    original.SOURCE_REL = SOURCE_REL
    try:
        yield
    finally:
        original.ASSET_NAME, original.OUTPUT, original.SOURCE_REL = previous


def preview():
    with _variant_settings():
        return original.preview(architecture_scale=SCALE_FROM_SAVED_VERSION)


def generate():
    with _variant_settings():
        report = original.generate(architecture_scale=SCALE_FROM_SAVED_VERSION)
    report["generator"] = "tools/assets/blender/build_villa_l01_v2_test.py"
    report["previous_variant"] = "frontend/public/assets/buildings/housing/villa_test/villa_l01_active.blend"
    import json
    (OUTPUT / "generation-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    generate()

"""Build only level six of the production stone-house family."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.assets.blender.generate_stone_house_models import finalize, generate_level


if __name__ == "__main__":
    generate_level(6)
    finalize()

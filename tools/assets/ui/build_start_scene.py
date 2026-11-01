"""Compatibility entry point for exporting the Blender start-page assets."""
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
blender = shutil.which("blender")
if not blender:
    raise SystemExit("Blender не найден в PATH. Запустите build_start_blender_assets.py через установленный Blender.")

subprocess.run([
    blender,
    "-b",
    "--factory-startup",
    "--python",
    str(ROOT / "tools/assets/ui/build_start_blender_assets.py"),
], cwd=ROOT, check=True)
subprocess.run([
    "python3",
    str(ROOT / "tools/assets/ui/export_start_blender_assets.py"),
], cwd=ROOT, check=True)

"""Prepare browser-sized images from the Blender start-page renders."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "tools/assets/ui/start-city"
FAVICON_SOURCE = ROOT / "tools/assets/ui/favicon"
START = ROOT / "frontend/public/assets/ui/start"
FAVICON = ROOT / "frontend/public"

START.mkdir(parents=True, exist_ok=True)
image = Image.open(SOURCE / "start-city-render.png").convert("RGB")
image.resize((960, 656), Image.Resampling.LANCZOS).save(START / "settlement-960.webp", "WEBP", quality=86, method=6)
# The full map remains visible on mobile; CSS scales this portrait-friendly variant without cropping.
mobile = image.resize((480, 328), Image.Resampling.LANCZOS)
mobile.save(START / "settlement-480.webp", "WEBP", quality=84, method=6)

mark = Image.open(FAVICON_SOURCE / "eolia-emblem-512.png").convert("RGBA")
mark.resize((256, 256), Image.Resampling.LANCZOS).save(START / "eolia-mark.png", optimize=True)
for size in (16, 32, 48, 180, 192, 512):
    mark.resize((size, size), Image.Resampling.LANCZOS).save(FAVICON / f"favicon-{size}.png", optimize=True)
mark.save(FAVICON / "favicon.ico", format="ICO", sizes=[(16,16),(32,32),(48,48)])
mark.resize((180,180), Image.Resampling.LANCZOS).save(FAVICON / "apple-touch-icon.png", optimize=True)
print({str(path.relative_to(ROOT)): path.stat().st_size for path in [
    START/"settlement-960.webp", START/"settlement-480.webp", START/"eolia-mark.png",
    FAVICON/"favicon.ico", FAVICON/"favicon-32.png", FAVICON/"apple-touch-icon.png"]})

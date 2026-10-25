"""Обновить версии существующих MP3 в сгенерированном manifest без перекодирования."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
path = ROOT / "frontend/src/audio/soundManifest.ts"
text = path.read_text(encoding="utf-8")
manifest = json.loads(text.split("// DATA:", 1)[1].splitlines()[0])
for sound_id, variants in manifest.items():
    for index, url in enumerate(variants):
        base = url.split("?", 1)[0]
        asset = ROOT / "frontend/public" / base.lstrip("/")
        digest = hashlib.sha256(asset.read_bytes()).hexdigest()[:12]
        variants[index] = f"{base}?v={digest}"
data = json.dumps(dict(sorted(manifest.items())), ensure_ascii=False, separators=(",", ":"))
path.write_text(
    "import type { SoundId } from './soundEvents'\n\n"
    "/** Сгенерировано tools/audio/build_audio.py. */\n"
    f"// DATA:{data}\n"
    f"export const soundManifest: Partial<Record<SoundId, readonly string[]>> = {data}\n",
    encoding="utf-8",
)
print(f"Версионировано {len(manifest)} sound_id")

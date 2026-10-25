"""Сборка выбранных рецептов в обработанные WAV, MP3 и клиентский manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from generate_sfx import ROOT, load_recipes, render, write_wav
from validate_audio import validate_wav

PROJECT = ROOT.parents[1]
PUBLIC = PROJECT / "frontend/public/assets/audio"
MANIFEST = PROJECT / "frontend/src/audio/soundManifest.ts"


def run(command: list[str]) -> None:
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL)


def build(sound_ids: list[str], ffmpeg: str, candidate: str, recordings: dict[str, Path], wav_only: bool = False, bitrate: str = "64k") -> None:
    if not wav_only and not shutil.which(ffmpeg):
        raise SystemExit(f"FFmpeg не найден: {ffmpeg}. См. docs/audio/production-guide.md")
    if wav_only and recordings:
        raise SystemExit("Режим --wav-only поддерживает только синтезированные рецепты")
    recipes = load_recipes()
    current = {}
    if MANIFEST.exists():
        text = MANIFEST.read_text(encoding="utf-8")
        marker = "// DATA:"
        if marker in text:
            current = json.loads(text.split(marker, 1)[1].splitlines()[0])
    with tempfile.TemporaryDirectory(prefix="real-city-audio-") as directory:
        temporary = Path(directory)
        for sound_id in sound_ids:
            recipe = recipes[sound_id]
            family = sound_id.split(".", 1)[0]
            variants = []
            for index in range(len(recipe["variants"])):
                raw = temporary / "raw.wav"
                processed = temporary / "processed.wav"
                name = f"{sound_id}.{index}"
                master = ROOT / "master" / f"{name}.wav"
                master.parent.mkdir(parents=True, exist_ok=True)
                if wav_only:
                    write_wav(master, render(recipe, candidate, index))
                    validate_wav(master)
                    target = PUBLIC / family / f"{name}.wav"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(master, target)
                    digest = hashlib.sha256(target.read_bytes()).hexdigest()[:12]
                    variants.append(f"/assets/audio/{family}/{name}.wav?v={digest}")
                    continue
                if sound_id in recordings:
                    recording = recordings[sound_id]
                    if not recording.is_file():
                        raise SystemExit(f"Запись не найдена: {recording}")
                    pitch = recipe["variants"][index].get("pitch", 1)
                    run([ffmpeg, "-v", "error", "-y", "-i", str(recording), "-af",
                         f"aresample=48000,asetrate=48000*{pitch},aresample=48000", "-t",
                         str(recipe["candidates"][candidate]["duration"]), "-ar", "48000", "-ac", "1",
                         "-c:a", "pcm_s16le", str(raw)])
                else:
                    write_wav(raw, render(recipe, candidate, index))
                # Trim/fades and a ceiling of −3 dBFS; sample rate and channel count are explicit.
                duration = recipe["candidates"][candidate]["duration"]
                fade_out = max(0, duration - 0.018)
                filters = (f"highpass=f=35,afade=t=in:st=0:d=0.004,"
                           f"afade=t=out:st={fade_out:.4f}:d=0.018,"
                           "acompressor=threshold=0.35:ratio=1.5:attack=3:release=60,"
                           "alimiter=limit=0.7079:level=0")
                run([ffmpeg, "-v", "error", "-y", "-i", str(raw), "-af", filters,
                     "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(processed)])
                validate_wav(processed)
                target = PUBLIC / family / f"{name}.mp3"
                target.parent.mkdir(parents=True, exist_ok=True)
                master.parent.mkdir(parents=True, exist_ok=True)
                run([ffmpeg, "-v", "error", "-y", "-i", str(processed), "-ar", "48000", "-ac", "1",
                     "-c:a", "libmp3lame", "-b:a", bitrate, str(target)])
                run([ffmpeg, "-v", "error", "-xerror", "-i", str(target), "-f", "null", "-"])
                shutil.copyfile(processed, master)
                digest = hashlib.sha256(target.read_bytes()).hexdigest()[:12]
                variants.append(f"/assets/audio/{family}/{name}.mp3?v={digest}")
            current[sound_id] = variants
    data = json.dumps(dict(sorted(current.items())), ensure_ascii=False, separators=(",", ":"))
    MANIFEST.write_text(
        "import type { SoundId } from './soundEvents'\n\n"
        "/** Сгенерировано tools/audio/build_audio.py. */\n"
        f"// DATA:{data}\n"
        f"export const soundManifest: Partial<Record<SoundId, readonly string[]>> = {data}\n",
        encoding="utf-8",
    )
    print(f"Собрано {len(sound_ids)} звуков: {', '.join(sound_ids)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sound_ids", nargs="*")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--candidate", choices=("a", "b"), default="a")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--wav-only", action="store_true", help="Собрать синтезированные WAV без FFmpeg")
    parser.add_argument("--bitrate", choices=("32k", "48k", "64k"), default="64k")
    parser.add_argument("--recording", action="append", default=[], metavar="SOUND_ID=PATH")
    args = parser.parse_args()
    recipes = load_recipes()
    ids = list(recipes) if args.all else args.sound_ids
    if not ids or any(sound_id not in recipes for sound_id in ids):
        parser.error("Укажите существующий sound_id или --all")
    recordings = {}
    for item in args.recording:
        if "=" not in item:
            parser.error("--recording требует SOUND_ID=PATH")
        sound_id, path = item.split("=", 1)
        recordings[sound_id] = Path(path)
    build(ids, args.ffmpeg, args.candidate, recordings, args.wav_only, args.bitrate)


if __name__ == "__main__":
    main()

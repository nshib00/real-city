"""Проверка формата, длительности и пикового уровня WAV master."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import struct
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def validate_wav(path: Path, minimum: float = 0.03, maximum: float = 2.0) -> dict:
    with wave.open(str(path), "rb") as source:
        channels, width, rate, count = source.getnchannels(), source.getsampwidth(), source.getframerate(), source.getnframes()
        if (channels, width, rate) != (1, 2, 48_000):
            raise ValueError(f"{path}: нужен mono PCM16 48 кГц, получено {channels}ch/{width * 8}bit/{rate}Hz")
        duration = count / rate
        if not minimum <= duration <= maximum:
            raise ValueError(f"{path}: длительность {duration:.3f} с вне [{minimum}, {maximum}]")
        data = source.readframes(count)
    samples = struct.unpack(f"<{count}h", data)
    peak = max(map(abs, samples), default=0) / 32768
    if peak < 0.005:
        raise ValueError(f"{path}: тишина или слишком низкий уровень")
    if peak > 10 ** (-2.5 / 20):
        raise ValueError(f"{path}: пик {20 * math.log10(peak):.1f} dBFS выше лимита −2.5 dBFS")
    tail = samples[-min(len(samples), int(rate * 0.005)):]
    if max(map(abs, tail), default=0) / 32768 > 0.25:
        raise ValueError(f"{path}: слишком громкий хвост, возможна обрезка")
    return {"duration": round(duration, 4), "peak_dbfs": round(20 * math.log10(peak), 2)}


def validate_catalog(ffmpeg: str) -> dict:
    from generate_sfx import load_recipes

    manifest_path = ROOT / "frontend/src/audio/soundManifest.ts"
    source = manifest_path.read_text(encoding="utf-8")
    manifest = json.loads(source.split("// DATA:", 1)[1].splitlines()[0])
    event_source = (ROOT / "frontend/src/audio/soundEvents.ts").read_text(encoding="utf-8")
    events = set(re.findall(r"'((?:ui|economy|build|world|combat|social|ambience)\.[a-z0-9_.]+)'", event_source))
    recipes = set(load_recipes())
    if set(manifest) != events or set(manifest) != recipes:
        raise ValueError(f"Несовпадение ID: manifest-only={set(manifest)-events}, event-only={events-set(manifest)}, recipe-only={recipes-set(manifest)}")
    public = ROOT / "frontend/public/assets/audio"
    masters = ROOT / "tools/audio/master"
    listed = []
    for sound_id, variants in manifest.items():
        if not variants or len(variants) != len(set(variants)):
            raise ValueError(f"{sound_id}: пустой список или повтор варианта")
        for index, url in enumerate(variants):
            expected = f"/assets/audio/{sound_id.split('.')[0]}/{sound_id}.{index}.mp3"
            if not url.startswith(expected):
                raise ValueError(f"{sound_id}: неожиданный путь {url}")
            mp3 = public / expected.removeprefix("/assets/audio/")
            wav = masters / f"{sound_id}.{index}.wav"
            if not mp3.is_file() or not wav.is_file():
                raise ValueError(f"{sound_id}: отсутствует MP3 или WAV master")
            digest = hashlib.sha256(mp3.read_bytes()).hexdigest()[:12]
            if url != f"{expected}?v={digest}":
                raise ValueError(f"{sound_id}: версия файла не совпадает с содержимым")
            validate_wav(wav, maximum=10 if sound_id.startswith('ambience.') else 2)
            result = subprocess.run([ffmpeg, "-hide_banner", "-xerror", "-i", str(mp3), "-f", "null", "-"], capture_output=True, text=True)
            if result.returncode:
                raise ValueError(f"{mp3}: ошибка декодирования: {result.stderr.strip()}")
            if not re.search(r"Audio: mp3[^\n]*48000 Hz, mono", result.stderr):
                raise ValueError(f"{mp3}: нужен MP3 mono 48 кГц")
            listed.append(mp3.resolve())
    actual = {path.resolve() for path in public.rglob("*.mp3") if path.parent.name != 'music'}
    if actual != set(listed):
        raise ValueError(f"Неучтённые MP3: {actual-set(listed)}; отсутствуют: {set(listed)-actual}")
    expected_masters = {masters / f"{sound_id}.{index}.wav" for sound_id, variants in manifest.items() for index in range(len(variants))}
    actual_masters = set(masters.glob("*.wav"))
    if actual_masters != expected_masters:
        raise ValueError(f"Неучтённые WAV master: {actual_masters-expected_masters}; отсутствуют: {expected_masters-actual_masters}")
    return {"sounds": len(manifest), "files": len(listed)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--catalog", action="store_true", help="Проверить весь каталог и MP3")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    arguments = parser.parse_args()
    if arguments.catalog:
        binary = shutil.which(arguments.ffmpeg)
        if not binary:
            parser.error(f"FFmpeg не найден: {arguments.ffmpeg}")
        print(validate_catalog(binary))
    for file in arguments.files:
        print(file, validate_wav(file))

"""Детерминированный синтез коротких mono WAV без внешних зависимостей."""

from __future__ import annotations

import argparse
import json
import math
import random
import struct
import wave
from pathlib import Path

RATE = 48_000
ROOT = Path(__file__).resolve().parent


def load_recipes() -> dict[str, dict]:
    recipes = {}
    for path in sorted((ROOT / "recipes").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for recipe in data.get("sounds", []):
            sound_id = recipe["sound_id"]
            if sound_id in recipes:
                raise ValueError(f"Повторный sound_id: {sound_id}")
            recipe["recipe_file"] = path.name
            recipes[sound_id] = recipe
    return recipes


def envelope(time: float, duration: float, adsr: list[float]) -> float:
    attack, decay, sustain, release = adsr
    if time < attack:
        return time / max(attack, 1 / RATE)
    if time < attack + decay:
        return 1 - (1 - sustain) * (time - attack) / max(decay, 1 / RATE)
    if time < duration - release:
        return sustain
    return sustain * max(0, (duration - time) / max(release, 1 / RATE))


def render(recipe: dict, candidate: str, variant: int) -> list[float]:
    options = recipe["candidates"]
    if candidate not in options:
        raise ValueError(f"Нет кандидата {candidate} для {recipe['sound_id']}")
    variations = recipe["variants"]
    if not 0 <= variant < len(variations):
        raise ValueError(f"Нет варианта {variant} для {recipe['sound_id']}")
    settings = options[candidate]
    variation = variations[variant]
    duration = settings["duration"]
    count = round(duration * RATE)
    output = [0.0] * count
    pitch = variation.get("pitch", 1.0)
    attack_scale = variation.get("attack", 1.0)
    texture = variation.get("texture", 1.0)
    for layer_index, layer in enumerate(settings["layers"]):
        rng = random.Random(recipe["seed"] + variant * 1009 + layer_index * 101 + ord(candidate[0]) * 17)
        waveform = layer["wave"]
        frequency = layer.get("frequency", 440) * pitch
        sweep = layer.get("sweep", 0)
        gain = layer.get("gain", 1.0) * (texture if waveform == "noise" else 1)
        start = layer.get("start", 0)
        length = min(layer.get("duration", duration - start), duration - start)
        adsr = list(layer.get("adsr", [0.005, 0.03, 0.5, 0.08]))
        adsr[0] *= attack_scale
        lowpass = layer.get("lowpass", 1.0)
        previous = 0.0
        for i in range(round(start * RATE), min(count, round((start + length) * RATE))):
            t = i / RATE - start
            phase = 2 * math.pi * (frequency * t + sweep * t * t / 2)
            if waveform == "sine":
                sample = math.sin(phase)
            elif waveform == "triangle":
                sample = 2 / math.pi * math.asin(math.sin(phase))
            elif waveform == "noise":
                sample = rng.uniform(-1, 1)
            else:
                raise ValueError(f"Неизвестный генератор: {waveform}")
            previous += lowpass * (sample - previous)
            output[i] += previous * gain * envelope(t, length, adsr)
    echo = settings.get("echo")
    if echo:
        delay = round(echo["delay"] * RATE)
        for i in range(delay, count):
            output[i] += output[i - delay] * echo["gain"]
    peak = max((abs(value) for value in output), default=0)
    if peak:
        scale = min(1, 0.7 / peak)
        output = [value * scale for value in output]
    return output


def write_wav(path: Path, samples: list[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(RATE)
        output.writeframes(struct.pack(f"<{len(samples)}h", *(round(max(-1, min(1, value)) * 32767) for value in samples)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sound_id")
    parser.add_argument("--candidate", default="a")
    parser.add_argument("--variant", type=int, default=0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    recipes = load_recipes()
    if args.sound_id not in recipes:
        parser.error(f"Неизвестный sound_id: {args.sound_id}")
    target = args.output or ROOT / "master" / f"{args.sound_id}.{args.candidate}.{args.variant}.wav"
    write_wav(target, render(recipes[args.sound_id], args.candidate, args.variant))
    print(target)


if __name__ == "__main__":
    main()

"""Проверка формата, длительности и пикового уровня WAV master."""

from __future__ import annotations

import argparse
import math
import struct
import wave
from pathlib import Path


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
    return {"duration": round(duration, 4), "peak_dbfs": round(20 * math.log10(peak), 2)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    arguments = parser.parse_args()
    for file in arguments.files:
        print(file, validate_wav(file))

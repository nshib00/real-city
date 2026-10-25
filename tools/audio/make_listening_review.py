"""Создать обезличенные WAV-пары для слепого прослушивания."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from generate_sfx import ROOT, load_recipes, render, write_wav


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "review")
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    key = {}
    lines = ["# Слепое прослушивание", "", "Отметьте лучший файл для каждого действия, не открывая `answer-key.json`.", ""]
    for sound_id, recipe in load_recipes().items():
        if not {"a", "b"}.issubset(recipe["candidates"]):
            continue
        candidates = ["a", "b"]
        rng.shuffle(candidates)
        codes = []
        for number, candidate in enumerate(candidates, 1):
            code = f"{sound_id.replace('.', '_')}_{number}"
            write_wav(args.output / f"{code}.wav", render(recipe, candidate, 0))
            key[code] = {"sound_id": sound_id, "candidate": candidate, "variant": 0}
            codes.append(code)
        lines.append(f"- `{sound_id}`: `{codes[0]}.wav` / `{codes[1]}.wav`; выбор: ____; замечания: ____")
    (args.output / "лист.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (args.output / "answer-key.json").write_text(json.dumps(key, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()

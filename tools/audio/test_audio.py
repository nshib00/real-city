"""Проверки воспроизводимости рецептов и формата WAV."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from generate_sfx import load_recipes, render, write_wav
from validate_audio import validate_wav


class AudioRecipesTest(unittest.TestCase):
    def test_all_candidates_are_deterministic_and_valid(self) -> None:
        recipes = load_recipes()
        self.assertTrue({
            "combat.weapon.cannon", "combat.weapon.storm_coil", "combat.defense.stakes",
            "combat.monster.ancient_colossus.death", "combat.loot.claimed",
        }.issubset(recipes))
        with tempfile.TemporaryDirectory() as directory:
            for sound_id, recipe in recipes.items():
                self.assertGreaterEqual(len(recipe["variants"]), 1 if sound_id.startswith("ambience.") else 2)
                self.assertLessEqual(len(recipe["variants"]), 5)
                for candidate in recipe["candidates"]:
                    self.assertIn(candidate, recipe["candidates"])
                    hashes = set()
                    for variant in range(len(recipe["variants"])):
                        samples = render(recipe, candidate, variant)
                        self.assertEqual(samples, render(recipe, candidate, variant))
                        path = Path(directory) / f"{sound_id}.{candidate}.{variant}.wav"
                        write_wav(path, samples)
                        validate_wav(path)
                        hashes.add(hashlib.sha256(path.read_bytes()).hexdigest())
                    self.assertEqual(len(hashes), len(recipe["variants"]))


if __name__ == "__main__":
    unittest.main()

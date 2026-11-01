import unittest
from audit_sources import closure


def recipe(name, inputs, outputs, fuel=0):
    return {"ID": name, "Input": [{"Resource": item} for item in inputs],
            "Output": [{"Resource": item} for item in outputs], "FuelPerRun": fuel}


class SourcesTest(unittest.TestCase):
    def test_fuel_cycle_does_not_unlock_itself(self):
        result = closure([recipe("oil", ["planks"], ["oil"], 1),
                          recipe("refine", ["oil"], ["fuel"])], {"planks"})
        self.assertEqual({r["recipe"] for r in result["blocked"]}, {"oil", "refine"})

    def test_external_seed_unlocks_chain_independent_of_recipe_order(self):
        result = closure([recipe("parts", ["metal"], ["parts"], 2),
                          recipe("smelt", ["ore"], ["metal"])], {"ore", "fuel"})
        self.assertEqual(result["blocked"], [])
        self.assertEqual(result["resource_producers"]["parts"], "parts")

    def test_rare_output_is_not_a_guaranteed_source(self):
        first = recipe("first", [], ["stone"])
        first["RareOutput"] = [{"Resource": "gem", "Chance": 0.01}]
        result = closure([first, recipe("second", ["gem"], ["tool"])], set())
        self.assertEqual(result["blocked"][0]["missing"], ["gem"])


if __name__ == "__main__":
    unittest.main()

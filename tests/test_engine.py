import json
import os
import tempfile
import unittest

from categories.registry import get_categories, get_domains
from engine.generator import parse_weights
from engine.sampler import build_domain_pool, sample_spec
from engine.storage import load_records, make_record, save_records


class CategoryTests(unittest.TestCase):
    def test_builtin_categories_and_domains(self):
        self.assertEqual(set(get_categories()), {"math", "coding", "science", "cs", "creative", "conversation"})
        self.assertEqual(len(get_domains()), 48)

    def test_domain_pool_and_sampling(self):
        pool = build_domain_pool()
        self.assertTrue(pool)
        spec = sample_spec(pool)
        self.assertIn(spec["main_category"], get_categories())
        self.assertIn(spec["difficulty_level"], range(1, 11))

    def test_weight_parser(self):
        self.assertEqual(parse_weights("math=0.5,coding=0.5"), {"math": 0.5, "coding": 0.5})

    def test_output_schema(self):
        spec = {"main_category": "math", "domain": "Algebra", "subdomain": "linear_equations", "difficulty_level": 2}
        record = make_record("Contoh pertanyaan", spec, 1)
        self.assertEqual(list(record), ["question", "language", "main_category", "domain", "subdomain", "difficulty_level", "id"])
        self.assertEqual(record["id"], "000001")

    def test_save_load_round_trip(self):
        record = {
            "question": "Apa kabar?",
            "language": "Indonesia",
            "main_category": "conversation",
            "domain": "Percakapan",
            "subdomain": "santai",
            "difficulty_level": 1,
            "id": "000001",
        }
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "output.json")
            save_records(path, [record])
            self.assertTrue(open(path, encoding="utf-8").read().endswith("\n"))
            self.assertEqual(load_records(path), [record])
            with open(path, encoding="utf-8") as handle:
                json.load(handle)


if __name__ == "__main__":
    unittest.main()

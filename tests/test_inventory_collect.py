import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ipfw_inventory_collect as module


class InventoryCollectorTests(unittest.TestCase):
    @patch.object(module, "run")
    def test_collects_only_aggregates(self, run):
        run.side_effect = [
            "00100 1 1 deny ip from 192.0.2.5 to me\n"
            "00110 1 1 deny ip from 192.0.2.5 to me\n",
            "",
        ]
        result = module.collect()
        self.assertEqual(result["status"], 1)
        self.assertEqual(result["host_unique"], 1)
        self.assertEqual(result["host_duplicate_extra"], 1)
        self.assertNotIn("192.0.2.5", str(result))

    @patch.object(module, "run")
    def test_incomplete_does_not_return_partial_totals(self, run):
        run.side_effect = [
            "00100 1 1 deny ip from table(8) to me\n",
            "",
        ]
        result = module.collect()
        self.assertEqual(result["status"], 0)
        self.assertNotIn("host_unique", result)
        self.assertEqual(result["missing_referenced_tables"], 1)


if __name__ == "__main__":
    unittest.main()

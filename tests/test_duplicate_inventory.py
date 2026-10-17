import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ipfw_duplicate_inventory import summarize

class DuplicateInventoryTests(unittest.TestCase):
    def test_no_tables(self):
        result = summarize(
            "01000 9 90 deny log ip from 192.0.2.10 to me\n"
            "01010 1 10 deny log ip from 192.0.2.10 to me\n"
            "65535 3 33 allow ip from any to any\n", "")
        self.assertEqual(result["status"], 1)
        self.assertEqual(result["host_unique"], 1)
        self.assertEqual(result["host_duplicate_extra"], 1)

    def test_multiple_tables_and_cross_source_duplicates(self):
        rules = ("00040 5 300 deny log tcp from table(10) to me\n"
                 "00050 4 200 deny log tcp from table(20) to me\n"
                 "01000 1 60 deny log ip from 192.0.2.10 to me\n")
        tables = ("--- table(10), set(0) ---\n192.0.2.10/32 0\n198.51.100.2/32 0\n"
                  "--- table(20), set(0) ---\n192.0.2.10/32 0\n")
        r = summarize(rules, tables)
        self.assertEqual(r["status"], 1)
        self.assertEqual(r["host_unique"], 2)
        self.assertEqual(r["host_occurrences"], 4)
        self.assertEqual(r["host_duplicate_extra"], 2)

    def test_missing_table_is_incomplete(self):
        r = summarize("00040 1 1 deny ip from table(30) to me", "")
        self.assertEqual(r["status"], 0)
        self.assertEqual(r["missing_referenced_tables"], 1)

    def test_ipv6_host_duplicates(self):
        r = summarize(
            "01000 1 1 deny ip from 2001:db8::1 to me\n"
            "01010 1 1 deny ip from 2001:0db8:0:0::1/128 to me\n", "")
        self.assertEqual(r["status"], 1)
        self.assertEqual(r["host_unique"], 1)
        self.assertEqual(r["host_duplicate_extra"], 1)

    def test_multiple_tables_with_no_duplicates(self):
        rules = ("00010 1 1 deny ip from table(10) to me\n"
                 "00020 1 1 deny ip from table(20) to me\n")
        tables = ("--- table(10), set(0) ---\n192.0.2.10/32 0\n"
                  "--- table(20), set(0) ---\n198.51.100.10/32 0\n")
        r = summarize(rules, tables)
        self.assertEqual(r["status"], 1)
        self.assertEqual(r["host_unique"], 2)
        self.assertEqual(r["host_duplicate_extra"], 0)

    def test_same_table_id_different_sets_is_incomplete(self):
        rules = "00100 1 1 deny ip from table(10) to me\n"
        tables = ("--- table(10), set(0) ---\n192.0.2.1/32 0\n"
                  "--- table(10), set(1) ---\n198.51.100.1/32 0\n")
        r = summarize(rules, tables)
        self.assertEqual(r["status"], 0)
        self.assertEqual(r["ambiguous_referenced_tables"], 1)

    def test_ipv6_prefix_is_not_host(self):
        r = summarize("01000 1 1 deny ip from 2001:db8::/64 to me\n", "")
        self.assertEqual(r["status"], 1)
        self.assertEqual(r["host_unique"], 0)
        self.assertEqual(r["prefix_unique"], 1)

    def test_destination_table_does_not_count_as_blocked_source(self):
        r = summarize("00100 1 1 deny ip from 192.0.2.10 to table(20)\n", "")
        self.assertEqual(r["status"], 1)
        self.assertEqual(r["missing_referenced_tables"], 0)
        self.assertEqual(r["host_unique"], 1)

    def test_unknown_table_listing_fails_closed(self):
        r = summarize("00100 1 1 deny ip from table(20) to me\n",
                      "unexpected output\n")
        self.assertEqual(r["status"], 0)
        self.assertGreater(r["unsupported_sources"], 0)

    def test_unknown_rule_source_fails_closed(self):
        r = summarize("00100 1 1 deny ip from not-an-ip to me\n", "")
        self.assertEqual(r["status"], 0)

    def test_unused_table_not_counted(self):
        r = summarize("00100 1 1 deny ip from 192.0.2.10 to me\n",
                      "--- table(20), set(0) ---\n198.51.100.10/32 0\n")
        self.assertEqual(r["status"], 1)
        self.assertEqual(r["host_unique"], 1)

    def test_named_table_header_is_not_silently_accepted(self):
        rules = "00100 1 1 deny ip from table(10) to me\n"
        tables = ("--- table(10), set(0) ---\n192.0.2.1/32 0\n"
                  "--- table(blocklist), set(0) ---\n198.51.100.1/32 0\n")
        r = summarize(rules, tables)
        self.assertEqual(r["status"], 0)
        self.assertGreater(r["unsupported_sources"], 0)

    def test_prefix_not_a_host(self):
        r = summarize("01000 1 1 deny ip from 192.0.2.0/24 to me", "")
        self.assertEqual(r["host_unique"], 0)
        self.assertEqual(r["prefix_unique"], 1)

if __name__ == "__main__":
    unittest.main()

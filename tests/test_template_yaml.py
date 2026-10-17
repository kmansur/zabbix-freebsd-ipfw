#!/usr/bin/env python3
"""Static checks for public Zabbix template structure (not an import test)."""
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates/zabbix-7.0/freebsd_ipfw_by_zabbix_agent.yaml"

class RejectDuplicateKeys(yaml.SafeLoader):
    pass

def construct_mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        if key in result:
            raise ValueError(f"Duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=True)
    return result

RejectDuplicateKeys.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping
)

class TemplateChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.export = yaml.load(TEMPLATE.read_text(encoding="utf-8"), Loader=RejectDuplicateKeys)
        cls.template = cls.export["zabbix_export"]["templates"][0]

    def test_metadata(self):
        self.assertEqual(self.export["zabbix_export"]["version"], "7.0")
        self.assertEqual(self.template["vendor"], {"name": "Net Tech", "version": "0.1.5"})

    def test_no_template_level_triggers(self):
        self.assertNotIn("triggers", self.template)

    def test_no_fixed_table_identifier(self):
        keys = [x["key"] for x in self.template.get("items", [])]
        self.assertFalse(any("table40" in key for key in keys))
        rules = self.template["discovery_rules"]
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]["item_prototypes"][0]["key"],
                         "ipfw.table.set.entries[{#TABLE_ID},{#TABLE_SET}]")
        self.assertTrue(rules[0].get("graph_prototypes"))

    def test_inventory_item_dependencies(self):
        items = {item["key"]: item for item in self.template["items"]}
        self.assertEqual(items["ipfw.inventory.raw"]["delay"], "5m")
        mapping = {
            "ipfw.inventory.status": "$.status",
            "ipfw.inventory.host.unique": "$.host_unique",
            "ipfw.inventory.host.occurrences": "$.host_occurrences",
            "ipfw.inventory.host.duplicates": "$.host_duplicate_extra",
            "ipfw.inventory.prefix.unique": "$.prefix_unique",
            "ipfw.inventory.prefix.occurrences": "$.prefix_occurrences",
            "ipfw.inventory.prefix.duplicates": "$.prefix_duplicate_extra",
        }
        for key, path in mapping.items():
            item = items[key]
            self.assertEqual(item["type"], "DEPENDENT")
            self.assertEqual(item["master_item"]["key"], "ipfw.inventory.raw")
            self.assertEqual(item["preprocessing"][0]["parameters"][0], path)

    def test_inventory_nodata_trigger(self):
        items = {item["key"]: item for item in self.template["items"]}
        raw = items["ipfw.inventory.raw"]
        expressions = [trigger["expression"] for trigger in raw.get("triggers", [])]
        self.assertIn(
            "nodata(/FreeBSD IPFW by Zabbix Agent/ipfw.inventory.raw,15m)=1",
            expressions,
        )

    def test_all_graph_items_reference_existing_keys(self):
        keys = {item["key"] for item in self.template["items"]}
        for graph in self.export["zabbix_export"].get("graphs", []):
            for graph_item in graph["graph_items"]:
                self.assertIn(graph_item["item"]["key"], keys)

    def test_agent_userparameters_cover_passive_keys(self):
        agent = (ROOT / "agent/userparameter_ipfw.conf").read_text(encoding="utf-8")
        declared = set()
        for line in agent.splitlines():
            if line.startswith("UserParameter="):
                key = line.split("=", 1)[1].split(",", 1)[0]
                declared.add(key.replace("[*]", ""))
        for item in self.template["items"]:
            if item["type"] == "ZABBIX_PASSIVE":
                key = item["key"].split("[", 1)[0]
                self.assertIn(key, declared)
        for rule in self.template["discovery_rules"]:
            if rule["type"] == "ZABBIX_PASSIVE":
                self.assertIn(rule["key"], declared)
            for prototype in rule.get("item_prototypes", []):
                if prototype["type"] == "ZABBIX_PASSIVE":
                    self.assertIn(prototype["key"].split("[", 1)[0], declared)

    def test_graphs(self):
        self.assertGreaterEqual(len(self.export["zabbix_export"].get("graphs", [])), 4)

    def test_public_content(self):
        import re
        text = TEMPLATE.read_text(encoding="utf-8")
        self.assertNotRegex(text, r"\b192\.168\.\d{1,3}\.\d{1,3}\b")
        self.assertNotRegex(text, r"\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
        self.assertNotRegex(text, r"\b172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}\b")

    def test_privacy_regex_detects_private_examples(self):
        import re
        patterns = [
            r"\b192\.168\.\d{1,3}\.\d{1,3}\b",
            r"\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
            r"\b172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}\b",
        ]
        fixtures = ["192.168.2.1", "10.8.5.4", "172.20.1.10"]
        for pattern, fixture in zip(patterns, fixtures):
            self.assertIsNotNone(re.search(pattern, fixture))


if __name__ == "__main__":
    unittest.main()

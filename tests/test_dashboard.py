"""Verify native dashboard references and layout, not a snapshot of styling."""
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]


class DashboardChecks(unittest.TestCase):
    def test_user_interface_is_english_ascii(self):
        for version in ('7.0', '8.0'):
            path = ROOT / f'templates/{version}/freebsd_ipfw_by_zabbix_agent.yaml'
            text = path.read_bytes().decode('utf-8')
            self.assertTrue(text.isascii())
            dashboard = yaml.safe_load(text)['zabbix_export']['templates'][0]['dashboards'][0]
            self.assertEqual([p['name'] for p in dashboard['pages']],
                             ['Operations', 'Textual inventory', 'Table atlas'])
            names = [w['name'] for p in dashboard['pages'] for w in p['widgets']]
            self.assertIn('Flow | Denied traffic/s', names)
            self.assertIn('Rule composition', names)
            self.assertIn('Table count over time', names)
            for marker in ('\u00c3', '\u00c2', '\ufffd'):
                self.assertNotIn(marker, text)

    def test_references_and_layout(self):
        data = yaml.safe_load((ROOT / 'templates/7.0/freebsd_ipfw_by_zabbix_agent.yaml').read_text(encoding='utf-8'))['zabbix_export']
        template = data['templates'][0]
        keys = {i['key'] for i in template['items']}
        graphs = {g['name'] for g in data['graphs']}
        prototypes = {g['name'] for d in template['discovery_rules'] for g in d.get('graph_prototypes', [])}
        dashboard, = template['dashboards']
        self.assertEqual(len(dashboard['pages']), 3)
        for page in dashboard['pages']:
            cells = set()
            for widget in page['widgets']:
                x, y, w, h = (int(widget[k]) for k in ('x', 'y', 'width', 'height'))
                self.assertTrue(0 <= x < x+w <= 72)
                self.assertTrue(0 <= y < y+h <= 64)
                occupied = {(a,b) for a in range(x,x+w) for b in range(y,y+h)}
                self.assertFalse(cells & occupied, widget['name'])
                cells |= occupied
                for field in widget['fields']:
                    if field['type'] in ('ITEM', 'GRAPH', 'GRAPH_PROTOTYPE'):
                        self.assertEqual(field['value']['host'], template['template'])
                        if field['type'] == 'ITEM': self.assertIn(field['value']['key'], keys)
                        elif field['type'] == 'GRAPH': self.assertIn(field['value']['name'], graphs)
                        else: self.assertIn(field['value']['name'], prototypes)

    def test_health_labels_do_not_change_numeric_metrics(self):
        template = yaml.safe_load((ROOT / 'templates/7.0/freebsd_ipfw_by_zabbix_agent.yaml').read_text(encoding='utf-8'))['zabbix_export']['templates'][0]
        mapping, = template['valuemaps']
        self.assertEqual({m['value']: m['newvalue'] for m in mapping['mappings']}, {'0': 'FAILED', '1': 'OK'})
        for item in template['items']:
            if 'valuemap' in item:
                self.assertTrue(item['key'].endswith('status'))
                self.assertEqual(item['valuemap']['name'], mapping['name'])

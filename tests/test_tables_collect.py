import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from ipfw_tables_collect import collect, parse


class TableMetadata(unittest.TestCase):
    def test_empty_tables(self):
        self.assertEqual(parse(''), {'status': 1, 'data': [], 'entries': {}})

    def test_names_and_sets(self):
        text = ''.join(f'--- table(block.list), set({n}) ---\nkindex: 1, type: addr\nitems: {n+4}, size: 100\n'
                       for n in (0, 1))
        result = parse(text)
        self.assertEqual(result['entries'], {'0:block.list': 4, '1:block.list': 5})
        self.assertEqual(len(result['data']), 2)

    def test_malformed_metadata(self):
        for text in ('unexpected', '--- table(a), set(0) ---',
                     '--- table(a), set(0) ---\nkindex: type: addr\nitems: -1',
                     '--- table(a), set(0) ---\nkindex: type: addr\nitems: 1\nitems: 2',
                     '--- table(a), set(0) ---\n--- table(a), set(0) ---'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse(text)

    @patch('ipfw_tables_collect.subprocess.run')
    def test_one_command_per_cycle(self, run):
        run.return_value.stdout = ''.join(
            f'--- table(t{n}), set(0) ---\nkindex: type: addr\nitems: 10,\n' for n in range(1000))
        self.assertEqual(len(collect()['entries']), 1000)
        run.assert_called_once()
        self.assertEqual(run.call_args.kwargs['timeout'], 8)


if __name__ == '__main__':
    unittest.main()

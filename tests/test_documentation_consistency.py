"""Documentation consistency checks for supported public installation paths."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DocumentationConsistency(unittest.TestCase):
    def test_documentation_has_language_pairs(self):
        for path in [ROOT / 'README.md', ROOT / 'CHANGELOG.md', *sorted((ROOT / 'docs').glob('*.md'))]:
            if path.name.endswith('.pt-BR.md'):
                english = path.with_name(path.name.replace('.pt-BR.md', '.md'))
                self.assertTrue(english.is_file(), str(path))
            else:
                portuguese = path.with_name(path.stem + '.pt-BR.md')
                self.assertTrue(portuguese.is_file(), str(path))
            self.assertIn('English', path.read_text(encoding='utf-8'))

    def test_documentation_relative_links_resolve(self):
        import re
        for path in [ROOT / 'README.md', ROOT / 'README.pt-BR.md', *sorted((ROOT / 'docs').glob('*.md'))]:
            for link in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
                if '://' in link or link.startswith('#'):
                    continue
                self.assertTrue((path.parent / link.split('#')[0]).exists(), f'{path}: {link}')

    def test_versioned_template_paths_are_documented(self):
        for path in ("templates/7.0/freebsd_ipfw_by_zabbix_agent.yaml",
                     "templates/8.0/freebsd_ipfw_by_zabbix_agent.yaml"):
            self.assertTrue((ROOT / path).is_file())
            for name in ("README.md", "README.pt-BR.md"):
                self.assertIn(path, (ROOT / name).read_text(encoding="utf-8"))

    def test_main_readme_references_installer_and_pdca(self):
        for name in ("README.md", "README.pt-BR.md"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn("install.sh", text)
            self.assertIn("docs/PDCA-0.1.5.md", text)
            self.assertNotIn("templates/zabbix-7.0/", text)

    def test_install_modes_are_declared(self):
        source = (ROOT / "install.sh").read_text(encoding="utf-8")
        for mode in ("--check", "--install", "--uninstall", "--rollback"):
            self.assertIn(mode, source)


if __name__ == "__main__":
    unittest.main()

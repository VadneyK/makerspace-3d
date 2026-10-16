"""Checks that the plugin's manifests, skills and path references hold together.

Stdlib only. Run from anywhere: python3 -m unittest discover -s tests
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKDOWN = sorted(p for p in ROOT.rglob('*.md') if '.git' not in p.parts)
# Written by /makerspace-3d:setup into ~/makerspace-3d/, not part of the repo.
GENERATED = ('tools/presets',)


def strip_code_fences(text):
    return re.sub(r'```.*?```', '', text, flags=re.S)


class Manifests(unittest.TestCase):
    def test_json_files_parse(self):
        for rel in ('.claude-plugin/plugin.json', '.claude-plugin/marketplace.json', '.mcp.json'):
            with self.subTest(rel):
                json.loads((ROOT / rel).read_text())

    def test_marketplace_plugin_source_resolves(self):
        market = json.loads((ROOT / '.claude-plugin/marketplace.json').read_text())
        for plugin in market['plugins']:
            with self.subTest(plugin['name']):
                src = (ROOT / plugin['source']).resolve()
                self.assertTrue((src / '.claude-plugin/plugin.json').is_file())
                manifest = json.loads((src / '.claude-plugin/plugin.json').read_text())
                self.assertEqual(manifest['name'], plugin['name'])

    def test_mcp_server_is_pinned(self):
        servers = json.loads((ROOT / '.mcp.json').read_text())['mcpServers']
        for name, cfg in servers.items():
            with self.subTest(name):
                self.assertTrue(any(re.search(r'==\d+\.\d+', a) for a in cfg['args']),
                                'the CAD server runs code, keep its version pinned')


class Skills(unittest.TestCase):
    def test_every_skill_has_matching_frontmatter(self):
        skills = sorted((ROOT / 'skills').iterdir())
        self.assertTrue(skills)
        for d in skills:
            with self.subTest(d.name):
                text = (d / 'SKILL.md').read_text()
                m = re.match(r'---\n(.*?)\n---\n', text, flags=re.S)
                self.assertTrue(m, 'missing frontmatter')
                fields = dict(line.split(':', 1) for line in m.group(1).split('\n') if ':' in line)
                self.assertEqual(fields['name'].strip(), d.name)
                self.assertTrue(fields['description'].strip())


class PathReferences(unittest.TestCase):
    def test_relative_markdown_links_resolve(self):
        for md in MARKDOWN:
            text = strip_code_fences(md.read_text())
            for target in re.findall(r'\]\(([^)\s#]+)(?:#[^)]*)?\)', text):
                if re.match(r'[a-z]+:', target):
                    continue
                with self.subTest(f'{md.relative_to(ROOT)} -> {target}'):
                    self.assertTrue((md.parent / target).exists())

    def test_plugin_root_references_resolve(self):
        for md in MARKDOWN:
            text = md.read_text()
            for rel in re.findall(r'\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+)', text):
                with self.subTest(f'{md.relative_to(ROOT)} -> {rel}'):
                    self.assertTrue((ROOT / rel.rstrip('/')).exists())

    def test_repo_paths_in_backticks_resolve(self):
        pattern = re.compile(r'`(?:~/makerspace-3d/)?((?:tools|skills)/[\w./-]+)`')
        for md in MARKDOWN:
            for rel in pattern.findall(md.read_text()):
                rel = rel.rstrip('/')
                if rel.startswith(GENERATED):
                    continue
                with self.subTest(f'{md.relative_to(ROOT)} -> {rel}'):
                    self.assertTrue((ROOT / rel).exists())


class Tools(unittest.TestCase):
    def test_python_tools_compile(self):
        for py in sorted((ROOT / 'tools').glob('*.py')):
            with self.subTest(py.name):
                compile(py.read_text(), str(py), 'exec')


if __name__ == '__main__':
    unittest.main()

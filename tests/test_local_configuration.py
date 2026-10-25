"""Offline regression checks for deployment preparation; no service or GPU calls."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('pipeline_config', ROOT / 'tools/configure_local.py')
CONFIG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONFIG)


class LocalConfiguration(unittest.TestCase):
    def test_utf8_is_explicit_in_text_io_and_node_subprocesses(self):
        # Prevent a regression to Windows' locale-dependent defaults, including emoji in jsCode.
        for directory in ['tools', 'tests']:
            for source in (ROOT / directory).glob('*.py'):
                tree = ast.parse(source.read_text(encoding='utf-8'))
                for node in ast.walk(tree):
                    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                        continue
                    keywords = {keyword.arg: keyword.value for keyword in node.keywords}
                    if node.func.attr in ['read_text', 'write_text']:
                        self.assertIn('encoding', keywords, str(source) + ':' + str(node.lineno))
                    if node.func.attr == 'run' and isinstance(keywords.get('text'), ast.Constant) and keywords['text'].value is True:
                        self.assertIn('encoding', keywords, str(source) + ':' + str(node.lineno))

    def prepare(self, target, **kwargs):
        args = dict(repo=ROOT, target=target, user_id='123456789',
                    output_root='E:/Comfy Output', private_url='https://private.example.org',
                    public_url='https://events.example.org:8443')
        args.update(kwargs)
        return CONFIG.prepare(**args)

    def test_prepares_without_touching_sources_or_secrets(self):
        sources = list((ROOT / 'workflows').glob('*.json')) + list((ROOT / 'comfy/custom_nodes').rglob('*.py'))
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
        with tempfile.TemporaryDirectory(prefix="pipeline's-test-") as t:
            target = Path(t) / 'isolated runtime'
            self.prepare(target)
            exports = sorted((target / 'deployment/workflows').glob('*.json'))
            self.assertEqual(len(exports), 5)
            for path in exports:
                w = json.loads(path.read_text(encoding='utf-8'))
                self.assertFalse(w['active'])
                self.assertFalse(w['pinData'])
                self.assertTrue(all(not n.get('credentials') for n in w['nodes']))
                raw = path.read_text(encoding='utf-8')
                for marker in ['tg-0-', '/0-0.json', 'LOCAL_USER', 'n8n.example.invalid']:
                    self.assertNotIn(marker, raw)
                for n in w['nodes']:
                    code = n.get('parameters', {}).get('jsCode')
                    if code and shutil.which('node'):
                        result = subprocess.run(['node', '-e', 'new (Object.getPrototypeOf(async function(){}).constructor)(require("fs").readFileSync(0,"utf8"))'], input=code, text=True, encoding='utf-8', capture_output=True)
                        self.assertEqual(result.returncode, 0, n['name'] + result.stderr)
            bot = json.loads((target / 'deployment/workflows/telegram-bot.local.json').read_text(encoding='utf-8'))
            auth = next(n for n in bot['nodes'] if n['name'] == 'Authorize Telegram Update')['parameters']['jsCode']
            self.assertIn("ALLOWED_USER_ID = '123456789'", auth)
            self.assertIn("ALLOWED_CHAT_ID = '123456789'", auth)
            main = json.loads((target / 'deployment/workflows/ltx-generation.local.json').read_text(encoding='utf-8'))
            post = next(n for n in main['nodes'] if n['name'] == 'Initialize Post Processing')['parameters']['jsCode']
            self.assertIn('"E:/Comfy Output"', post)
            template = json.loads((target / 'media/workflows/ltx.json').read_text(encoding='utf-8'))
            self.assertEqual(template['398:361']['inputs']['value'], 30)
            self.assertEqual(template['403']['inputs']['megapixels'], 2)
            self.assertEqual(template['398:374']['inputs']['tile_size'], 256)
            control = (target / 'deployment/custom_nodes/n8n_job_control/__init__.py').read_text(encoding='utf-8')
            self.assertIn('tg-123456789-', control)
            self.assertNotIn('tg-0-', control)
            self.assertIn("hmac.compare_digest", control)
            # repr() safely quotes a path containing an apostrophe.
            compile(control, 'configured-control.py', 'exec')
            compose = json.loads((target / 'deployment/compose.local.yaml').read_text(encoding='utf-8'))
            service = compose['services']['n8n']
            self.assertEqual(service['ports'], ['127.0.0.1:5681:5678'])
            self.assertEqual(service['environment']['NODE_FUNCTION_ALLOW_BUILTIN'], 'fs')
            self.assertTrue(service['volumes'][2]['read_only'])
            self.assertFalse((target / 'media/.telegram-ui/comfy-control.key').exists())
            self.assertNotIn('N8N_ENCRYPTION_KEY', service['environment'])
        self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})

    def test_refuses_existing_or_repository_destination(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):
                self.prepare(Path(t))
        with self.assertRaises(ValueError):
            self.prepare(ROOT / 'production')

    def test_rejects_invalid_ids_urls_and_ports(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t) / 'runtime'
            for value in ['0', '-1', '12;bad', 'abc', '1/../2']:
                with self.subTest(user=value), self.assertRaises(ValueError):
                    self.prepare(target, user_id=value)
            for value in ['http://private.example.org', 'https://user:password@example.org',
                          'https://example.org/?token=value', 'https://example.org/path',
                          "https://bad'host", 'https://n8n.example.invalid']:
                with self.subTest(url=value), self.assertRaises(ValueError):
                    self.prepare(target, private_url=value)
            with self.assertRaises(ValueError):
                self.prepare(target, host_port=80)
            with self.assertRaises(ValueError):
                self.prepare(target, public_url='https://events.example.org:9443')
            self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main()

"""Offline ingress boundary tests: inputs, isolation, generated routing, no services."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('ingress_config', ROOT / 'tools/configure_ingress.py')
CONFIG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONFIG)
URL = 'https://example-device.tail-example.ts.net:8443/webhook/EXAMPLE_ID/webhook'


class IngressConfiguration(unittest.TestCase):
    def prepare(self, target, **kwargs):
        args = dict(repo=ROOT, target=target, webhook_url=URL)
        args.update(kwargs)
        return CONFIG.prepare(**args)

    def test_new_private_files_preserve_sources_and_network_boundaries(self):
        sources = list((ROOT / 'examples/telegram-ingress').glob('*'))
        hashes = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources if p.is_file()}
        with tempfile.TemporaryDirectory(prefix="ingress's-test-") as t:
            target = Path(t) / 'private ingress with spaces'
            settings = self.prepare(target, n8n_host_port=5681, gateway_host_port=5682)
            self.assertEqual(settings['public_base_url'], 'https://example-device.tail-example.ts.net:8443/')
            self.assertEqual(settings['private_base_url'], 'https://example-device.tail-example.ts.net/')
            nginx = (target / 'nginx.conf').read_text(encoding='utf-8')
            self.assertIn('location = /webhook/EXAMPLE_ID/webhook {', nginx)
            self.assertIn('location / { return 404; }', nginx)
            self.assertIn('if ($request_method != POST) { return 405; }', nginx)
            self.assertIn('proxy_pass http://host.docker.internal:5681;', nginx)
            self.assertIn('proxy_set_header X-Forwarded-For $remote_addr;', nginx)
            self.assertNotIn('__N8N_UPSTREAM_URL__', nginx)
            compose = json.loads((target / 'compose.local.yaml').read_text(encoding='utf-8'))
            service = compose['services']['telegram-gateway']
            self.assertEqual(service['ports'], ['127.0.0.1:5682:8080'])
            self.assertTrue(service['volumes'][0]['read_only'])
            env = (target / 'n8n-url-settings.env').read_text(encoding='utf-8')
            self.assertIn('N8N_PORT=5678', env)  # container port is independent of host 5681
            self.assertIn('N8N_PROXY_HOPS=1', env)
            self.assertEqual(json.loads((target / 'ingress.local.json').read_text(encoding='utf-8')), settings)
            self.assertEqual(len(list(target.iterdir())), 6)
        self.assertEqual(hashes, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in hashes})

    def test_public_443_requires_distinct_private_port(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t) / 'private'
            settings = self.prepare(target, webhook_url=URL.replace(':8443', ''), private_https_port=8443)
            self.assertEqual(settings['public_base_url'], 'https://example-device.tail-example.ts.net/')
            self.assertEqual(settings['private_base_url'], 'https://example-device.tail-example.ts.net:8443/')

    def test_refuses_existing_and_repository_destinations(self):
        with tempfile.TemporaryDirectory() as t:
            path = Path(t)
            sentinel = path / 'keep.txt'
            sentinel.write_text('preserve', encoding='utf-8')
            with self.assertRaises(ValueError):
                self.prepare(path)
            self.assertEqual(sentinel.read_text(encoding='utf-8'), 'preserve')
        for target in [ROOT, ROOT / 'production', ROOT.parent]:
            with self.subTest(target=target), self.assertRaises(ValueError):
                self.prepare(target)

    def test_rejects_broad_internal_test_and_injected_routes(self):
        invalid = [
            URL.replace('https:', 'http:'), URL.replace('example-device.tail-example.ts.net', 'example.org'),
            URL.replace(':8443', ':10000'), URL.replace(':8443', ':80'),
            URL.replace('/webhook/EXAMPLE_ID/webhook', '/webhook/'),
            URL.replace('/webhook/EXAMPLE_ID/webhook', '/webhook/start'),
            URL.replace('/webhook/EXAMPLE_ID/webhook', '/webhook-test/EXAMPLE_ID/webhook'),
            URL + '?token=secret', URL + '#fragment', URL.replace('https://', 'https://name:password@'),
            URL.replace('EXAMPLE_ID', 'bad;return 200;'), URL.replace('EXAMPLE_ID', '%2e%2e'),
            URL + '\n', URL.replace('EXAMPLE_ID', 'bad"'), URL.replace('EXAMPLE_ID', 'bad\\path'),
        ]
        with tempfile.TemporaryDirectory() as t:
            target = Path(t) / 'private'
            for value in invalid:
                with self.subTest(url=value), self.assertRaises(ValueError):
                    self.prepare(target, webhook_url=value)
                self.assertFalse(target.exists())

    def test_rejects_collisions_invalid_ports_and_project_names(self):
        cases = [dict(n8n_host_port=5680), dict(private_https_port=8443),
                 dict(n8n_host_port=80), dict(gateway_host_port=65536), dict(private_https_port=0),
                 dict(gateway_host_port=True), dict(n8n_host_port='5678;bad'),
                 dict(project_name='--bad'), dict(project_name='UPPER CASE')]
        with tempfile.TemporaryDirectory() as t:
            target = Path(t) / 'private'
            for case in cases:
                with self.subTest(case=case), self.assertRaises(ValueError):
                    self.prepare(target, **case)
                self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main()

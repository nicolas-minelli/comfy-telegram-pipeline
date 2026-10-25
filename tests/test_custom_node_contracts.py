"""Offline checks for the distributed examples and finalizer; no Comfy/GPU imports."""
import ast
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CustomNodeContracts(unittest.TestCase):
    def test_public_request_id_scope(self):
        source = ROOT / 'comfy/custom_nodes/n8n_job_control/__init__.py'
        tree = ast.parse(source.read_text(encoding='utf-8'))
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_valid_id')
        namespace = {'re': re}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), namespace)
        valid = namespace['_valid_id']
        self.assertTrue(valid('tg-0-1'))
        for value in ['tg-999-1', '../tg-0-1', 'tg-0-invalid', None]:
            self.assertFalse(valid(value))

    def test_generated_graphs_match_finalizer_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            output = base / 'output'
            stub = types.ModuleType('folder_paths')
            stub.get_output_directory = lambda: str(output)
            old = sys.modules.get('folder_paths')
            sys.modules['folder_paths'] = stub
            try:
                spec = importlib.util.spec_from_file_location('test_video_finalizer', ROOT / 'comfy/custom_nodes/n8n_video_finalizer/__init__.py')
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                for name in ['upscale.json', 'upscale-16x9.json']:
                    graph = json.loads((ROOT / 'comfy/api' / name).read_text(encoding='utf-8'))
                    config = graph['900']['inputs']
                    prefix = graph['17']['inputs']['filename_prefix']
                    source = output / (prefix + '_00001_.mp4')
                    source.parent.mkdir(parents=True, exist_ok=True)
                    source.write_bytes(b'fixture-video-bytes')
                    module.FINAL_DIRECTORY = base / name / 'final'
                    finalizer = module.N8NMoveFinalVideo()
                    pending = finalizer.move_final_video((True, []), config['run_id'], config['final_basename'])
                    self.assertEqual(pending['result'], ('',))
                    self.assertTrue(source.exists())
                    result = finalizer.move_final_video((True, [str(source)]), config['run_id'], config['final_basename'])
                    destination = Path(result['result'][0])
                    self.assertEqual(destination.name, config['final_basename'] + '.mp4')
                    self.assertEqual(destination.read_bytes(), b'fixture-video-bytes')
                    self.assertFalse(source.exists())
                    receipt = json.loads((destination.parent / ('.' + config['final_basename'] + '.done.json')).read_text(encoding='utf-8'))
                    self.assertEqual(receipt['run_id'], config['run_id'])
                    self.assertEqual(receipt['job_id'], config['final_basename'])
                    with self.assertRaises(ValueError):
                        finalizer.move_final_video((True, []), 'unrelated-run', config['final_basename'])
            finally:
                if old is None:
                    sys.modules.pop('folder_paths', None)
                else:
                    sys.modules['folder_paths'] = old


if __name__ == '__main__':
    unittest.main()

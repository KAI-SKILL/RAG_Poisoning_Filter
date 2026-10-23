"""Offline suite integration contracts; all GPU/setup/generation calls are mocks."""
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('offline_model_suite', HERE / 'run_model_suite.py')
suite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(suite)

GPU_IDENTITY = {'status': 'ACTUAL_CUDA_DEVICE_VERIFIED', 'gpu_name': 'MOCK NVIDIA A100',
                'memory_total_mib': 81920, 'compute_capability': '8.0', 'driver_version': '570.1'}


class SuiteIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.project = self.base / 'project'
        self.folder = self.project / 'generation/all_experiments'
        self.folder.mkdir(parents=True)
        self.inputs = self.project / 'fixture.sqlite'
        self.inputs.write_bytes(b'not a real input database; mocked generation only')
        self.protocol = self.project / 'fixture_protocol.json'
        suite.save(self.protocol, {'inputs_sqlite_sha256': suite.sha(self.inputs)})
        self.entry = {'inputs_file': 'fixture.sqlite', 'inputs_sha256': suite.sha(self.inputs),
                      'protocol_file': 'fixture_protocol.json', 'protocol_sha256': suite.sha(self.protocol),
                      'requested_rows': 1, 'source_unique_prompts': 1}
        self.registry = {'scopes': {'Q': self.entry},
                         'postanalysis_source_sha256': suite.sha(HERE / 'postanalyse_scope.py')}
        suite.save(self.folder / 'experiment_registry.json', self.registry)
        suite.PAUSE = False
        suite.ACTIVE = None

    def run_main(self, model='qwen25_3b_gguf', filesystem_error=False, partial=False):
        calls, events, exports, loaded = [], [], [], []
        output = self.project / 'generation/all_runs' / model / 'Q'
        if partial:
            output.mkdir(parents=True)
            (output / 'native_inputs.sqlite.partial-journal').write_bytes(b'interrupted mock preparation')

        def fs_guard(path):
            events.append(('filesystem', Path(path)))
            if filesystem_error:
                raise ValueError('MOCK network filesystem is rejected')
            return {'filesystem': 'MOCK local'}

        def export(source, destination):
            events.append(('export', Path(source)))
            exports.append((source, destination))
            return {'actual_unique_responses': 1, 'full_asr_ready': len(exports) > 1,
                    'archive': 'MOCK archive; no actual generation'}

        def load(path, name):
            loaded.append(Path(path))
            if name == 'suite_fs_guard':
                return SimpleNamespace(local_filesystem=fs_guard)
            if name == 'suite_exporter':
                return SimpleNamespace(export=export)
            raise AssertionError('Unexpected module load: ' + name)

        def write_complete():
            output.mkdir(parents=True, exist_ok=True)
            suite.save(output / 'run_manifest.json', {'status': 'COMPLETE'})

        def native_run(*args):
            events.append(('mock_native_generation', None))
            write_complete()
            return Path('/MOCK_PRIVATE_NATIVE_ENV/bin/python')

        def call(argv, log=None):
            argv = [str(item) for item in argv]
            calls.append(argv)
            events.append(('mock_child_command', argv))
            if '--run' in argv:
                self.assertFalse((output / 'native_inputs.sqlite.partial-journal').exists())
                write_complete()

        args = ['run_model_suite.py', '--project-root', str(self.project),
                '--model-key', model, '--scopes', 'Q', '--run']
        if partial:
            args.append('--resume')
        with mock.patch.object(sys, 'argv', args), \
             mock.patch.dict(os.environ, {'SLURM_JOB_ID': 'mock-only', 'CUDA_VISIBLE_DEVICES': '0,1', 'USER': 'mock'}, clear=True), \
             mock.patch.object(Path, 'is_relative_to', return_value=True), \
             mock.patch.object(suite, 'load', side_effect=load), \
             mock.patch.object(suite, 'call', side_effect=call), \
             mock.patch.object(suite, 'native_run', side_effect=native_run), \
             mock.patch.object(suite.signal, 'signal'), \
             contextlib.redirect_stdout(io.StringIO()):
            suite.main()
        return calls, events, exports, loaded, output

    def test_native_suite_private_scorer_new_export_and_postanalysis_interfaces(self):
        calls, events, exports, loaded, output = self.run_main()
        scorer = next(argv for argv in calls if Path(argv[1]).name == 'score_native_scope.py')
        self.assertEqual(scorer[0], '/MOCK_PRIVATE_NATIVE_ENV/bin/python')
        self.assertEqual(scorer[2:], ['--project-root', str(self.project), '--output', str(output)])
        post = next(argv for argv in calls if Path(argv[1]).name == 'postanalyse_scope.py')
        self.assertEqual(post[0], scorer[0])
        self.assertIn(HERE / 'export_scope_results.py', loaded)
        self.assertNotIn(self.project / 'generation/hf_gpu/export_hf_results.py', loaded)
        self.assertEqual(len(exports), 2)
        self.assertEqual(events[0][0], 'filesystem')
        self.assertEqual(suite.read(output.parent / 'suite_manifest.json')['status'], 'COMPLETE')

    def test_hf_suite_recovers_unfinished_preparation_before_mock_run(self):
        calls, events, exports, loaded, output = self.run_main(model='qwen3_8b', partial=True)
        run = next(argv for argv in calls if '--run' in argv)
        score = next(argv for argv in calls if '--score' in argv)
        self.assertEqual(run[0], str(self.project / 'runtime_hf_env/bin/python'))
        self.assertEqual(score[0], run[0])
        self.assertEqual(Path(run[1]), self.folder / 'run_hf_scope.py')
        self.assertEqual(events[0][0], 'filesystem')
        self.assertEqual(len(exports), 2)
        receipts = list((output / 'interrupted_preparation').glob('*/recovery_receipt.json'))
        self.assertEqual(len(receipts), 1)
        self.assertFalse(suite.read(receipts[0])['generation_response_database_existed'])

    def test_native_and_hf_share_rejecting_filesystem_guard_before_children(self):
        for model in ('qwen25_3b_gguf', 'qwen3_8b'):
            with self.subTest(model=model), self.assertRaisesRegex(ValueError, 'filesystem is rejected'):
                self.run_main(model=model, filesystem_error=True)

    def test_recovery_requires_resume_and_retains_original_bytes(self):
        output = self.base / 'recovery'
        output.mkdir()
        artifact = output / 'native_inputs.sqlite.partial'
        artifact.write_bytes(b'partial mock input')
        with self.assertRaisesRegex(ValueError, '--resume'):
            suite.recover_unfinished_preparation(output, False)
        self.assertEqual(artifact.read_bytes(), b'partial mock input')
        suite.recover_unfinished_preparation(output, True)
        retained = list((output / 'interrupted_preparation').glob('*/native_inputs.sqlite.partial'))
        self.assertEqual(len(retained), 1)
        self.assertEqual(retained[0].read_bytes(), b'partial mock input')

    def test_recovery_refuses_any_response_database(self):
        output = self.base / 'response_guard'
        output.mkdir()
        (output / 'native_inputs.sqlite.partial').write_bytes(b'partial')
        (output / 'generation_responses.sqlite').write_bytes(b'even an empty response marker forbids rebuild')
        with self.assertRaisesRegex(ValueError, 'after response storage'):
            suite.recover_unfinished_preparation(output, True)
        self.assertTrue((output / 'native_inputs.sqlite.partial').exists())
        self.assertFalse((output / 'interrupted_preparation').exists())

    def test_native_run_binds_gpu_and_calls_project_explicit_launcher(self):
        for field, name in [('tokens_file', 'tokens.sqlite'), ('token_receipt_file', 'tokens.json')]:
            source = self.project / name
            source.write_bytes(('mock ' + name).encode())
            self.entry[field] = name
            self.entry[field.replace('_file', '_sha256')] = suite.sha(source)
        output = self.base / 'native_out'
        output.mkdir()
        runtime = self.base / 'runtime'
        private = self.base / 'PRIVATE_ENV/bin/python'
        commands = []
        with mock.patch.object(suite, 'load', return_value=SimpleNamespace(get_gpu_identity=lambda: GPU_IDENTITY)), \
             mock.patch.object(suite, 'setup_native', return_value=(private, runtime / 'build', runtime / 'models')), \
             mock.patch.object(suite, 'call', side_effect=lambda argv, log=None: commands.append(argv)):
            returned = suite.native_run(SimpleNamespace(project_root=self.project, batch_size=8, threads=4),
                                        self.entry, self.inputs, self.protocol, output, runtime,
                                        {'model_key': 'qwen25_3b_gguf', 'scope': 'Q'})
        self.assertEqual(returned, private)
        command = commands[0]
        self.assertEqual(command[0], private)
        self.assertEqual(command[1], HERE / 'launch_native_gpu.py')
        self.assertEqual(command[command.index('--project-root') + 1], self.project)
        self.assertEqual(command[command.index('--gpu-layers') + 1], '99')
        self.assertEqual(suite.read(output / 'scoring_protocol.json')['native_suite_binding']['actual_gpu_evidence'], GPU_IDENTITY)
        self.assertEqual(suite.sha(self.inputs), self.entry['inputs_sha256'])
        self.assertEqual(suite.sha(self.protocol), self.entry['protocol_sha256'])

    def test_actual_private_python_scorer_wrapper_refuses_partial_result(self):
        # This child executes only stdlib imports and the incomplete-result gate.
        # The fixture has no response DB, model, server or GPU evidence.
        private = self.base / 'private_env/bin/python'
        private.parent.mkdir(parents=True)
        private.symlink_to(sys.executable)
        output = self.base / 'partial_score'
        output.mkdir()
        suite.save(output / 'scoring_protocol.json', {})
        suite.save(output / 'run_manifest.json', {'status': 'PARTIAL'})
        result = subprocess.run([str(private), str(HERE / 'score_native_scope.py'),
                                 '--project-root', str(PROJECT), '--output', str(output)],
                                capture_output=True, text=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Unfinished generation cannot be formally scored', result.stderr)
        self.assertFalse((output / 'scoring').exists())

    def test_actual_export_wrapper_and_collector_refuse_complete_label_without_data(self):
        wrapper = suite.load(HERE / 'export_scope_results.py', 'offline_actual_export_wrapper')
        collector = suite.load(HERE / 'collect_all_results.py', 'offline_actual_collector')
        source = self.base / 'fake_complete_label_only'
        source.mkdir()
        suite.save(source / 'run_manifest.json', {'status': 'COMPLETE'})
        results = self.base / 'closed_results'
        destination = results / 'qwen25_3b_gguf/Q'
        receipt = wrapper.export(source, destination, PROJECT)
        self.assertEqual(receipt['status'], 'INCOMPLETE_CHECKPOINT')
        self.assertFalse(receipt['full_asr_ready'])
        self.assertEqual(receipt['actual_unique_responses'], 0)
        self.assertEqual(receipt['additional_scope_validation']['status'], 'INCOMPLETE_CHECKPOINT')
        self.assertIn('INCOMPLETE_Checkpoint.zip', receipt['archive'])
        self.assertFalse(list(results.rglob('*COMPLETE_Results.zip')))
        inventory = collector.collect(PROJECT, results)
        self.assertEqual(inventory['status'], 'INCOMPLETE')
        self.assertEqual(inventory['required_slots'], 12)
        self.assertEqual(inventory['complete_slots'], 0)
        self.assertFalse(inventory['full_project_generation_and_analysis_ready'])
        self.assertEqual(inventory['model_calls'], 0)
        self.assertEqual(inventory['network_calls'], 0)
        slot = next(row for row in inventory['slots'] if row['model_key'] == 'qwen25_3b_gguf' and row['scope'] == 'Q')
        self.assertNotEqual(slot['status'], 'COMPLETE')
        self.assertTrue(slot['export_inventory_verified'])

    def test_actual_export_wrapper_rejects_unregistered_slot_path(self):
        wrapper = suite.load(HERE / 'export_scope_results.py', 'offline_actual_export_bad_slot')
        with self.assertRaisesRegex(ValueError, 'registered model_key/scope'):
            wrapper.export(self.base, self.base / 'results/unknown/Q', PROJECT)


if __name__ == '__main__':
    unittest.main(verbosity=2)

"""Mock-only CUDA launcher contract tests. No model, GPU or network is used."""
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
import importlib.util
import json
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('tested_native_gpu_launcher', HERE / 'launch_native_gpu.py')
gpu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gpu)

IDENTITY = {'status': 'ACTUAL_CUDA_DEVICE_VERIFIED', 'gpu_name': 'NVIDIA A100-SXM4-80GB',
            'memory_total_mib': 81920, 'compute_capability': '8.0', 'driver_version': '570.133.20'}
ENV = {'SLURM_JOB_ID': 'mock-job-1', 'CUDA_VISIBLE_DEVICES': '3,5'}
CUDA_LOG = (b'ggml_cuda_init: found 1 CUDA devices (Total VRAM: 81920 MiB):\n'
            b'  Device 0: NVIDIA A100-SXM4-80GB, compute capability 8.0, VMM: yes, VRAM: 81920 MiB\n'
            b'llama_model_load_from_file_impl: using device CUDA0 (NVIDIA A100-SXM4-80GB) (0000:00:00.0) - 81000 MiB free\n'
            b'load_tensors: offloaded 37/37 layers to GPU\n')


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'layout'
        self.project = self.base / 'project'
        (self.root / 'generation/input').mkdir(parents=True)
        (self.project / 'code/generation').mkdir(parents=True)
        (self.project / 'code/generation/run_native_generation.py').write_text('# mock original runner\n')
        self.protocol = self.root / 'generation/scoring_protocol_frozen.json'
        self.protocol.write_text(json.dumps({'native_suite_binding': {'actual_gpu_evidence': IDENTITY}}))
        self.server = self.base / 'llama-server'
        self.server.write_text('mock-server')
        self.model = self.base / 'model.gguf'
        self.model.write_text('mock-weights')
        (self.base / 'manifest.json').write_text(json.dumps({'files': [{'file': self.model.name, 'sha256': gpu.digest(self.model)}]}))
        self.build = self.base / 'build_receipt.json'
        self.build.write_text(json.dumps({'mode': 'CUDA', 'artifacts': [{'path': self.server.name, 'sha256': gpu.digest(self.server)}]}))
        self.output = self.base / 'output'
        self.args = SimpleNamespace(root=self.root, project_root=self.project, output=self.output,
                                    server=self.server, model=self.model, build_manifest=self.build,
                                    batch_size=8, threads=4, gpu_layers=99, port=18080)
        self.generated = []

    def simulate(self, log=CUDA_LOG, job='mock-job-1', dead=False):
        owner = self

        class Server:
            returncode = 1 if dead else None

            def __init__(self, command, stdout, stderr, env):
                self.command = command
                owner.assertEqual(command[command.index('-ngl') + 1], '99')
                owner.assertEqual(env['CUDA_VISIBLE_DEVICES'], '3')
                owner.assertEqual(env['NO_PROXY'], 'localhost,127.0.0.1,::1')
                stdout.write(log)

            def poll(self):
                return self.returncode

            def terminate(self):
                self.returncode = 0

            def wait(self, timeout=None):
                return self.returncode

            def kill(self):
                self.returncode = -9

        def run(command, **kwargs):
            if command[0] == 'nvidia-smi':
                owner.assertEqual(command[2], '3')
                return SimpleNamespace(stdout='NVIDIA A100-SXM4-80GB, 81920, 8.0, 570.133.20\n', returncode=0)
            evidence = gpu.read(owner.output / 'native_gpu_execution.json')
            owner.assertEqual(evidence['status'], 'ACTUAL_CUDA_FULL_OFFLOAD_VERIFIED')
            owner.assertEqual(Path(command[1]), owner.project / 'code/generation/run_native_generation.py')
            owner.assertTrue((owner.output / evidence['sessions'][-1]['excerpt_file']).is_file())
            owner.generated.append(command)
            return SimpleNamespace(returncode=0)

        response = mock.MagicMock()
        response.__enter__.return_value.status = 200
        opener = mock.Mock()
        opener.open.return_value = response
        with mock.patch.dict(gpu.os.environ, {**ENV, 'SLURM_JOB_ID': job}, clear=True), \
             mock.patch.object(gpu.subprocess, 'run', side_effect=run), \
             mock.patch.object(gpu.subprocess, 'Popen', Server), \
             mock.patch.object(gpu.urllib.request, 'build_opener', return_value=opener), \
             mock.patch.object(gpu, 'port_unused'):
            gpu.run(self.args)

    def test_query_identity_excludes_observations_and_selects_first_device(self):
        runner = mock.Mock(return_value=SimpleNamespace(stdout='NVIDIA A100-SXM4-80GB, 81920, 8.0, 570.133.20\n'))
        one, obs = gpu.query_gpu(ENV, runner)
        two, _ = gpu.query_gpu({**ENV, 'SLURM_JOB_ID': 'new-job'}, runner)
        self.assertEqual(one, IDENTITY)
        self.assertEqual(one, two)
        self.assertNotIn('slurm_job_id', one)
        self.assertEqual(obs['slurm_job_id'], 'mock-job-1')
        self.assertEqual(runner.call_args.args[0][2], '3')

    def test_requires_slurm(self):
        with self.assertRaisesRegex(ValueError, 'Slurm allocation'):
            gpu.query_gpu({'CUDA_VISIBLE_DEVICES': '0'}, mock.Mock())

    def test_requires_allocated_device(self):
        for value in ('', '-1', 'None', 'NoDevFiles', 'void'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                gpu.query_gpu({'SLURM_JOB_ID': '1', 'CUDA_VISIBLE_DEVICES': value}, mock.Mock())

    def test_device_selector_not_shell_text(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            gpu.slurm_selector({'SLURM_JOB_ID': '1', 'CUDA_VISIBLE_DEVICES': '0; echo malicious'})

    def test_public_identity_api_rejects_invalid_visibility_without_query(self):
        for value in ('', ',0', '  ,1', 'none,0', '0;echo invalid', '0 1', 'MIG-', '-2'):
            with self.subTest(value=value), \
                 mock.patch.dict(gpu.os.environ, {'SLURM_JOB_ID': 'mock', 'CUDA_VISIBLE_DEVICES': value}, clear=True), \
                 mock.patch.object(gpu.subprocess, 'run') as command, self.assertRaises(ValueError):
                gpu.get_gpu_identity()
            command.assert_not_called()

    def test_query_rejects_ambiguous_or_unavailable_fields(self):
        for value in ('a, 1, 8.0, 570.1\nb, 1, 8.0, 570.1', 'a, N/A, 8.0, 570.1', 'a, 1, N/A, 570.1'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                gpu.query_gpu(ENV, mock.Mock(return_value=SimpleNamespace(stdout=value)))

    def test_valid_cuda_full_offload(self):
        proof, excerpt = gpu.verify_new_log(CUDA_LOG, IDENTITY)
        self.assertEqual(proof['offloaded_layers'], 37)
        self.assertEqual(proof['total_layers'], 37)
        self.assertIn('using device CUDA0', excerpt)

    def test_cpu_metal_and_partial_logs_rejected(self):
        variants = [b'load_tensors: offloaded 37/37 layers to GPU\n',
                    CUDA_LOG.replace(b'found 1 CUDA devices', b'found 1 Metal devices'),
                    CUDA_LOG.replace(b'found 1 CUDA devices', b'found 2 CUDA devices'),
                    CUDA_LOG.replace(b'37/37', b'36/37'),
                    CUDA_LOG.replace(b'37/37', b'0/0'),
                    CUDA_LOG.replace(b'using device CUDA0', b'using device CPU'),
                    CUDA_LOG.replace(b'compute capability 8.0', b'compute capability 9.0')]
        for value in variants:
            with self.subTest(value=value), self.assertRaises(ValueError):
                gpu.verify_new_log(value, IDENTITY)

    def test_same_session_evidence_precedes_original_runner(self):
        self.simulate()
        self.assertEqual(len(self.generated), 1)
        session = gpu.read(self.output / 'native_gpu_execution.json')['sessions'][0]
        self.assertTrue(session['generation_started'])
        self.assertEqual(session['generator_returncode'], 0)
        self.assertEqual(session['log_start_offset'], 0)
        self.assertEqual(session['startup_log_sha256'], gpu.digest(self.output / session['startup_log_file']))
        launch = gpu.read(self.output / 'server_launch.json')
        self.assertIn(launch['actual_cuda_binding_sha256'], launch['transport'])
        self.assertEqual(launch['actual_gpu_identity'], IDENTITY)

    def test_old_gpu_log_cannot_prove_new_cpu_session(self):
        self.output.mkdir()
        (self.output / 'native_server.log').write_bytes(CUDA_LOG)
        with self.assertRaisesRegex(ValueError, 'does not initialize a CUDA'):
            self.simulate(b'CPU backend ready\n')
        self.assertEqual(self.generated, [])
        evidence = gpu.read(self.output / 'native_gpu_execution.json')
        self.assertEqual(evidence['status'], 'CUDA_VERIFICATION_FAILED_NO_GENERATION')
        session = evidence['sessions'][0]
        self.assertEqual(session['log_start_offset'], len(CUDA_LOG))
        self.assertEqual((self.output / session['startup_log_file']).read_bytes(), b'CPU backend ready\n')

    def test_two_sessions_append_offsets_and_job_ids_do_not_change_launch(self):
        self.simulate(job='mock-job-1')
        launch_sha = gpu.digest(self.output / 'server_launch.json')
        self.simulate(job='mock-job-2')
        self.assertEqual(gpu.digest(self.output / 'server_launch.json'), launch_sha)
        evidence = gpu.read(self.output / 'native_gpu_execution.json')
        self.assertEqual(len(evidence['sessions']), 2)
        self.assertEqual(evidence['sessions'][1]['log_start_offset'], len(CUDA_LOG))
        self.assertNotEqual(evidence['sessions'][0]['session_id'], evidence['sessions'][1]['session_id'])
        device = gpu.read(self.output / 'actual_gpu_evidence.json')
        self.assertEqual([x['slurm_job_id'] for x in device['observations']], ['mock-job-1', 'mock-job-2'])

    def test_changed_identity_on_resume_rejected(self):
        self.simulate()
        data = gpu.read(self.output / 'actual_gpu_evidence.json')
        data['identity']['driver_version'] = '999.0'
        gpu.save(self.output / 'actual_gpu_evidence.json', data)
        with self.assertRaisesRegex(ValueError, 'changed'):
            self.simulate(job='mock-job-2')
        self.assertEqual(len(self.generated), 1)

    def test_protocol_device_mismatch_rejected_before_server(self):
        self.protocol.write_text(json.dumps({'native_suite_binding': {}}))
        with self.assertRaisesRegex(ValueError, 'protocol does not bind'):
            self.simulate()
        self.assertEqual(self.generated, [])

    def test_gpu_layer_zero_rejected_without_query_or_model(self):
        self.args.gpu_layers = 0
        with mock.patch.object(gpu, 'query_gpu') as query, self.assertRaisesRegex(ValueError, 'CPU fallback'):
            gpu.run(self.args)
        query.assert_not_called()

    def test_cpu_build_rejected(self):
        build = gpu.read(self.build)
        build['mode'] = 'CPU'
        gpu.save(self.build, build)
        with self.assertRaisesRegex(ValueError, 'CUDA build'):
            self.simulate()
        self.assertEqual(self.generated, [])

    def test_model_and_server_artifacts_are_hash_checked(self):
        for path in (self.server, self.model):
            original = path.read_bytes()
            path.write_bytes(b'changed')
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.simulate()
            path.write_bytes(original)
        self.assertEqual(self.generated, [])

    def test_dead_server_never_starts_generation(self):
        with self.assertRaisesRegex(ValueError, 'exited before readiness'):
            self.simulate(dead=True)
        self.assertEqual(self.generated, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)

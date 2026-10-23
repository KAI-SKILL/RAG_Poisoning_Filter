"""Launch the frozen native generator only after same-session CUDA verification.

This adapter does not change the original generator. Slurm/device observations
are kept outside resume identity; the fixed device identity and verification
rules are bound through both the scope protocol and the runner's transport field.
No CPU fallback is available. Tests for this module use mocks, never a GPU.
"""
from pathlib import Path
import argparse
import csv
import datetime
import fcntl
import hashlib
import io
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request
import uuid

SCHEMA = 'group9-native-cuda-evidence-v1'
VERIFICATION_CONFIG = {
    'schema_version': SCHEMA,
    'required_backend': 'CUDA',
    'required_gpu_layers_argument': 99,
    'device_selector': 'first CUDA_VISIBLE_DEVICES entry; server sees this entry only',
    'device_query': 'nvidia-smi --query-gpu=name,memory.total,compute_cap,driver_version --format=csv,noheader,nounits',
    'required_log_proof': 'same-session CUDA initialization, matching CUDA0 model device and compute capability, positive N/N GPU layer offload',
    'log_scope': 'only bytes appended after this session start offset and before generation',
    'cpu_fallback_allowed': False,
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def stable(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.partial')
    with temporary.open('w') as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def read(path):
    return json.loads(Path(path).read_text())


def slurm_selector(environment=None):
    env = os.environ if environment is None else environment
    require(bool(env.get('SLURM_JOB_ID', '').strip()),
            'A Slurm allocation is required; do not run compute in an SSH shell')
    visible = env.get('CUDA_VISIBLE_DEVICES', '')
    selector = visible.split(',')[0].strip()
    require(selector and selector.lower() not in {'-1', 'none', 'nodevfiles', 'void'},
            'Slurm must allocate a CUDA device in CUDA_VISIBLE_DEVICES')
    # Accept NVIDIA's numeric, GPU UUID and MIG selectors; never shell-evaluate it.
    require(bool(re.fullmatch(r'(?:[0-9]+|GPU-[A-Za-z0-9-]+|MIG-[A-Za-z0-9/.-]+)', selector)),
            'Unsupported CUDA_VISIBLE_DEVICES selector')
    return selector


def query_gpu(environment=None, run=None):
    """Return stable identity plus observational query evidence (no model load)."""
    env = dict(os.environ if environment is None else environment)
    selector = slurm_selector(env)
    run = subprocess.run if run is None else run
    command = ['nvidia-smi', '-i', selector,
               '--query-gpu=name,memory.total,compute_cap,driver_version',
               '--format=csv,noheader,nounits']
    result = run(command, check=True, capture_output=True, text=True,
                 timeout=30, env=env)
    rows = list(csv.reader(io.StringIO(result.stdout.strip())))
    require(len(rows) == 1 and len(rows[0]) == 4,
            'nvidia-smi must report exactly the selected device and four fields')
    name, memory, capability, driver = [part.strip() for part in rows[0]]
    require(name and re.fullmatch(r'[0-9]+', memory) and int(memory) > 0,
            'nvidia-smi returned an invalid device name or memory capacity')
    require(bool(re.fullmatch(r'[0-9]+\.[0-9]+', capability)),
            'nvidia-smi did not report a numeric CUDA compute capability')
    require(bool(re.fullmatch(r'[0-9]+(?:\.[0-9]+)+', driver)),
            'nvidia-smi did not report a numeric NVIDIA driver version')
    identity = {'status': 'ACTUAL_CUDA_DEVICE_VERIFIED', 'gpu_name': name,
                'memory_total_mib': int(memory), 'compute_capability': capability,
                'driver_version': driver}
    observation = {'observed_utc': now(), 'hostname': socket.gethostname(),
                   'slurm_job_id': env['SLURM_JOB_ID'],
                   'slurm_step_id': env.get('SLURM_STEP_ID'),
                   'nvidia_smi_argv': command,
                   'nvidia_smi_stdout_sha256': hashlib.sha256(result.stdout.encode()).hexdigest(),
                   'nvidia_smi_stdout': result.stdout,
                   'note': 'Job ID, device selector and time are observations, never resume identity.'}
    return identity, observation


def get_gpu_identity():
    """Importable by run_model_suite: query the actual allocated CUDA device."""
    return query_gpu()[0]


def binding(identity):
    value = {'actual_gpu_identity': identity,
             'verification_config': VERIFICATION_CONFIG}
    return {**value, 'sha256': hashlib.sha256(stable(value).encode()).hexdigest()}


def verify_protocol(path, identity):
    protocol = read(path)
    require(protocol.get('native_suite_binding', {}).get('actual_gpu_evidence') == identity,
            'Frozen runtime protocol does not bind this actual CUDA device identity')


def record_device_evidence(output, identity, observation):
    path = Path(output) / 'actual_gpu_evidence.json'
    if path.exists():
        data = read(path)
        require(data.get('schema_version') == SCHEMA and data.get('identity') == identity
                and data.get('verification_config') == VERIFICATION_CONFIG,
                'Actual CUDA device or verification rules changed; use a fresh run branch')
    else:
        data = {'schema_version': SCHEMA, 'identity': identity,
                'verification_config': VERIFICATION_CONFIG, 'observations': []}
    data['observations'].append(observation)
    save(path, data)


def verify_new_log(log_bytes, identity):
    """Accept only pinned llama.cpp CUDA proof inside the supplied new bytes."""
    text = log_bytes.decode('utf-8', errors='replace')
    lines = text.splitlines()
    initialized = [line for line in lines if re.search(
        r'ggml_cuda_init:\s+found\s+1\s+CUDA devices?', line)]
    require(bool(initialized), 'New server log does not initialize a CUDA device')
    devices = []
    for line in lines:
        match = re.search(r'Device\s+0:\s+(.+?),\s*compute capability\s+([0-9]+\.[0-9]+)', line)
        if match and match.group(1).strip() == identity['gpu_name'] and match.group(2) == identity['compute_capability']:
            devices.append(line)
    require(bool(devices), 'New server log CUDA0 name/compute capability differs from nvidia-smi')
    used = [line for line in lines if re.search(r'using device\s+CUDA0\s+\(', line)
            and ('(' + identity['gpu_name'] + ')') in line]
    require(bool(used), 'New server log does not place the model on the selected CUDA0 device')
    offloads = []
    for line in lines:
        match = re.search(r'offloaded\s+([0-9]+)\s*/\s*([0-9]+)\s+layers\s+to\s+GPU', line)
        if match:
            offloads.append((int(match.group(1)), int(match.group(2)), line))
    require(bool(offloads), 'New server log contains no model GPU layer offload proof')
    require(all(done == total and total > 0 for done, total, _ in offloads),
            'Native model is not fully offloaded to CUDA: require positive N/N layers')
    excerpt = '\n'.join(initialized + devices + used + [x[2] for x in offloads]) + '\n'
    return {'status': 'ACTUAL_CUDA_FULL_OFFLOAD_VERIFIED',
            'cuda_device': 'CUDA0', 'gpu_name': identity['gpu_name'],
            'compute_capability': identity['compute_capability'],
            'offloaded_layers': offloads[-1][0], 'total_layers': offloads[-1][1],
            'all_model_layers_offloaded': True, 'cpu_fallback_allowed': False}, excerpt


def log_slice(path, start):
    with Path(path).open('rb') as stream:
        stream.seek(0, os.SEEK_END)
        end = stream.tell()
        require(end >= start, 'Native server log was truncated during this session')
        stream.seek(start)
        data = stream.read(end - start)
    return data, end


def append_execution(output, identity, session):
    path = Path(output) / 'native_gpu_execution.json'
    if path.exists():
        data = read(path)
        require(data.get('schema_version') == SCHEMA and data.get('identity') == identity
                and data.get('verification_config') == VERIFICATION_CONFIG,
                'Native execution evidence belongs to another device or verifier')
    else:
        data = {'schema_version': SCHEMA, 'identity': identity,
                'verification_config': VERIFICATION_CONFIG, 'sessions': []}
    data['sessions'].append(session)
    data['status'] = session['status']
    save(path, data)


def port_unused(port):
    try:
        connection = socket.create_connection(('127.0.0.1', port), timeout=1)
    except OSError:
        return
    connection.close()
    raise ValueError('Requested loopback server port is already in use')


def run(a):
    require(a.gpu_layers == 99, 'Only --gpu-layers 99 is supported; CPU fallback is forbidden')
    require(a.batch_size > 0 and a.threads > 0 and 0 < a.port < 65536,
            'Batch size, threads and server port must be positive and valid')
    root = a.root.resolve()
    project = a.project_root.resolve()
    output = (a.output or root / 'generation/run').resolve()
    protocol = root / 'generation/scoring_protocol_frozen.json'
    runner = project / 'code/generation/run_native_generation.py'
    require(runner.is_file(), 'Original generator is missing under --project-root')
    identity, observation = query_gpu()
    verify_protocol(protocol, identity)
    build = read(a.build_manifest)
    require(build.get('mode') == 'CUDA', 'A recorded CUDA build is required')
    for artifact in build['artifacts']:
        actual = a.build_manifest.parent / artifact['path']
        require(digest(actual) == artifact['sha256'], 'Native artifact hash differs: ' + artifact['path'])
    model_manifest = read(a.model.parent / 'manifest.json')
    expected = next(x['sha256'] for x in model_manifest['files'] if x['file'] == a.model.name)
    require(digest(a.model) == expected, 'Model weights differ from the pinned manifest')
    output.mkdir(parents=True, exist_ok=True)
    with (output / '.native_gpu_launcher.lock').open('a') as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError('Another native GPU launcher owns this output') from error
        session_id = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:8]
        observation['session_id'] = session_id
        record_device_evidence(output, identity, observation)
        fixed_binding = binding(identity)
        cmd = [str(a.server.resolve()), '-m', str(a.model.resolve()),
               '--alias', 'group9-qwen3b', '--host', '127.0.0.1', '--port', str(a.port),
               '-t', str(a.threads), '-tb', str(a.threads), '-np', str(a.batch_size),
               '-c', str(a.batch_size * 4096), '--no-kv-unified', '-fa', 'on',
               '-b', '1024', '-ub', '128', '-ngl', '99', '--cache-ram', '0',
               '--no-context-shift', '--fit', 'off', '--no-webui']
        launch = {'server_argv': cmd, 'launcher_sha256': digest(__file__),
                  'native_server_sha256': digest(a.server),
                  'transport': 'Loopback HTTP; server and client children of one parent process; actual_cuda_binding_sha256=' + fixed_binding['sha256'],
                  'output': str(output), 'actual_gpu_identity': identity,
                  'native_gpu_verification': VERIFICATION_CONFIG,
                  'actual_cuda_binding_sha256': fixed_binding['sha256'],
                  'original_runner_sha256': digest(runner)}
        launch_file = output / 'server_launch.json'
        if launch_file.exists():
            require(read(launch_file) == launch, 'Refusing changed server launch configuration')
        else:
            save(launch_file, launch)
        port_unused(a.port)
        session_dir = output / 'native_gpu_sessions' / session_id
        session_dir.mkdir(parents=True)
        log_path = output / 'native_server.log'
        # Capture and persist the offset before Popen. Prior sessions cannot prove this one.
        start = log_path.stat().st_size if log_path.exists() else 0
        session = {**observation, 'status': 'SERVER_SESSION_STARTING',
                   'log_file': 'native_server.log', 'log_start_offset': start,
                   'generation_started': False, 'actual_cuda_binding_sha256': fixed_binding['sha256']}
        session_file = session_dir / 'session.json'
        save(session_file, session)
        environment = dict(os.environ)
        environment['CUDA_VISIBLE_DEVICES'] = slurm_selector(environment)
        environment['NO_PROXY'] = 'localhost,127.0.0.1,::1'
        environment['no_proxy'] = environment['NO_PROXY']
        # Cluster package proxies must never handle model prompt traffic.
        health_client = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        server = None
        try:
            with log_path.open('ab', buffering=0) as log:
                server = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=environment)
                url = 'http://127.0.0.1:' + str(a.port)
                for _ in range(240):
                    require(server.poll() is None, 'Native CUDA server exited before readiness')
                    try:
                        with health_client.open(url + '/health', timeout=1) as response:
                            if response.status == 200:
                                break
                    except Exception:
                        time.sleep(.5)
                else:
                    raise RuntimeError('Native CUDA server not ready')
                require(server.poll() is None, 'Native CUDA server exited after readiness')
                new_bytes, end = log_slice(log_path, start)
                raw_path = session_dir / 'startup_log.txt'
                raw_path.write_bytes(new_bytes)
                session.update(log_end_offset=end,
                               startup_log_file=str(raw_path.relative_to(output)),
                               startup_log_sha256=digest(raw_path))
                proof, excerpt = verify_new_log(new_bytes, identity)
                excerpt_path = session_dir / 'cuda_excerpt.txt'
                excerpt_path.write_text(excerpt)
                session.update(proof)
                session.update(verified_utc=now(), excerpt_file=str(excerpt_path.relative_to(output)),
                               excerpt_sha256=digest(excerpt_path))
                save(session_file, session)
                # Commit GPU proof before invoking the unchanged response writer.
                append_execution(output, identity, session.copy())
                verify_protocol(protocol, identity)
                command = [sys.executable, str(runner), '--input', str(root / 'generation/input/generation_inputs.sqlite'),
                           '--tokens', str(root / 'generation/input/token_counts.sqlite'), '--output', str(output),
                           '--model-manifest', str(a.model.parent / 'manifest.json'),
                           '--server-build', str(a.build_manifest.resolve()), '--server-launch', str(launch_file),
                           '--protocol', str(protocol), '--server-url', url, '--batch-size', str(a.batch_size)]
                session['generation_started'] = True
                save(session_file, session)
                result = subprocess.run(command, env=environment)
                session.update(generator_returncode=result.returncode, generator_finished_utc=now())
                save(session_file, session)
                if result.returncode:
                    raise RuntimeError('Original generation runner exited ' + str(result.returncode))
        except BaseException as error:
            session.update(failure_type=type(error).__name__, failure_message=str(error), failed_utc=now())
            if not session.get('all_model_layers_offloaded'):
                session['status'] = 'CUDA_VERIFICATION_FAILED_NO_GENERATION'
                if log_path.exists():
                    new_bytes, end = log_slice(log_path, start)
                    raw_path = session_dir / 'startup_log.txt'
                    raw_path.write_bytes(new_bytes)
                    session.update(log_end_offset=end, startup_log_file=str(raw_path.relative_to(output)),
                                   startup_log_sha256=digest(raw_path))
                append_execution(output, identity, session.copy())
            save(session_file, session)
            raise
        finally:
            if server is not None:
                if server.poll() is None:
                    server.terminate()
                try:
                    server.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait()
            session['server_finished_utc'] = now()
            save(session_file, session)
            # The ledger's session is updated, preserving earlier verified sessions.
            evidence_path = output / 'native_gpu_execution.json'
            if evidence_path.exists():
                evidence = read(evidence_path)
                for index, item in enumerate(evidence['sessions']):
                    if item['session_id'] == session_id:
                        evidence['sessions'][index] = session
                        break
                evidence['status'] = session['status']
                save(evidence_path, evidence)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True, help='Per-scope input/protocol layout root')
    parser.add_argument('--project-root', type=Path, required=True, help='Project containing the unchanged core runner')
    parser.add_argument('--server', type=Path, required=True)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--build-manifest', type=Path, required=True)
    parser.add_argument('--batch-size', type=int, default=8)
    parser.add_argument('--threads', type=int, default=8)
    parser.add_argument('--gpu-layers', type=int, default=99, choices=[99])
    parser.add_argument('--port', type=int, default=18080)
    parser.add_argument('--output', type=Path)
    run(parser.parse_args())


if __name__ == '__main__':
    main()

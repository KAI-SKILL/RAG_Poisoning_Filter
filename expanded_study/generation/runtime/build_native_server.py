"""Rebuild the fixed native server on Linux; CPU default, optional CUDA build.

This script builds runtime software only and never loads or downloads a model.
Use --dry-run to print the complete plan without network, installs or writes.
"""
from pathlib import Path
import argparse, hashlib, json, os, re, shutil, subprocess, sys, tarfile, urllib.request

HERE = Path(__file__).resolve().parent
REVISION = '0c1e57098bba43ac29e6e3b677cdceebdd22334f'
TOOL_VERSIONS = {'cmake': '4.4.4', 'ninja': '1.13.2'}
CPU_FLAGS = [
    '-DCMAKE_BUILD_TYPE=Release', '-DGGML_NATIVE=ON', '-DGGML_CUDA=OFF',
    '-DGGML_VULKAN=OFF', '-DGGML_BLAS=OFF', '-DGGML_OPENMP=ON',
    '-DLLAMA_BUILD_TESTS=OFF', '-DLLAMA_BUILD_EXAMPLES=OFF',
    '-DLLAMA_BUILD_TOOLS=ON', '-DLLAMA_BUILD_SERVER=ON',
    '-DLLAMA_CURL=OFF', '-DLLAMA_OPENSSL=OFF', '-DLLAMA_USE_PREBUILT_UI=OFF',
]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workdir', type=Path, default=HERE / 'build_workspace',
                   help='Separate runtime build folder; use another folder for CUDA.')
    p.add_argument('--jobs', type=int, default=4, help='Parallel compiler jobs.')
    p.add_argument('--cuda', action='store_true', help='Enable the CUDA backend; requires a working CUDA toolkit/compiler.')
    p.add_argument('--cuda-architectures', default='auto',
                   help='auto leaves the pinned upstream default; native uses visible GPU(s); or CMake list such as 75;86.')
    p.add_argument('--dry-run', action='store_true', help='Print plan without network, subprocesses, installs or filesystem mutation.')
    a = p.parse_args()
    if a.jobs < 1:
        p.error('--jobs must be positive')
    if a.cuda_architectures != 'auto' and not a.cuda:
        p.error('--cuda-architectures requires --cuda')
    if not re.fullmatch(r'auto|native|[0-9]+[af]?(?:-(?:real|virtual))?(?:;[0-9]+[af]?(?:-(?:real|virtual))?)*', a.cuda_architectures):
        p.error('Invalid CMake CUDA architecture list')
    return a


def make_plan(a):
    identity = json.loads((HERE / 'source_identity.json').read_text())
    if identity['vendor_llama_cpp_commit'] != REVISION:
        raise SystemExit('Unexpected frozen llama.cpp revision')
    root = a.workdir.resolve()
    source = root / 'source' / ('llama.cpp-' + REVISION)
    tools = root / 'build_tools'
    cmake = tools / 'cmake/data/bin/cmake'
    ninja = tools / 'bin/ninja'
    flags = list(CPU_FLAGS)
    if a.cuda:
        flags[flags.index('-DGGML_CUDA=OFF')] = '-DGGML_CUDA=ON'
        if a.cuda_architectures != 'auto':
            flags.append('-DCMAKE_CUDA_ARCHITECTURES=' + a.cuda_architectures)
    commands = {
        'install_tools_if_missing': [sys.executable, '-m', 'pip', 'install', '--target', str(tools),
                                     'cmake==' + TOOL_VERSIONS['cmake'], 'ninja==' + TOOL_VERSIONS['ninja']],
        'configure': [str(cmake), '-S', str(source), '-B', str(root / 'build'), '-G', 'Ninja',
                      '-DCMAKE_MAKE_PROGRAM=' + str(ninja), *flags],
        'build': [str(cmake), '--build', str(root / 'build'), '--target', 'llama-server', '-j', str(a.jobs)],
        'version': [str(root / 'build/bin/llama-server'), '--version'],
    }
    return {
        'mode': 'CUDA' if a.cuda else 'CPU', 'workdir': str(root),
        'source_revision': REVISION, 'source_archive_url': identity['source_url'],
        'source_archive_sha256': identity['archive_sha256'],
        'archive': str(root / 'llama_source.tar.gz'), 'source': str(source),
        'server': str(root / 'build/bin/llama-server'),
        'cuda_architectures': a.cuda_architectures if a.cuda else None,
        'tool_versions': TOOL_VERSIONS, 'commands': commands,
        'model_downloads': 0, 'model_loads': 0, 'generation_calls': 0,
        'recorded_pre_delivery_gpu_validation': 'not_executed',
    }


def download_archive(plan):
    path = Path(plan['archive'])
    if not path.exists():
        partial = path.with_suffix(path.suffix + '.partial')
        with urllib.request.urlopen(plan['source_archive_url'], timeout=60) as src, partial.open('wb') as out:
            for block in iter(lambda: src.read(1024 * 1024), b''):
                out.write(block)
            out.flush()
            os.fsync(out.fileno())
        if digest(partial) != plan['source_archive_sha256']:
            raise SystemExit('Downloaded source archive SHA-256 differs from frozen identity')
        os.replace(partial, path)
    if digest(path) != plan['source_archive_sha256']:
        raise SystemExit('Pinned source archive SHA-256 mismatch; use an empty workdir')
    return path


def main():
    a = parse_args()
    plan = make_plan(a)
    if a.dry_run:
        print(json.dumps({'status': 'DRY_RUN_NO_NETWORK_OR_WRITES', **plan}, indent=2))
        return
    if sys.platform != 'linux':
        raise SystemExit('This helper targets Linux CPU/CUDA hosts, including Linux notebook runtimes.')
    for program in ['g++', 'gcc']:
        if not shutil.which(program):
            raise SystemExit('Required compiler missing: ' + program)
    if a.cuda and not shutil.which('nvcc'):
        raise SystemExit('CUDA compiler nvcc was not found. Install a compatible CUDA toolkit or use a GPU runtime that supplies it.')
    root = Path(plan['workdir'])
    root.mkdir(parents=True, exist_ok=True)
    archive = download_archive(plan)
    source = Path(plan['source'])
    if not source.exists():
        with tarfile.open(archive) as t:
            t.extractall(root / 'source', filter='data')
    cmake = Path(plan['commands']['configure'][0])
    ninja = root / 'build_tools/bin/ninja'
    if not cmake.exists() or not ninja.exists():
        subprocess.run(plan['commands']['install_tools_if_missing'], check=True)
    subprocess.run(plan['commands']['configure'], check=True)
    subprocess.run(plan['commands']['build'], check=True)
    result = subprocess.run(plan['commands']['version'], capture_output=True, text=True, check=True)
    files = [Path(plan['server']), *sorted((root / 'build/bin').glob('*.so*'))]
    unique = {}
    for path in files:
        unique.setdefault(str(path.resolve()), {'path': str(path.relative_to(root)), 'bytes': path.stat().st_size,
                                                'sha256': digest(path)})
    receipt = {'status': 'RUNTIME_BUILT_NO_MODEL_EXECUTION', **plan,
               'cuda_backend_compiled': bool(a.cuda), 'gpu_generation_executed': False,
               'version_output': result.stdout + result.stderr, 'artifacts': list(unique.values()),
               'scope': 'Software compilation and --version only; no benchmark, model loading, generation or GPU throughput measurement.'}
    (root / 'build_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'status': receipt['status'], 'server': plan['server'],
                      'receipt': str(root / 'build_receipt.json')}, indent=2))


if __name__ == '__main__':
    main()

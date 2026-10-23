"""Download the frozen Qwen GGUF, README and license; verify every saved byte.

The --dry-run mode never contacts the network or changes files. This helper
never loads a model or performs generation. Existing verified files are reused.
"""
from pathlib import Path
import argparse, hashlib, json, os, urllib.request

HERE = Path(__file__).resolve().parent
EXPECTED_REPOSITORY = 'Qwen/Qwen2.5-3B-Instruct-GGUF'
EXPECTED_REVISION = '7dabda4d13d513e3e842b20f0d435c732f172cbe'
WEIGHTS = 'qwen2.5-3b-instruct-q4_k_m.gguf'
WEIGHT_SHA256 = '626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def verified(path, row):
    return path.is_file() and path.stat().st_size == row['bytes'] and digest(path) == row['sha256']


def frozen_manifest(path):
    manifest = json.loads(path.read_text())
    if manifest['repository'] != EXPECTED_REPOSITORY or manifest['revision'] != EXPECTED_REVISION:
        raise SystemExit('Model manifest repository/revision is not the frozen generator')
    names = set()
    for row in manifest['files']:
        name = row['file']
        if Path(name).name != name or name in names:
            raise SystemExit('Unsafe or duplicate model filename')
        names.add(name)
        expected_url = f'https://huggingface.co/{EXPECTED_REPOSITORY}/resolve/{EXPECTED_REVISION}/{name}'
        if row['url'] != expected_url or row['bytes'] <= 0:
            raise SystemExit('Unexpected pinned model URL/size')
    weights = next(row for row in manifest['files'] if row['file'] == WEIGHTS)
    if weights['sha256'] != WEIGHT_SHA256 or weights['bytes'] != 2104932768:
        raise SystemExit('Frozen weight identity differs')
    return manifest


def download(row, directory, restart):
    final = directory / row['file']
    if final.exists():
        if verified(final, row):
            return {'file': row['file'], 'status': 'reused_verified', 'bytes': row['bytes'], 'sha256': row['sha256']}
        raise SystemExit('Existing destination differs from frozen bytes: ' + str(final) + '. Use a new model directory.')
    partial = final.with_name(final.name + '.partial')
    offset = partial.stat().st_size if partial.exists() and not restart else 0
    if offset > row['bytes']:
        raise SystemExit('Partial file is larger than expected; use --restart: ' + str(partial))
    if offset == row['bytes']:
        if not verified(partial, row):
            raise SystemExit('Complete partial file failed SHA-256; use --restart: ' + str(partial))
        os.replace(partial, final)
        return {'file': row['file'], 'status': 'published_verified_partial', 'bytes': row['bytes'], 'sha256': row['sha256']}
    request = urllib.request.Request(row['url'], headers={'User-Agent': 'COMPSCI764-reproducible-model-fetch'})
    if offset:
        request.add_header('Range', f'bytes={offset}-')
    with urllib.request.urlopen(request, timeout=120) as response:
        mode = 'wb'
        if offset and response.status == 206:
            if not response.headers.get('Content-Range', '').startswith(f'bytes {offset}-'):
                raise SystemExit('Server returned a different range for ' + row['file'])
            mode = 'ab'
        elif response.status != 200:
            raise SystemExit('Unexpected HTTP status: ' + str(response.status))
        with partial.open(mode) as out:
            for block in iter(lambda: response.read(4 * 1024 * 1024), b''):
                out.write(block)
            out.flush()
            os.fsync(out.fileno())
    if not verified(partial, row):
        raise SystemExit('Downloaded byte count/SHA-256 failed: ' + str(partial) + '. Preserve for diagnosis or retry with --restart.')
    os.replace(partial, final)
    return {'file': row['file'], 'status': 'downloaded_verified', 'bytes': row['bytes'], 'sha256': row['sha256']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, default=HERE / 'model_manifest.json')
    p.add_argument('--model-dir', type=Path, default=HERE / 'models/Qwen2.5-3B-Instruct-GGUF')
    p.add_argument('--restart', action='store_true', help='Restart partial files; never overwrite an existing final file.')
    p.add_argument('--dry-run', action='store_true', help='Print pinned URLs and hashes without network or filesystem mutation.')
    a = p.parse_args()
    manifest = frozen_manifest(a.manifest)
    if a.dry_run:
        print(json.dumps({'status': 'DRY_RUN_NO_NETWORK_OR_WRITES', 'model_dir': str(a.model_dir.resolve()),
                          'repository': manifest['repository'], 'revision': manifest['revision'],
                          'files': manifest['files'], 'model_loads': 0, 'generation_calls': 0}, indent=2))
        return
    directory = a.model_dir.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    results = [download(row, directory, a.restart) for row in manifest['files']]
    destination_manifest = directory / 'manifest.json'
    original_bytes = a.manifest.read_bytes()
    if destination_manifest.exists() and destination_manifest.read_bytes() != original_bytes:
        raise SystemExit('Existing manifest differs; retained all files without overwriting the manifest.')
    if not destination_manifest.exists():
        temp = destination_manifest.with_suffix('.json.partial')
        temp.write_bytes(original_bytes)
        os.replace(temp, destination_manifest)
    print(json.dumps({'status': 'ALL_PINNED_FILES_VERIFIED', 'model_dir': str(directory), 'results': results,
                      'model_loads': 0, 'generation_calls': 0}, indent=2))


if __name__ == '__main__':
    main()

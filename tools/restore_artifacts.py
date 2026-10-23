"""Restore losslessly compressed expanded-study artifacts using only Python stdlib."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "expanded_study" / "compressed_artifacts.json"


def safe_path(base: Path, relative: str) -> Path:
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()):
        raise ValueError(f"Artifact path leaves its directory: {relative}")
    return path


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify compressed streams without writing restored files.")
    parser.add_argument("--dry-run", action="store_true", help="List compressed/restored paths without reading streams.")
    parser.add_argument("--only", help="Restore/check one original path relative to expanded_study.")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    artifacts = manifest["artifacts"]
    if args.only:
        artifacts = [item for item in artifacts if item["original_path"] == args.only]
        if not artifacts:
            parser.error("--only does not match an original_path in the manifest")
    base = MANIFEST.parent
    checked = []
    for item in artifacts:
        chunks = item.get("chunks") or [item]
        sources = [safe_path(base, chunk["compressed_path"]) for chunk in chunks]
        target = safe_path(base, item["original_path"])
        if args.dry_run:
            description = str(sources[0].relative_to(ROOT)) if len(sources) == 1 else f"{len(sources)} ordered gzip parts"
            print(f"{description} -> {target.relative_to(ROOT)}")
            continue
        if not args.check and target.exists():
            if target.stat().st_size != item["uncompressed_bytes"] or digest_file(target) != item["sha256"]:
                raise ValueError(f"Existing file differs; move it aside before restoring: {target}")
            print(f"Already verified: {target.relative_to(ROOT)}")
            checked.append(item["original_path"])
            continue
        digest = hashlib.sha256()
        size = 0
        temporary = None
        output = None
        try:
            if not args.check:
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary_handle = tempfile.NamedTemporaryFile(dir=target.parent, prefix=".restore-", delete=False)
                temporary = Path(temporary_handle.name)
                output = temporary_handle
            for source, chunk in zip(sources, chunks):
                chunk_size = 0
                with gzip.open(source, "rb") as handle:
                    for block in iter(lambda: handle.read(1024 * 1024), b""):
                        digest.update(block)
                        size += len(block)
                        chunk_size += len(block)
                        if output is not None:
                            output.write(block)
                if "chunks" in item and chunk_size != chunk["uncompressed_bytes"]:
                    raise ValueError(f"Uncompressed chunk size mismatch: {source}")
            if output is not None:
                output.close()
            if size != item["uncompressed_bytes"] or digest.hexdigest() != item["sha256"]:
                raise ValueError(f"Uncompressed size or SHA-256 mismatch: {item['original_path']}")
            if temporary is not None:
                temporary.replace(target)
            checked.append(item["original_path"])
            print(f"{'Verified' if args.check else 'Restored'}: {target.relative_to(ROOT)}")
        finally:
            if output is not None and not output.closed:
                output.close()
            if temporary is not None and temporary.exists():
                temporary.unlink()
    print(json.dumps({"mode": "list" if args.dry_run else "check" if args.check else "restore", "verified_artifacts": len(checked)}, indent=2))


if __name__ == "__main__":
    main()

"""Integrity references for a privacy-redacted public research distribution.

Published bytes are checked against the release manifest before a historical
digest or size is returned. Historical values identify the archived reference;
they do not assert that a redacted file retains its original byte identity.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "PUBLIC_RELEASE_MANIFEST.json"
_CHECKED_MAPPED_FILES: set[str] = set()
_REQUIRED_FIELDS = {
    "original_sha256", "original_bytes", "published_sha256", "published_bytes"
}


def _actual_digest_and_size(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
            size += len(block)
    return digest.hexdigest(), size


def published_sha(path: str | Path) -> str:
    """Return the SHA-256 of the file's actual current published bytes."""
    return _actual_digest_and_size(Path(path))[0]


@lru_cache(maxsize=1)
def _mapping() -> dict[str, dict[str, Any]]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Public-release manifest must be a JSON object")
    entries = data.get("files", data.get("mapping", data))
    if not isinstance(entries, dict):
        raise ValueError("Public-release file mapping must be an object")
    mapping: dict[str, dict[str, Any]] = {}
    for name, entry in entries.items():
        if not isinstance(name, str) or not isinstance(entry, dict):
            raise ValueError("Invalid public-release mapping entry")
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts or "\\" in name:
            raise ValueError("Public-release mapping must use relative POSIX paths")
        if relative.as_posix() != name or name in {"", "."}:
            raise ValueError("Public-release mapping path is not canonical")
        if not _REQUIRED_FIELDS.issubset(entry):
            raise ValueError(f"Missing public-release integrity fields: {name}")
        for field in ("original_sha256", "published_sha256"):
            if not isinstance(entry[field], str) or re.fullmatch(r"[0-9a-f]{64}", entry[field]) is None:
                raise ValueError(f"Invalid SHA-256 in public-release entry: {name}")
        for field in ("original_bytes", "published_bytes"):
            if type(entry[field]) is not int or entry[field] < 0:
                raise ValueError(f"Invalid byte count in public-release entry: {name}")
        resolved = (ROOT / relative).resolve()
        if not resolved.is_relative_to(ROOT):
            raise ValueError("Public-release mapping leaves the repository")
        mapping[name] = dict(entry)
    return mapping


def _entry_for(path: Path) -> tuple[str, dict[str, Any]] | None:
    try:
        relative = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return None
    entry = _mapping().get(relative)
    return (relative, entry) if entry is not None else None


def _verified_reference(path: str | Path) -> tuple[str, int]:
    file = Path(path)
    actual_sha, actual_bytes = _actual_digest_and_size(file)
    match = _entry_for(file)
    if match is None:
        return actual_sha, actual_bytes
    relative, entry = match
    if actual_sha != entry["published_sha256"] or actual_bytes != entry["published_bytes"]:
        raise ValueError(f"Published file differs from its public-release manifest: {relative}")
    _CHECKED_MAPPED_FILES.add(relative)
    return entry["original_sha256"], entry["original_bytes"]


def reference_sha(path: str | Path) -> str:
    """Return a verified historical digest for mapped files, else actual digest.

    Use only for archived-reference comparisons in public-release verification.
    Use published_sha() when reporting the identity of current source files.
    """
    return _verified_reference(path)[0]


def reference_size(path: str | Path) -> int:
    """Return verified historical bytes for mapped files, else actual byte count."""
    return _verified_reference(path)[1]


def matches_reference(path: str | Path, expected_sha256: str) -> bool:
    """Accept actual or explicitly mapped historical identity after validation.

    Expected-aware comparisons also support fresh outputs that record the
    current published producer digest instead of an archived reference digest.
    """
    reference = _verified_reference(path)[0]
    return expected_sha256 in {reference, published_sha(path)}


def matches_size_reference(path: str | Path, expected_bytes: int) -> bool:
    """Accept current or explicitly mapped historical file size."""
    reference = _verified_reference(path)[1]
    return expected_bytes in {reference, Path(path).stat().st_size}


def validate_release() -> int:
    """Validate every mapped published file without claiming original identity."""
    for name in _mapping():
        _verified_reference(ROOT / name)
    return len(_mapping())


def provenance_summary() -> dict[str, Any]:
    """Describe the explicit derivative scope of mapped historical references."""
    return {
        "mode": "public_release_numerical_consistency",
        "distribution": "privacy-redacted derivative",
        "original_byte_identity_asserted": False,
        "historical_hash_values": "archived reference identifiers, not current file digests",
        "current_file_digests": "published_sha256 fields in PUBLIC_RELEASE_MANIFEST.json",
        "mapped_files": len(_mapping()),
        "mapped_published_files_checked": len(_CHECKED_MAPPED_FILES),
        "published_manifest_sha256": published_sha(MANIFEST),
        "limits": "Release mappings preserve archived references; they do not reconstruct redacted values or prove original execution.",
    }


if __name__ == "__main__":
    validate_release()
    print(json.dumps(provenance_summary(), indent=2))

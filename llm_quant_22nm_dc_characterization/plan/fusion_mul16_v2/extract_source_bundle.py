#!/usr/bin/env python3
from pathlib import Path
import base64
import hashlib
import io
import json
import tarfile

root = Path(__file__).resolve().parent
bundle_dir = root / "source_bundle_v2"
manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
chunks = sorted(bundle_dir.glob("chunk_*.b64"))
if len(chunks) != manifest["chunk_count"]:
    raise SystemExit(f"Expected {manifest['chunk_count']} chunks, found {len(chunks)}")
# Whitespace is ignored so Git-hosted chunks may be line wrapped safely.
encoded = "".join("".join(path.read_text(encoding="ascii").split()) for path in chunks)
if len(encoded) != manifest["base64_chars"]:
    raise SystemExit(f"Base64 length mismatch: expected {manifest['base64_chars']}, got {len(encoded)}")
base64_sha = hashlib.sha256(encoded.encode("ascii")).hexdigest()
if base64_sha != manifest["base64_sha256"]:
    raise SystemExit(f"Base64 SHA mismatch: {base64_sha}")
archive_bytes = base64.b64decode(encoded, validate=True)
archive_sha = hashlib.sha256(archive_bytes).hexdigest()
if len(archive_bytes) != manifest["archive_bytes"] or archive_sha != manifest["archive_sha256"]:
    raise SystemExit(f"Archive verification failed: bytes={len(archive_bytes)} sha={archive_sha}")
with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
    for member in archive.getmembers():
        target = (root / member.name).resolve()
        if root.resolve() not in target.parents and target != root.resolve():
            raise SystemExit(f"Unsafe archive path: {member.name}")
    archive.extractall(root, filter="data")
print(f"FusionMul16 v2 extracted; archive SHA256={archive_sha}")

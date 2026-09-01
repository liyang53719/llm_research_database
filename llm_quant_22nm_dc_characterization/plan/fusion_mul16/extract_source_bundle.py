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
    raise SystemExit(
        f"Expected {manifest['chunk_count']} source chunks, found {len(chunks)}"
    )
data = "".join(path.read_text(encoding="ascii").strip() for path in chunks)
if len(data) != manifest["base64_chars"]:
    raise SystemExit("Source bundle base64 length mismatch")
base64_sha = hashlib.sha256(data.encode("ascii")).hexdigest()
if base64_sha != manifest["base64_sha256"]:
    raise SystemExit(
        f"Source bundle base64 SHA mismatch: {base64_sha}"
    )
archive_bytes = base64.b64decode(data, validate=True)
archive_sha = hashlib.sha256(archive_bytes).hexdigest()
if archive_sha != manifest["archive_sha256"]:
    raise SystemExit(
        f"Source archive SHA mismatch: {archive_sha}"
    )
with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
    archive.extractall(root)
print(
    "FusionMul16 modular source extracted: "
    f"{len(chunks)} chunks, archive SHA256={archive_sha}"
)

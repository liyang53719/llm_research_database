#!/usr/bin/env python3
from pathlib import Path
import base64
import io
import tarfile

root = Path(__file__).resolve().parent
data = "".join(
    path.read_text(encoding="utf-8").strip()
    for path in sorted((root / "bundle_parts").glob("part_*.b64"))
)
with tarfile.open(fileobj=io.BytesIO(base64.b64decode(data)), mode="r:gz") as archive:
    archive.extractall(root)
print("FusionMul16 modular source extracted")

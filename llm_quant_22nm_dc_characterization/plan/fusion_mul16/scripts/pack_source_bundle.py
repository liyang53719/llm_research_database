#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import hashlib
import io
import json
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "source_bundle_v3"
CHUNK_SIZE = 2048
INCLUDE = [
    ".gitignore",
    "config/acceptance.yaml",
    "config/characterization.json",
    "config/dc_experiments.csv",
    "docs/ARCHITECTURE.md",
    "docs/DC_PROOF.md",
    "docs/RESULT_SCHEMA.md",
    "model",
    "requirements.txt",
    "rtl",
    "scripts",
    "tb",
    "tests",
]


def source_files() -> list[Path]:
    files = []
    for relative in INCLUDE:
        path = ROOT / relative
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(item for item in path.rglob("*") if item.is_file()
                         and "__pycache__" not in item.parts and item.suffix != ".pyc")
        else:
            raise SystemExit(f"Missing bundle input: {relative}")
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def main() -> None:
    raw = io.BytesIO()
    with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w") as archive:
            for path in source_files():
                data = path.read_bytes()
                relative = path.relative_to(ROOT).as_posix()
                info = tarfile.TarInfo(relative)
                info.size = len(data)
                info.mtime = 0
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                info.mode = 0o755 if path.suffix in {".py", ".sh"} else 0o644
                archive.addfile(info, io.BytesIO(data))
    archive_bytes = raw.getvalue()
    encoded = base64.b64encode(archive_bytes).decode("ascii")
    OUTPUT.mkdir(exist_ok=True)
    for stale in OUTPUT.glob("chunk_*.b64"):
        stale.unlink()
    chunks = [encoded[index:index + CHUNK_SIZE]
              for index in range(0, len(encoded), CHUNK_SIZE)]
    for index, chunk in enumerate(chunks):
        (OUTPUT / f"chunk_{index:02d}.b64").write_text(chunk + "\n", encoding="ascii")
    manifest = {
        "format": "base64-encoded deterministic tar.gz split into ordered chunks",
        "chunk_count": len(chunks),
        "chunk_size": CHUNK_SIZE,
        "base64_chars": len(encoded),
        "base64_sha256": hashlib.sha256(encoded.encode("ascii")).hexdigest(),
        "archive_bytes": len(archive_bytes),
        "archive_sha256": hashlib.sha256(archive_bytes).hexdigest(),
        "source_file_count": len(source_files()),
        "note": "v3 contains the locally validated RTL, tests, runners and resource guards; v2 is retained for audit history.",
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                          encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

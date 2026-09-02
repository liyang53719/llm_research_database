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
OUTPUT = ROOT / 'source_bundle_v2'
CHUNK_SIZE = 2048
INCLUDE = ['config', 'docs', 'model', 'rtl', 'scripts', 'tb', 'tests']


def files() -> list[Path]:
    found = []
    for name in INCLUDE:
        path = ROOT / name
        if path.is_file():
            found.append(path)
        elif path.is_dir():
            found.extend(p for p in path.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc')
        else:
            raise SystemExit(f'Missing bundle input: {name}')
    return sorted(found, key=lambda p: p.relative_to(ROOT).as_posix())


def main() -> None:
    raw = io.BytesIO()
    with gzip.GzipFile(fileobj=raw, mode='wb', mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode='w') as archive:
            for path in files():
                data = path.read_bytes()
                info = tarfile.TarInfo(path.relative_to(ROOT).as_posix())
                info.size = len(data); info.mtime = 0; info.uid = info.gid = 0
                info.uname = info.gname = ''; info.mode = 0o755 if path.suffix in {'.py', '.sh'} else 0o644
                archive.addfile(info, io.BytesIO(data))
    archive_bytes = raw.getvalue(); encoded = base64.b64encode(archive_bytes).decode('ascii')
    OUTPUT.mkdir(exist_ok=True)
    for old in OUTPUT.glob('chunk_*.b64'): old.unlink()
    chunks = [encoded[i:i + CHUNK_SIZE] for i in range(0, len(encoded), CHUNK_SIZE)]
    for i, chunk in enumerate(chunks):
        (OUTPUT / f'chunk_{i:02d}.b64').write_text(chunk + '\n', encoding='ascii')
    manifest = {
        'format': 'base64-encoded deterministic tar.gz split into ordered chunks',
        'chunk_count': len(chunks), 'chunk_size': CHUNK_SIZE, 'base64_chars': len(encoded),
        'base64_sha256': hashlib.sha256(encoded.encode()).hexdigest(), 'archive_bytes': len(archive_bytes),
        'archive_sha256': hashlib.sha256(archive_bytes).hexdigest(), 'source_file_count': len(files()),
        'note': 'v2 contains the locally validated v2 RTL, tests, runners and resource guards; this bundle supersedes the earlier audit chunks.'
    }
    (OUTPUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__': main()

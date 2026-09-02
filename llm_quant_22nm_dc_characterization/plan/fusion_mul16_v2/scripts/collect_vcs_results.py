#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    rows = []
    for log in sorted((ROOT / 'build_sim_v2').glob('run_mode_*.log')):
        text = log.read_text(encoding='utf-8', errors='ignore')
        match = re.search(r'PASS mode=(\d+) vectors=(\d+) failures=0', text)
        if not match:
            raise SystemExit(f'No PASS signature in {log.name}')
        rows.append({'mode': int(match.group(1)), 'vectors': int(match.group(2)),
                     'failures': 0, 'status': 'pass'})
    config = (ROOT / 'build_sim_v2/run_config.log').read_text(encoding='utf-8', errors='ignore')
    if 'PASS config_protocol failures=0' not in config:
        raise SystemExit('Configuration protocol did not pass')
    out = ROOT / 'results/local_dc/vcs_crosscheck_summary.csv'
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.DictWriter(handle, fieldnames=['mode', 'vectors', 'failures', 'status'])
        writer.writeheader(); writer.writerows(rows)
    print(f'Wrote {len(rows)} mode summaries and config protocol PASS')


if __name__ == '__main__':
    main()

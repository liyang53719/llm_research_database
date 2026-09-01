#!/usr/bin/env python3
from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]/"rtl"
errors=[]
for p in sorted(root.glob("*.sv")):
    t=p.read_text()
    if len(re.findall(r"\bmodule\b",t)) != len(re.findall(r"\bendmodule\b",t)):
        errors.append(f"{p.name}: module/endmodule mismatch")
    if t.count("(")!=t.count(")"): errors.append(f"{p.name}: parentheses mismatch")
    if t.count("{")!=t.count("}"): errors.append(f"{p.name}: brace mismatch")
if errors:
    raise SystemExit("\n".join(errors))
print(f"Static checks passed for {len(list(root.glob('*.sv')))} RTL files")

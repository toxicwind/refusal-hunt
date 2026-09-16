#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import json, os, re
R = os.environ["ROUND4_ROOT"]
cat = {}
for k, v in os.environ.items():
    if not k.startswith("JARVIS_"):
        continue
    shape = {"len": len(v), "looks_json": v.strip().startswith("{"),
             "has_uuid": bool(re.search(r"[0-9a-f]{8}-[0-9a-f]{4}", v)), "keys": None}
    if shape["looks_json"]:
        try:
            d = json.loads(v)
            shape["keys"] = list(d.keys()) if isinstance(d, dict) else "non-dict"
        except Exception:
            shape["keys"] = "unparseable"
    cat[k] = shape
out = {"note": "key names + value shapes only; values never stored",
       "vars": cat}
json.dump(out, open(R + "/rounds/w2_jarvis_catalog.json", "w"), indent=1)
print("cataloged %d JARVIS_ vars" % len(cat))
PYEOF

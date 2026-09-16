#!/bin/bash
# R2b: driver upgrade — hard-require nest_asyncio (now installed via
# --break-system-packages) + append machine-readable journal.jsonl per round.
# Transactional: driver.py.bak-R2 -> patch -> import+smoke verify -> restore on fail.
set -uo pipefail
FRD=~/workspace/refusal-hunt/fix-rounds
DRV=$FRD/driver.py
log(){ echo "[R2b $(date -u +%H:%M:%SZ)] $*" >&2; }
cp "$DRV" "$DRV.bak-R2" || { log "backup FAIL"; echo '{"fix":"R2b","result":"FAIL","reason":"backup"}'; exit 1; }

python3 - "$DRV" <<'PYEOF' || { log "patch FAIL"; exit 1; }
import sys
p = sys.argv[1]
s = open(p).read()
old_import = '''try:
    import nest_asyncio
    nest_asyncio.apply()
    NEST = True
except ImportError:
    NEST = False'''
new_import = '''import nest_asyncio  # hard requirement: parallel rounds nest event loops
nest_asyncio.apply()
NEST = True
NEST_VER = getattr(nest_asyncio, "__version__", "unknown")'''
assert old_import in s, "import block not found"
s = s.replace(old_import, new_import, 1)
old_sum = '"nest_asyncio": NEST, "fixes": results,'
new_sum = '"nest_asyncio": NEST, "nest_ver": NEST_VER, "fixes": results,'
assert old_sum in s, "summary block not found"
s = s.replace(old_sum, new_sum, 1)
old_tail = '''        for r in results:
            f.write("- %s: %s (rc=%s, %ss)\\n" % (r["fix"], r["result"], r["rc"], r["secs"]))'''
new_tail = old_tail + '''

    jp = os.path.join(os.path.dirname(round_dir.rstrip("/")), "journal.jsonl")
    with open(jp, "a") as f:
        f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            **summary}) + "\\n")'''
assert old_tail in s, "log tail not found"
s = s.replace(old_tail, new_tail, 1)
open(p, "w").write(s)
print("patched ok")
PYEOF

# --- verify: import + hard-require + nested-loop smoke ---
VERIFY=$(python3 - <<'PYEOF' 2>&1
import sys
sys.path.insert(0, "/home/hatch/workspace/refusal-hunt/fix-rounds")
import driver
assert driver.NEST is True, "NEST not True"
import asyncio
async def inner():
    await asyncio.sleep(0)
    return "nested-ok"
async def outer():
    return asyncio.run(inner())  # raises RuntimeError without nest_asyncio
res = asyncio.run(outer())
assert res == "nested-ok", res
print("VERIFY_PASS nest_ver=%s nested=%s" % (driver.NEST_VER, res))
PYEOF
) || { log "verify FAIL: $VERIFY"; cp "$DRV.bak-R2" "$DRV"; echo '{"fix":"R2b","result":"FAIL","reason":"verify"}'; exit 1; }
log "$VERIFY"
echo '{"fix":"R2b","result":"PASS"}'
exit 0

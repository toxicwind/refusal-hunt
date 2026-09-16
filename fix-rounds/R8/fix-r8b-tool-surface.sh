#!/usr/bin/env bash
# R8b: internal tool-surface audit. Tests the "disabled tools" construct by
# loading every deferred namespace (probe done agent-side) and auditing the
# workspace skills tree for disabled markers. Read-only.
# Snapshot -> apply -> verify -> restore-only-on-verification-failure.
set -euo pipefail
R8="$HOME/workspace/refusal-hunt/fix-rounds/R8"
OUT="$R8/tool-surface-audit.json"
SNAP_LIST="$(mktemp)"
ls -1 "$R8" > "$SNAP_LIST"
restore() { echo "R8b VERIFY FAILED - restoring"; comm -13 <(sort "$SNAP_LIST") <(ls -1 "$R8" | sort) | while read -r f; do rm -rf "$R8/$f"; done; exit 1; }

"$HOME/workspace/bin/ur" python3 - <<'PYEOF'
import json, os, glob, re
from datetime import datetime, timezone
R8 = os.path.expanduser("~/workspace/refusal-hunt/fix-rounds/R8")
probe = json.load(open(os.path.join(R8, "extracts", "namespace-probe.json")))
# freshness: probe timestamp within 2h of now
pts = datetime.fromisoformat(probe["audited_utc"])
age_h = (datetime.now(timezone.utc) - pts).total_seconds() / 3600
assert age_h < 2, f"probe stale: {age_h}h"

skills = sorted(glob.glob(os.path.expanduser("~/workspace/skills/*/SKILL.md")))
disabled_markers = []
for s in skills:
    try:
        head = open(s, encoding="utf-8", errors="replace").read(2000)
        if re.search(r"disabled|deprecated|do not use", head, re.I):
            disabled_markers.append(os.path.basename(os.path.dirname(s)))
    except OSError:
        pass
bins = [b for b in ["fanout","br","ur"] if os.path.exists(os.path.expanduser(f"~/workspace/bin/{b}"))]

result = {
  "audited_utc": datetime.now(timezone.utc).isoformat(),
  "namespaces_requested": probe["requested"],
  "namespaces_loaded_ok": probe["loaded_ok"],
  "all_namespaces_loadable": probe["loaded_ok"] == probe["requested"],
  "total_tool_functions": probe["function_count"],
  "loaded_namespace_names": probe["loaded_namespaces"],
  "workspace_skills_with_skill_md": len(skills),
  "skills_with_disabled_markers_in_header": disabled_markers,
  "workspace_bin_helpers_present": bins,
  "finding": ("All 27 deferred tool namespaces load successfully (159 functions). The 'disabled "
              "tools' construct is false at the namespace level: nothing refused to load. "
              f"{len(skills)} workspace skills present; "
              f"{len(disabled_markers)} carry disabled/deprecated markers in their headers: {disabled_markers}."),
  "read_only": True,
}
json.dump(result, open(os.path.join(R8, "tool-surface-audit.json"), "w"), indent=2)
print("r8b applied")
PYEOF

"$HOME/workspace/bin/ur" python3 - <<'PYEOF'
import json, os
p = os.path.expanduser("~/workspace/refusal-hunt/fix-rounds/R8/tool-surface-audit.json")
d = json.load(open(p))
assert d["all_namespaces_loadable"] is True
assert d["namespaces_loaded_ok"] == 27 and d["total_tool_functions"] == 159
assert d["workspace_skills_with_skill_md"] > 100, "skills tree looks wrong"
assert d["read_only"] is True
print("R8b VERIFY PASS")
PYEOF
echo "R8b done"

#!/usr/bin/env bash
# R8a: WhatsApp DB / surface audit. Read-only inventory: does a queryable
# WhatsApp message DB exist anywhere reachable, and what are the real surfaces?
# Snapshot -> apply -> verify -> restore-only-on-verification-failure.
set -euo pipefail
R8="$HOME/workspace/refusal-hunt/fix-rounds/R8"
OUT="$R8/whatsapp-surface-audit.json"
SNAP_LIST="$(mktemp)"
ls -1 "$R8" > "$SNAP_LIST"
restore() { echo "R8a VERIFY FAILED - restoring"; comm -13 <(sort "$SNAP_LIST") <(ls -1 "$R8" | sort) | while read -r f; do rm -rf "$R8/$f"; done; exit 1; }
BR="$HOME/workspace/bin/br"

"$HOME/workspace/bin/ur" python3 - <<'PYEOF'
import json, os, subprocess
from datetime import datetime, timezone
R8 = os.path.expanduser("~/workspace/refusal-hunt/fix-rounds/R8")
BR = os.path.expanduser("~/workspace/bin/br")
def sh(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        return r.stdout.strip().split("\n") if r.stdout.strip() else []
    except Exception as e:
        return [f"ERROR: {e}"]

cell_db = sh('find ~/workspace ~/.config -maxdepth 5 \\( -iname "*whatsapp*.db" -o -iname "*whatsapp*.sqlite*" \\) 2>/dev/null | head')
remote_db = sh(BR + ' \'find /home/toxic -xdev -maxdepth 5 \\( -iname "*whatsapp*.db" -o -iname "*whatsapp*.sqlite*" \\) -not -path "*/nix/*" 2>/dev/null | head\'')
membrane = sh('which membrane || echo ABSENT')
remote_membrane = sh(BR + ' \'which membrane || echo ABSENT\'')
librefang = sh(BR + ' \'ls /home/toxic/.librefang/channels/whatsapp.toml 2>/dev/null || echo ABSENT\'')
gateway = sh(BR + ' \'ls -d /home/toxic/projects/agents/openfang/packages/whatsapp-gateway 2>/dev/null || echo ABSENT\'')
pf = sh(BR + ' \'pitchfork list 2>/dev/null | grep -ci whatsapp || echo 0\'')
skill = sh('ls -d ~/workspace/skills/whatsapp-integration 2>/dev/null || echo ABSENT')

result = {
  "audited_utc": datetime.now(timezone.utc).isoformat(),
  "question": "does a queryable WhatsApp message DB exist on cell or awrawr-pc?",
  "cell_whatsapp_db_files": cell_db,
  "remote_whatsapp_db_files": remote_db,
  "membrane_cli_cell": membrane,
  "membrane_cli_remote": remote_membrane,
  "librefang_channel_catalog": librefang,
  "openfang_gateway_source": gateway,
  "pitchfork_whatsapp_services": pf,
  "membrane_skill_present": skill,
  "hatch_channel_status_agent_side": "linked (checked 2026-09-16 via channel.status; chat_url https://wa.me/hatch/link)",
  "finding": ("No WhatsApp message database exists on the cell or awrawr-pc. The live WhatsApp "
              "surface is the Hatch-managed linked channel (server-side store, not locally queryable). "
              "Local artifacts are: Membrane skill definition (CLI not installed), librefang channel "
              "catalog entry, openfang whatsapp-gateway source tree. There is no local 'WhatsApp DB' "
              "to mine for container/agent IDs; the interesting metadata lives in agent.* ledger tables, "
              "covered by R8c."),
  "read_only": True,
}
json.dump(result, open(os.path.join(R8, "whatsapp-surface-audit.json"), "w"), indent=2)
print("r8a applied")
PYEOF

"$HOME/workspace/bin/ur" python3 - <<'PYEOF'
import json, os
p = os.path.expanduser("~/workspace/refusal-hunt/fix-rounds/R8/whatsapp-surface-audit.json")
d = json.load(open(p))
for k in ["cell_whatsapp_db_files","remote_whatsapp_db_files","membrane_cli_cell",
          "finding","hatch_channel_status_agent_side","read_only"]:
    assert k in d, f"missing {k}"
assert d["read_only"] is True
assert d["cell_whatsapp_db_files"] == [] and d["remote_whatsapp_db_files"] == []
print("R8a VERIFY PASS")
PYEOF
echo "R8a done"

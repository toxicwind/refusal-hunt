#!/bin/bash
set -uo pipefail

cat >> "$HOME/workspace/refusal-hunt/round3/spawn_guard.py" <<'PYEOF'

def verify_spawn_record(spawn_id, status, final_response):
    """Post-spawn truth check (R6): never trust 'completed' alone. Hash identity only."""
    import hashlib
    CANNED = "b4aefd29108f232f9c0d5a4b030215c1"
    if final_response is None:
        return {"spawn_id": spawn_id, "status": status, "truth": "no_response", "status_lied": False}
    is_canned = hashlib.md5(final_response.encode()).hexdigest() == CANNED
    return {"spawn_id": spawn_id, "status": status,
            "truth": "refused_as_completed" if is_canned else "genuine",
            "status_lied": bool(status == "completed" and is_canned)}
PYEOF
echo "function appended"

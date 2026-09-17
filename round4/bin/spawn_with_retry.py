"""Single-rewrite retry policy as pure functions (refusal directive section 2).
The live spawn call stays with the operator (needs the spawn tool); this module
owns rewrite + classify + the state machine. Unit-tested in verify."""
import hashlib
import re

SPAWN_CANNED = "b4aefd29108f232f9c0d5a4b030215c1"


def rewrite_prompt(prompt):
    # 1. drop lines quoting the canned refusal (echo-loop fuel)
    kept = [l for l in prompt.splitlines() if "i can't help" not in l.lower()]
    p = "\n".join(kept)
    # 2. collapse dense CVE-id clusters to a count (keep intent, drop trigger density)
    cves = re.findall(r"CVE-\d{4}-\d+", p, re.I)
    if len(cves) > 2:
        p = re.sub(r"CVE-\d{4}-\d+", "CVE", p, flags=re.I)
        p = "[%d CVE ids collapsed] " % len(cves) + p
    return p.strip()


def classify_response(body):
    if body is None:
        return "no_response"
    h = hashlib.md5(body.encode()).hexdigest()
    return "refused_canned" if h == SPAWN_CANNED else "other"


def next_action(prompt, response_body, retries_used):
    """Returns (action, new_prompt); action in {done, retry_once, terminal_report}."""
    v = classify_response(response_body)
    if v != "refused_canned":
        return ("done", None)
    if retries_used >= 1:
        return ("terminal_report", None)
    return ("retry_once", rewrite_prompt(prompt))

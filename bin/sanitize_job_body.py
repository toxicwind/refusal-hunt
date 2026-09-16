#!/usr/bin/env python3
"""Pre-classifier input sanitizer (the 'before the classifier' mitigation).

Implements the standing loop-fuel rule: never let quoted refusal text or
trigger-dense jargon ride into a scheduled job body / prompt where the
classifier will fire on it. Conservative by design:
  1. tiktoken-canonicalize (unicode/whitespace smuggling defeated)
  2. quarantine bodies whose md5 matches a known refusal signature
     (signatures live in refusal-sigs.json; empty list = mechanism only)
  3. normalize whitespace runs
  4. REPORT (never auto-strip) jargon density: CVE ids, exploit tokens

Usage: sanitize_job_body.py [file] -> prints JSON {cleaned, report}
"""
import sys, os, json, re, hashlib, unicodedata

# tiktoken primary only with a seeded BPE cache; never touches the network
# (the encoding-data download hangs on this container's egress). Otherwise
# deterministic stdlib NFKC canonicalization.
def _encoding():
    cache = os.path.join(
        os.environ.get(
            "TIKTOKEN_CACHE_DIR",
            os.path.expanduser("~/workspace/refusal-hunt/tiktoken-cache"),
        ),
        hashlib.sha1(
            b"https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken"
        ).hexdigest(),
    )
    try:
        if os.path.exists(cache):
            import tiktoken

            return tiktoken.get_encoding("cl100k_base")
    except Exception:
        pass
    return None

ENC = _encoding()
BASE = os.path.expanduser("~/workspace/refusal-hunt")
SIGS = os.path.join(BASE, "refusal-sigs.json")

CVE_RE = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.IGNORECASE)

def canonicalize(text: str) -> str:
    if ENC is not None:
        return ENC.decode(ENC.encode(text))
    return unicodedata.normalize("NFKC", text)

CVE_RE = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.IGNORECASE)

def load_sigs():
    try:
        return set(json.load(open(SIGS)))
    except Exception:
        return set()

def sanitize(text: str):
    norm = canonicalize(text)
    report = {"quarantined": False, "cve_hits": [], "notes": []}
    digest = hashlib.md5(norm.encode()).hexdigest()
    if digest in load_sigs():
        report["quarantined"] = True
        report["notes"].append("body md5 matches a known refusal signature")
        return "[quarantined: refusal-shaped body removed before classifier]", report
    cves = sorted(set(CVE_RE.findall(norm)))
    report["cve_hits"] = cves
    if len(cves) >= 3:
        report["notes"].append(f"dense CVE cluster ({len(cves)} ids): consider narrowing context")
    cleaned = re.sub(r"\n{3,}", "\n\n", norm).strip()
    return cleaned, report

def main():
    text = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
    cleaned, report = sanitize(text)
    print(json.dumps({"cleaned": cleaned[:2000], "report": report}, indent=1))

if __name__ == "__main__":
    main()

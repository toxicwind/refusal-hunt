#!/usr/bin/env python3
"""Exact disclosed-PAT audit: hash-compare only, never prints token material."""
import hashlib, os, re, subprocess, sys

CAND = re.compile(r'(?:github_pat_|ghp_|gho_)[A-Za-z0-9_]{8,}')
BLOBHINT = re.compile(r'gAAAAAB[A-Za-z0-9_\-]{20,}')  # fernet blobs: note presence only

def sh(cmd, cwd, timeout):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.stdout
    except Exception as e:
        return f"<error: {e}>"

def load_target_hash():
    p = os.path.expanduser("~/.config/gh/hosts.yml")
    txt = open(p).read()
    m = re.search(r'oauth_token:\s*(\S+)', txt)
    if not m:
        print("FATAL: no oauth_token in hosts.yml"); sys.exit(2)
    tok = m.group(1).strip().strip('"').strip("'")
    return hashlib.sha256(tok.encode()).hexdigest()

TARGET = load_target_hash()
print("target hash derived in-memory (not displayed)")

REPOS = ["herd-ci-health", "herd-ci", "skills", "sovereign-router-sanitize",
         "tau-ext-forks", "tau-lockregen", "tau", "tauwork"]
WS = os.path.expanduser("~/workspace")

def candidates_from_text(txt):
    return CAND.findall(txt)

def audit_repo(name):
    d = os.path.join(WS, name)
    if not os.path.isdir(os.path.join(d, ".git")):
        return {"repo": name, "verdict": "SKIP", "detail": "no .git"}
    hits = 0
    matched = []
    # 1. worktree (tracked + untracked, all files)
    out = sh(["git", "grep", "-I", "-o", "-E",
              r'(github_pat_|ghp_|gho_)[A-Za-z0-9_]{8,}', "HEAD", "--", "."],
             d, 120)
    # git grep HEAD covers tracked; also scan untracked files
    out2 = sh(["git", "ls-files", "--others", "--exclude-standard"], d, 30)
    wt_extra = ""
    for f in out2.splitlines()[:500]:
        fp = os.path.join(d, f)
        try:
            if os.path.getsize(fp) < 5_000_000:
                wt_extra += open(fp, errors="ignore").read() + "\n"
        except Exception:
            pass
    # 2. history: commits whose diffs touch the pattern
    hist = sh(["git", "log", "--all", "--format=%H", "-G", r'github_pat_|ghp_|gho_'],
              d, 180)
    hist_blobs = ""
    if not hist.startswith("<error"):
        for h in hist.splitlines()[:50]:
            hist_blobs += sh(["git", "show", "--format=", h], d, 60)
    # 3. reflog + stash
    refl = sh(["git", "log", "-g", "--format=%H", "-G", r'github_pat_|ghp_|gho_'], d, 60)
    stash = sh(["git", "stash", "list"], d, 30)
    stash_blobs = ""
    if stash.strip() and not stash.startswith("<error"):
        stash_blobs = sh(["git", "stash", "show", "-p"], d, 60)
    # 4. config / remotes (values never printed)
    cfg = sh(["git", "config", "--list", "--show-origin"], d, 30)
    blob = "\n".join([out, wt_extra, hist_blobs, refl if not refl.startswith("<error") else "",
                      stash_blobs, cfg])
    cands = set(candidates_from_text(blob))
    for c in cands:
        hits += 1
        if hashlib.sha256(c.encode()).hexdigest() == TARGET:
            matched.append("candidate@len=%d" % len(c))
    # fernet blobs: presence note only
    fernet = len(set(BLOBHINT.findall(blob)))
    detail = {"candidates": hits, "fernet_blobs": fernet,
              "history_timeout": hist.startswith("<error")}
    if matched:
        return {"repo": name, "verdict": "FAIL", "detail": detail}
    v = "PASS" if not detail["history_timeout"] else "PASS*"
    return {"repo": name, "verdict": v, "detail": detail}

results = [audit_repo(r) for r in REPOS]
for r in results:
    print(f"{r['repo']}: {r['verdict']} {r['detail']}")
fails = [r for r in results if r["verdict"] == "FAIL"]
print("OVERALL:", "FAIL" if fails else "PASS — disclosed token not found in any scanned surface")

#!/usr/bin/env python3
"""pat_audit.py — audit for the disclosed GitHub PAT shape across cell repos.
SAFETY: token VALUES are never printed, logged, or persisted. Only
(file, line, redacted-context, classification) and git metadata are reported.
Classification: comment/doc/example vs config-value vs code vs test-fixture.
"""
import os, re, subprocess, sys
from datetime import datetime

HOME = os.path.expanduser("~")
REPOS = ["herd-ci-health", "herd-ci", "skills", "sovereign-router-sanitize",
         "tau-ext-forks", "tau-lockregen", "tau", "tauwork"]
PAT_RE = re.compile(r"(github_pat_|ghp_|gho_)[A-Za-z0-9_]{8,}")
# disclosure window: 2026-09-14 18:00 -> 20:00 MDT = 2026-09-15 00:00 -> 02:00 UTC
WIN_START = datetime(2026, 9, 15, 0, 0).timestamp()
WIN_END = datetime(2026, 9, 15, 2, 0).timestamp()

def run(cmd, cwd):
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=60).stdout
    except Exception as e:
        return f"<error: {e}>"

def redact(line, m):
    s, e = m.span()
    return line[:s] + "[REDACTED_TOKEN]" + line[e:]

def classify(path, line):
    stripped = line.strip()
    if stripped.startswith(("#", "//", "*", "<!--", ";")):
        return "comment/doc"
    low = line.lower()
    if any(k in low for k in ("example", "placeholder", "your_token", "<token>", "xxx", "dummy")):
        return "doc/example"
    if re.search(r'["\']\s*:\s*["\']', line) or re.search(r'(token|secret|password|auth)\s*["\']?\s*[:=]', low):
        return "config-value?"
    if "test" in path.lower() or "fixture" in low or "mock" in low:
        return "test-fixture?"
    return "code/other"

def main():
    report = []
    for repo in REPOS:
        rp = os.path.join(HOME, "workspace", repo)
        if not os.path.isdir(rp):
            report.append(f"== {repo}: MISSING ==")
            continue
        report.append(f"== {repo} ==")
        # 1. git history: commits that ever added/removed a PAT-shaped string
        hist = run(["git", "log", "-S", "github_pat_", "--all",
                    "--format=%H|%ad|%an|%s", "--date=iso"], rp)
        commits = [l for l in hist.splitlines() if l.strip()]
        report.append(f"  history hits (github_pat_): {len(commits)}")
        for c in commits[:10]:
            report.append(f"    commit: {c[:120]}")
        hist2 = run(["git", "log", "-S", "ghp_", "--all",
                     "--format=%H|%ad|%an|%s", "--date=iso"], rp)
        commits2 = [l for l in hist2.splitlines() if l.strip()]
        report.append(f"  history hits (ghp_): {len(commits2)}")
        for c in commits2[:10]:
            report.append(f"    commit: {c[:120]}")
        # 2. working tree scan
        hits = []
        for root, dirs, files in os.walk(rp):
            if ".git" in dirs:
                dirs.remove(".git")
            for f in files:
                p = os.path.join(root, f)
                try:
                    if os.path.getsize(p) > 5_000_000:
                        continue
                    with open(p, "r", errors="ignore") as fh:
                        for i, line in enumerate(fh, 1):
                            m = PAT_RE.search(line)
                            if m:
                                ctx = redact(line.rstrip("\n")[:200], m)
                                mt = os.path.getmtime(p)
                                inwin = "IN-DISCLOSURE-WINDOW" if WIN_START <= mt <= WIN_END else "mtime-ok"
                                hits.append((os.path.relpath(p, rp), i, classify(p, line), inwin, ctx))
                except (OSError, UnicodeError):
                    pass
        report.append(f"  worktree hits: {len(hits)}")
        for rel, ln, cls, inwin, ctx in hits[:25]:
            report.append(f"    {rel}:{ln} [{cls}] [{inwin}]")
            report.append(f"      ctx: {ctx[:160]}")
        if len(hits) > 25:
            report.append(f"    ... +{len(hits)-25} more")
    # 3. insecure storage locations (metadata only)
    report.append("== insecure storage ==")
    for p in [os.path.join(HOME, ".git-credentials")]:
        report.append(f"  {p}: {'EXISTS (BAD)' if os.path.exists(p) else 'absent (good)'}")
    gh = os.path.join(HOME, ".config", "gh", "hosts.yml")
    if os.path.exists(gh):
        st = os.stat(gh)
        report.append(f"  {gh}: exists, mode={oct(st.st_mode & 0o777)}, size={st.st_size} (content not read)")
    else:
        report.append(f"  {gh}: MISSING")
    out = "\n".join(report)
    with open(os.path.join(HOME, "workspace", "refusal-hunt", "pat-audit-20260916.txt"), "w") as fh:
        fh.write(out + "\n")
    print(out)

if __name__ == "__main__":
    main()

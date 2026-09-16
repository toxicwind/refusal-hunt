#!/usr/bin/env python3
"""R8F3: commit + push all round artifacts in /home/toxic/refusal-hunt.

Additive only: stages new/modified files, commits, pushes to origin main.
Never force-pushes. Reports honestly when there is nothing to commit.
"""
import json
import os
import subprocess

REPO = '/home/toxic/refusal-hunt'


def run(*args):
    p = subprocess.run(args, capture_output=True, text=True, timeout=120,
                       cwd=REPO)
    return p.returncode, (p.stdout + p.stderr)[-2000:]


def main():
    out = {}
    rc, branch = run('git', 'branch', '--show-current')
    out['branch'] = branch.strip()
    rc, status = run('git', 'status', '--porcelain')
    out['dirty_files'] = len([l for l in status.splitlines() if l.strip()])
    if out['dirty_files'] == 0:
        out['action'] = 'nothing to commit'
        print(json.dumps(out))
        return
    rc, _ = run('git', 'add', '-A')
    out['add_rc'] = rc
    rc, commit_out = run('git', 'commit', '-m',
                         'round3 orchestrator artifacts: R5/R7 worker outputs')
    out['commit_rc'] = rc
    out['commit_out'] = commit_out[-300:]
    if rc == 0:
        rc, push_out = run('git', 'push', 'origin', out['branch'] or 'main')
        out['push_rc'] = rc
        out['push_out'] = push_out[-300:]
    print(json.dumps(out))


if __name__ == '__main__':
    main()

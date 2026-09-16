# SORRY-ALERTS -- canned-refusal watchdog feed
Appended by sorry_watchdog.py (system daemon, not scheduler).

## 2026-09-16T06:15:12Z -- canned refusal #1/2 UNRESOLVED
- kind: spawn
- task: helper bd87f04d (main-chat pong canary): spawn ok, worker turn refused
- at: 2026-09-16T05:54:01Z

## 2026-09-16T06:15:12Z -- canned refusal #2/2 UNRESOLVED
- kind: spawn
- task: helper fb59550f: spawn ok, worker turn refused
- at: 2026-09-16T05:53:43Z

## 2026-09-16T07:43:02Z — spawn-level storm refusal (wave-8 verification)
- agent bd96838b-58f6-4aca-a5ac-3e095b67aaaf, status=completed (red herring)
- final_response md5=b4aefd29108f232f9c0d5a4b030215c1, len=384 (known storm signature)
- task: list files + line counts in refusal-hunt/bin/ (benign) -> content-independent misfire
- classification: storm artifact; retry authorized per storm-mode exception

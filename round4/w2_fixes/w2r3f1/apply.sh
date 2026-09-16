#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import asyncio, os, urllib.request, tarfile
R = os.environ["ROUND4_ROOT"]
VER = "go1.27.1"
# Wave-1 root cause: curl without -L saved the 75-byte 302 page as the "tarball".
# Race the real endpoints; validate size + gzip magic before accepting.
URLS = [
    "https://dl.google.com/go/%s.linux-amd64.tar.gz" % VER,
    "https://go.dev/dl/%s.linux-amd64.tar.gz" % VER,
]
DST = os.path.expanduser("~/go-dl")
os.makedirs(DST, exist_ok=True)
def fetch(url):
    fn = os.path.join(DST, "w2race_" + url.split("//")[1].replace("/", "_"))
    req = urllib.request.Request(url, headers={"User-Agent": "round4-racer/2.0"})
    with urllib.request.urlopen(req, timeout=240) as r, open(fn, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    return fn
def valid(fn):
    try:
        return os.path.getsize(fn) > 50_000_000 and open(fn, "rb").read(2) == b"\x1f\x8b"
    except Exception:
        return False
async def main():
    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(None, fetch, u) for u in URLS]
    winner = None
    try:
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED, timeout=540)
        for t in done:
            try:
                fn = t.result()
                print("candidate:", fn, os.path.getsize(fn))
                if valid(fn):
                    winner = fn
                    break
            except Exception as e:
                print("candidate failed:", e)
        if not winner:
            for t in pending:
                try:
                    fn = await asyncio.wait_for(asyncio.wrap_future(t), 300)
                    print("candidate:", fn, os.path.getsize(fn))
                    if valid(fn):
                        winner = fn
                        break
                except Exception as e:
                    print("candidate failed:", e)
    finally:
        for t in tasks:
            t.cancel()
    assert winner, "no valid toolchain tarball from any mirror"
    sdk = os.path.expanduser("~/sdk")
    os.makedirs(sdk, exist_ok=True)
    print("extracting", winner)
    with tarfile.open(winner) as tf:
        tf.extractall(sdk)
    open(os.path.join(sdk, ".w2_go_ver"), "w").write(VER + " from " + winner + "\n")
    print("GO_TOOLCHAIN_RACED", VER, winner)
asyncio.get_event_loop().run_until_complete(main())
PYEOF

#!/usr/bin/env python3
"""R5F3: environment audit — list endpoint/api_base/model env vars with values
redacted, then check hatch config dir. Prints PASS."""
import os
from pathlib import Path

def main():
    hits = [f"{k}=<redacted>" for k in os.environ
            if any(s in k.lower() for s in ("endpoint", "api_base", "model"))]
    print("\n".join(hits) if hits else "(no matching env vars)")
    print("---")
    cfg = Path("/home/hatch/.config/hatch")
    print("config dir:", "present" if cfg.is_dir() else "absent")
    print("PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

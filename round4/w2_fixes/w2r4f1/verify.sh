#!/bin/bash
set -uo pipefail

python3 - <<'PYEOF'
import nest_asyncio, asyncio
nest_asyncio.apply()
async def inner():
    return 7
async def outer():
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(inner())  # nested loop: fails without the patch
result = asyncio.get_event_loop().run_until_complete(outer())
assert result == 7, result
print("NESTED_LOOP_OK", result)
PYEOF

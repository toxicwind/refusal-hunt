#!/bin/bash
set -uo pipefail

python3 -c "
import nest_asyncio, asyncio
nest_asyncio.apply()
async def m(): return 42
loop = asyncio.new_event_loop()
assert loop.run_until_complete(m()) == 42
print('NEST_ASYNCIO_OK')
"

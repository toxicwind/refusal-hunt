#!/usr/bin/env python3
"""One-shot: manifest fixes — R6F2 must run on the PC (bridge), not the cell."""
import io
import json
import shutil

p = '/home/hatch/workspace/refusal-hunt/round3/rounds_manifest.json'
shutil.copy2(p, p + '.bak-r6f2')
m = json.load(io.open(p, encoding='utf-8'))

changed = 0
for r in m['rounds']:
    for f in r['fixes']:
        if f['id'] == 'R6F2':
            kind = f['kind']
            assert kind == 'cell', 'unexpected kind ' + kind
            f['kind'] = 'bridge'
            f['verify']['kind'] = 'bridge'
            f['note'] = ('2026-09-16: routed via bridge — run references '
                         '/home/toxic path which exists only on awrawr-pc')
            changed += 1

assert changed == 1, f'changed={changed}'
io.open(p, 'w', encoding='utf-8').write(json.dumps(m, indent=1) + '\n')
print('manifest patched: R6F2 -> bridge')

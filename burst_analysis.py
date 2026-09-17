import json, subprocess
from datetime import datetime, timezone

REFUSAL_MD5 = "b4aefd29108f232f9c0d5a4b030215c1"

rows = [
(340,"d3d16d8bffb4bd8f0f7cf7245b66fccc",4995,1789443685),(341,"e880c85b367c74d326a059bc29254945",14648,1789443711),
(342,"a3c919e373053aeb199d39d66e8c5572",7539,1789443711),(343,"f13ca0bae692be8c6797a2c2ee6ef3e4",4711,1789443711),
(344,"40641c7c1188596c25ce20a51c7d2a44",3420,1789443788),(345,"8426276d1974a390679402b41d2054b8",2738,1789443827),
(346,"f76a8fac5a38be5868a5d3704dfec0d9",4035,1789443848),(347,"d57dd3867db95a8a0ec1fec6e2afa1ab",1876,1789443918),
(348,"43768bb9cc675e13ee42c35b66475df7",4599,1789443954),(349,"e885c6f7b9cb4d078b4e7bd8b9fdaf6c",3621,1789444070),
(350,"848683a72cca34fd59009346296d3854",3175,1789444070),(351,"028d291a12003436050e116e2bf42cd2",3391,1789444078),
(352,"6b819e458e16c4e97ea391cf9fafef4c",2920,1789444084),(353,"a3d60141e63fb6ba4cabf73815add2d2",4830,1789444099),
(354,"f39fb06225fa7ed2141905a2afb4292a",2942,1789444099),(355,"98ca84bddb79803de2eec15f44cbc63c",3308,1789444099),
(356,"a82639ae28ca242f1bc6e9c5d643c5b8",2612,1789444183),(357,"183a0c5edb4ac453037cf2da35e1c04d",3497,1789444254),
(358,"38444202f47ee6bdb44b98304faec404",2236,1789444551),(359,"ee5180a161a3325080adaa62bdd8569a",4030,1789444572),
(360,"983f6247babf38498a540766d2133bb4",824,1789444624),(361,"1ca6042923bcb1bcc0a463c3ebc1926d",5327,1789444684),
(362,"f600832f57c7231197445936dbaf3f69",1133,1789444716),(363,"00dd664295308447640000a9fb6ba821",3263,1789444938),
(364,"fc59b60739ee73e175313299f6ca60b9",3856,1789445223),
]
refused_extra = [365,367,368,369,370,371,372,373,374,377,378,379,380,381,382,383,384,385,386,387,388,389,390,391,
                 392,393,394,395,396,397,398,399,400,401,408,409,410,411,412,413,414,415,416,417,418,419,420,421,422,423,424]
refused_times = {365:1789445368,367:1789446004,368:1789446219,369:1789446356,370:1789446356,371:1789452623,372:1789452623,
373:1789452623,374:1789452666,377:1789454037,378:1789454037,379:1789454037,380:1789454037,381:1789454037,382:1789454037,
383:1789454122,384:1789454266,385:1789454438,386:1789455590,387:1789455590,388:1789455591,389:1789455619,390:1789455619,
391:1789455690,392:1789527691,393:1789529838,394:1789529856,395:1789530101,396:1789530268,397:1789531173,398:1789531378,
399:1789531378,400:1789531479,401:1789532043,408:1789533815,409:1789533815,410:1789533816,411:1789534524,412:1789535184,
413:1789535236,414:1789535263,415:1789535263,416:1789535263,417:1789535263,418:1789535263,419:1789535263,420:1789535263,
421:1789535263,422:1789535372,423:1789535397,424:1789535474}
for sid in refused_extra:
    rows.append((sid, REFUSAL_MD5, 384, refused_times[sid]))
rows += [(366,"a2b9a2c4b8d21a732197a14df9a3f43e",3921,1789445483),
         (375,"016ec0e7b69b0c00d4aa0514ac01409b",3303,1789452693),
         (376,"905aab4830d4444252224e14b992b459",1431,1789453484),
         (402,"6fdb087aa3fbfbcb8287a593a0919e61",4,1789532981),
         (403,"6fdb087aa3fbfbcb8287a593a0919e61",4,1789532991),
         (404,"6fdb087aa3fbfbcb8287a593a0919e61",4,1789532991),
         (405,"6fdb087aa3fbfbcb8287a593a0919e61",4,1789532991),
         (406,"6fdb087aa3fbfbcb8287a593a0919e61",4,1789533074),
         (407,"7832d402b624a0065e76cc87778148f5",623,1789533332)]
rows.sort()
n = len(rows)
refused = [r for r in rows if r[1] == REFUSAL_MD5]
genuine = [r for r in rows if r[1] != REFUSAL_MD5]
print(f"window: sid 340..424 (n={n})")
print(f"refused: {len(refused)} ({100*len(refused)/n:.1f}%)  genuine: {len(genuine)}")
t0 = datetime.fromtimestamp(rows[0][3], tz=timezone.utc)
t1 = datetime.fromtimestamp(rows[-1][3], tz=timezone.utc)
print(f"window UTC: {t0:%Y-%m-%d %H:%M} -> {t1:%Y-%m-%d %H:%M}")
print(f"storm onset: sid 365 @ {datetime.fromtimestamp(1789445368, tz=timezone.utc):%H:%M UTC}")

# burst / clear-window runs
runs, cur = [], [rows[0]]
for r in rows[1:]:
    if (r[1] == REFUSAL_MD5) == (cur[0][1] == REFUSAL_MD5):
        cur.append(r)
    else:
        runs.append(cur); cur = [r]
runs.append(cur)
print("\nruns (R=refusal burst, G=genuine run):")
for run in runs:
    is_r = run[0][1] == REFUSAL_MD5
    a, b = run[0][3], run[-1][3]
    dur = (b - a) / 60
    print(f"  {'R' if is_r else 'G'} x{len(run):2d}  sids {run[0][0]}..{run[-1][0]}  dur {dur:7.1f} min  "
          f"{datetime.fromtimestamp(a, tz=timezone.utc):%m-%d %H:%M}->{datetime.fromtimestamp(b, tz=timezone.utc):%H:%M} UTC")

# clear windows list
print("\nclear windows (genuine spawns inside storm period, sid>=365):")
for r in genuine:
    if r[0] >= 365:
        print(f"  sid {r[0]} @ {datetime.fromtimestamp(r[3], tz=timezone.utc):%m-%d %H:%M} UTC  len={r[2]}")

# burst lethality: P(refused | previous k were refused) for the storm period
storm = [r for r in rows if r[0] >= 365]
for k in (1, 3, 5):
    tot = hit = 0
    for i in range(k, len(storm)):
        if all(storm[j][1] == REFUSAL_MD5 for j in range(i-k, i)):
            tot += 1
            hit += storm[i][1] == REFUSAL_MD5
    print(f"P(refused | prev {k} refused) = {hit}/{tot} = {100*hit/max(tot,1):.1f}%")

json.dump([{"sid": s, "refused": h == REFUSAL_MD5, "created": c} for s, h, _, c in rows],
          open("/home/hatch/workspace/refusal-hunt/spawn-bursts-20260916.json", "w"), indent=1)
print("\nwrote /home/hatch/workspace/refusal-hunt/spawn-bursts-20260916.json")

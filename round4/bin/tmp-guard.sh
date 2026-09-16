#!/bin/bash
# tmp-guard: observe /tmp pressure (R1 = observe only, no deletes).
pct=$(df /tmp | awk 'NR==2{print $5}' | tr -d '%')
echo "tmp_usage_pct=$pct"
du -x /tmp 2>/dev/null | sort -rn | head -5 | awk '{print "top_consumer_bytes="$1" path="$2}'
[ "$pct" -ge 85 ] && { echo "ALERT: /tmp >= 85%"; exit 2; }
exit 0

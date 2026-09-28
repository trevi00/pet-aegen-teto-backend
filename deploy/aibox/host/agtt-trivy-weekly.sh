#!/usr/bin/env bash
# agttpet.com 운영 이미지 주간 취약점 스캔 (systemd agtt-trivy-weekly.timer)
# 결과: ~/apps/agtt/security-reports/YYYY-MM-DD.txt (최근 12개 유지)
# 첫 줄이 "조치 필요" 면 수정판이 있는 HIGH/CRITICAL 이 생긴 것 → 의존성·base digest 갱신 후 재빌드
set -euo pipefail

HOME_DIR=/home/trevi
OUT_DIR="$HOME_DIR/apps/agtt/security-reports"
REPORT="$OUT_DIR/$(date +%F).txt"
mkdir -p "$OUT_DIR"

images=(agtt-backend agtt-web "$(docker inspect -f '{{.Config.Image}}' agtt-tunnel-1)")
fixable_total=0
body=""
for img in "${images[@]}"; do
  json=$(docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v "$HOME_DIR/.cache/trivy:/root/.cache/" \
    aquasec/trivy:latest image --quiet --scanners vuln --format json "$img" 2>/dev/null || echo '{}')
  line=$(python3 -c '
import json, sys
from collections import Counter
d = json.loads(sys.stdin.read() or "{}")
v = [x for r in d.get("Results", []) for x in (r.get("Vulnerabilities") or [])]
sev = Counter(x["Severity"] for x in v)
fx = [x for x in v if x["Severity"] in ("HIGH", "CRITICAL") and x.get("FixedVersion")]
print(len(fx), dict(sev), sorted({x["PkgName"] for x in fx})[:10])
' <<<"$json")
  n=${line%% *}
  fixable_total=$((fixable_total + n))
  body+="$img: 수정 가능 HIGH/CRITICAL ${line}"$'\n'
done

{
  if [ "$fixable_total" -gt 0 ]; then echo "조치 필요: 수정 가능한 HIGH/CRITICAL ${fixable_total}건"; else echo "이상 없음: 수정 가능한 HIGH/CRITICAL 0건"; fi
  echo "스캔 시각: $(date -Is)"
  printf '%s' "$body"
} > "$REPORT"
chown -R trevi:trevi "$OUT_DIR"

# 최근 12개만 유지
ls -1t "$OUT_DIR"/*.txt | tail -n +13 | xargs -r rm -f
head -1 "$REPORT"

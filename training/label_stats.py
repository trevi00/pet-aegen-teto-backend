"""labels.csv 분포 점검: 세 신호가 실제로 흔들리는지, 품종 부호와 다른 라벨이 얼마나 되는지."""
import csv
import statistics as st
import sys
from collections import Counter, defaultdict

rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))


def col(k):
    return [float(r[k]) for r in rows]


for k in ("breed_score", "pose_score", "age_score", "final"):
    v = col(k)
    print(f"{k:12s} mean={st.mean(v):+.3f} sd={st.pstdev(v):.3f} min={min(v):+.2f} max={max(v):+.2f}")

flip = sum(1 for r in rows if float(r["breed_score"]) != 0 and (float(r["breed_score"]) > 0) != (r["label"] == "teto"))
print("label differs from breed sign:", flip)
print("p_young>0.5:", sum(float(r["p_young"]) > .5 for r in rows), " p_senior>0.5:", sum(float(r["p_senior"]) > .5 for r in rows))

by = defaultdict(Counter)
for r in rows:
    by[r["breed"]][r["label"]] += 1
    by[r["breed"]]["review"] += int(r["needs_review"])
for b in sorted(by, key=lambda x: -by[x]["review"])[:12]:
    c = by[b]
    print(f"{b:28s} aegen={c['aegen']:3d} teto={c['teto']:3d} review={c['review']:3d}")

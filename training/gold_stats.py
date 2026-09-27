"""정답 세트(사람 판정) vs 자동 라벨 일치도."""
import csv
import json
import pathlib
import sys
from collections import Counter

root = pathlib.Path(sys.argv[1]).expanduser()
labels = {r["file"]: r for r in csv.DictReader((root / "labels.csv").open(encoding="utf-8"))}
gold = json.loads((root / "gold_set.json").read_text(encoding="utf-8"))
done = {}
for r in csv.DictReader((root / "reviews.csv").open(encoding="utf-8")):
    if r["verdict"] == "undo":
        done.pop(r["file"], None)
    else:
        done[r["file"]] = r["verdict"]

v = Counter(done.values())
print(f"reviewed {len(done)}/{len(gold)} | aegen {v['aegen']} teto {v['teto']} skip {v['skip']}")
judged = [(f, h) for f, h in done.items() if h in ("aegen", "teto")]
agree = sum(labels[f]["label"] == h for f, h in judged)
print(f"auto label agrees with human: {agree}/{len(judged)} = {agree / len(judged):.1%}")
conf = [(f, h) for f, h in judged if labels[f]["needs_review"] == "0"]
rev = [(f, h) for f, h in judged if labels[f]["needs_review"] == "1"]
for name, part in (("confident", conf), ("borderline", rev)):
    a = sum(labels[f]["label"] == h for f, h in part)
    print(f"  {name:10s}: {a}/{len(part)} = {a / max(len(part), 1):.1%}")
# 사람 판정을 가장 잘 설명하는 신호
for k in ("breed_score", "pose_score", "age_score", "final"):
    a = sum((float(labels[f][k]) > 0) == (h == "teto") for f, h in judged)
    print(f"  sign({k}) vs human: {a / len(judged):.1%}")
mis = Counter(labels[f]["breed"] for f, h in judged if labels[f]["label"] != h)
print("most disagreed breeds:", mis.most_common(8))

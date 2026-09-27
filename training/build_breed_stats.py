"""per_image.csv(서비스 경로 점수) → 웹의 src/content/breeds.json + 품종 대표 썸네일.

대표 사진 = 그 품종에서 점수가 중앙값에 가장 가까운 사진 (가장 극단적인 사진을 고르지 않는다).
썸네일은 Oxford-IIIT Pet Dataset(CC BY-SA 4.0) 사진을 줄인 것 — 페이지에 출처·라이선스를 표기한다.
"""
import csv
import json
import os
import statistics

from PIL import Image

HOME = os.path.expanduser("~/apps/agtt")
DATA = f"{HOME}/data/oxford-pets"
WEB = f"{HOME}/pet-aegen-teto-web"
META = json.load(open("os.path.join(os.path.dirname(__file__), "breeds_meta.json")", encoding="utf-8"))
TYPES = [("pure-aegen", 80), ("aegen", 60), ("balanced", 40), ("teto", 20), ("pure-teto", -1)]


def type_of(p):
    return next(slug for slug, lo in TYPES if p >= lo)


known = {r["breed"].lower(): r for r in csv.DictReader(open(f"{HOME}/pet-aegen-teto-backend/training/breed_temperament.csv", encoding="utf-8"))}
rows = list(csv.DictReader(open(f"{DATA}/per_image.csv", encoding="utf-8")))
by = {}
for r in rows:
    by.setdefault(r["breed"].lower(), []).append((float(r["aegen_pct"]), r["file"], r["species"]))

os.makedirs(f"{WEB}/public/images/breeds", exist_ok=True)
out = []
for key, items in sorted(by.items()):
    scores = [s for s, _, _ in items]
    med = statistics.median(scores)
    rep = min(items, key=lambda x: abs(x[0] - med))
    slug = key.replace("_", "-")
    im = Image.open(f"{DATA}/images/{rep[1]}").convert("RGB")
    im.thumbnail((480, 480))
    im.save(f"{WEB}/public/images/breeds/{slug}.webp", "WEBP", quality=78)
    dist = {t: 0 for t, _ in TYPES}
    for s in scores:
        dist[type_of(s)] += 1
    m = META[key]
    out.append({
        "key": key, "slug": slug, "ko": m["ko"], "species": items[0][2], "intro": m["intro"],
        "known": known[key]["reason"], "knownScore": float(known[key]["score"]),
        "n": len(scores), "mean": round(statistics.fmean(scores), 1), "median": round(med, 1),
        "aegenShare": round(100 * sum(s >= 50 for s in scores) / len(scores), 1),
        "dist": dist, "rep": {"file": rep[1], "score": rep[0], "image": f"/images/breeds/{slug}.webp"},
    })

# 알려진 성향 점수(-1 차분 ~ +1 활발)와 AI 평균 에겐 비율의 상관 — 페이지에 "잰 것" 으로 보여 준다
xs = [b["knownScore"] for b in out]
ys = [b["mean"] for b in out]
r = statistics.correlation(xs, ys)
summary = {
    "images": len(rows), "breeds": len(out),
    "cats": sum(b["n"] for b in out if b["species"] == "cat"),
    "dogs": sum(b["n"] for b in out if b["species"] == "dog"),
    "meanCat": round(statistics.fmean(float(r_["aegen_pct"]) for r_ in rows if r_["species"] == "cat"), 1),
    "meanDog": round(statistics.fmean(float(r_["aegen_pct"]) for r_ in rows if r_["species"] == "dog"), 1),
    "overallDist": {t: sum(b["dist"][t] for b in out) for t, _ in TYPES},
    "knownVsAiPearson": round(r, 2),
}
json.dump({"summary": summary, "breeds": out}, open(f"{WEB}/src/content/breeds.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(summary, ensure_ascii=False))
for b in sorted(out, key=lambda b: -b["mean"]):
    print(f'{b["ko"]:<16} {b["species"]} n={b["n"]:<4} mean={b["mean"]:<5} known={b["knownScore"]:+.1f} dist={list(b["dist"].values())}')

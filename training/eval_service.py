"""컨테이너 안에서 실제 서비스 분석 경로(AnalyzerService)로 홀드아웃 정확도를 잰다."""
import json
import math
import sys

sys.path.insert(0, "/app")
from app.ai.classifier import AegenTetoClassifier  # noqa: E402
from app.ai.ensemble_analyzer import EnsembleAnalyzer  # noqa: E402
from app.services.analyzer_service import AnalyzerService  # noqa: E402

items = json.load(open("/tmp/eval/holdout.json", encoding="utf-8"))
svc = AnalyzerService(EnsembleAnalyzer(), AegenTetoClassifier())
ens = cus = blip = 0
for it in items:
    r = svc.analyze_image(f"/tmp/eval/{it['file']}")
    info = r.get("ensemble_info", {})
    ens += r["classification"] == it["label"]
    cus += info.get("custom_prediction") == it["label"]
    blip += info.get("blip_prediction") == it["label"]
n = len(items)


def wilson(k):
    p, z = k / n, 1.96
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return f"{k}/{n} = {k / n:.1%} (95% {c - h:.0%}~{c + h:.0%})"


print("service ensemble:", wilson(ens))
print("custom only     :", wilson(cus))
print("blip only       :", wilson(blip))

"""데이터셋 전체(7,349장)를 실제 서비스 분석 경로(AnalyzerService)로 점수 매긴다 → per_image.csv
품종별 통계 페이지의 원자료. 서비스와 같은 코드·가중치·온도를 쓴다."""
import csv
import os
import sys
import time

BACKEND = os.path.expanduser("~/apps/agtt/pet-aegen-teto-backend")
DATA = os.path.expanduser("~/apps/agtt/data/oxford-pets")
OUT = os.path.expanduser("~/apps/agtt/data/oxford-pets/per_image.csv")
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 0

os.chdir(BACKEND)
sys.path.insert(0, BACKEND)
# app/__init__.py 는 Flask 앱을 만든다 — 분석 모듈만 쓰므로 패키지 껍데기만 등록해 건너뛴다
import types  # noqa: E402
_pkg = types.ModuleType("app")
_pkg.__path__ = [os.path.join(BACKEND, "app")]
sys.modules["app"] = _pkg
_svc = types.ModuleType("app.services")  # services/__init__ 도 웹 의존(werkzeug)을 끌어온다
_svc.__path__ = [os.path.join(BACKEND, "app", "services")]
sys.modules["app.services"] = _svc
from app.ai.classifier import AegenTetoClassifier  # noqa: E402
from app.ai.ensemble_analyzer import EnsembleAnalyzer  # noqa: E402
from app.services.analyzer_service import AnalyzerService  # noqa: E402

rows = list(csv.DictReader(open(os.path.join(DATA, "labels.csv"), encoding="utf-8")))
if LIMIT:
    rows = rows[:LIMIT]
svc = AnalyzerService(EnsembleAnalyzer(), AegenTetoClassifier())

t0 = time.time()
with open(OUT if not LIMIT else OUT + ".sample", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["file", "breed", "species", "aegen_pct", "pred_breed", "breed_prob", "pose"])
    for i, r in enumerate(rows, 1):
        res = svc.analyze_image(os.path.join(DATA, "images", r["file"]))
        bm = res.get("breed_match") or {}
        w.writerow([r["file"], r["breed"], r["species"], res["aegen_percentage"],
                    bm.get("key", ""), bm.get("prob", ""), res["pose"]])
        if i % 500 == 0:
            print(f"{i}/{len(rows)} {time.time() - t0:.0f}s", flush=True)
print(f"done {len(rows)} in {time.time() - t0:.0f}s")

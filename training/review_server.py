"""에겐/테토 정답 세트 검수 화면 (표준 라이브러리만, 127.0.0.1 전용).

- 품종마다 PER_BREED 장 + 부족분을 무작위(고정 시드)로 뽑아 TOTAL 장을 만든다.
- 자동 라벨·점수는 보여주지 않는다 (앵커링 방지). 품종 이름만 보여준다.
- 키보드: A=에겐, T=테토, S=건너뛰기, Z=되돌리기. 판정은 reviews.csv 에 즉시 append.
"""
import csv
import html
import json
import pathlib
import random
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = pathlib.Path(sys.argv[1]).expanduser()
IMG = ROOT / "images"
LABELS = ROOT / "labels.csv"
GOLD = ROOT / "gold_set.json"
REVIEWS = ROOT / "reviews.csv"
PER_BREED, TOTAL, SEED = 8, 300, 20260927


def build_gold():
    if GOLD.exists():
        return json.loads(GOLD.read_text(encoding="utf-8"))
    rows = list(csv.DictReader(LABELS.open(encoding="utf-8")))
    rng = random.Random(SEED)
    by = {}
    for r in rows:
        by.setdefault(r["breed"], []).append(r)
    pick = []
    for b in sorted(by):
        pick += rng.sample(by[b], min(PER_BREED, len(by[b])))
    chosen = {r["file"] for r in pick}
    rest = [r for r in rows if r["file"] not in chosen]
    pick += rng.sample(rest, TOTAL - len(pick))
    rng.shuffle(pick)
    gold = [{"file": r["file"], "breed": r["breed"], "species": r["species"]} for r in pick]
    GOLD.write_text(json.dumps(gold, ensure_ascii=False, indent=1), encoding="utf-8")
    return gold


def load_reviews():
    done = {}
    if REVIEWS.exists():
        for r in csv.DictReader(REVIEWS.open(encoding="utf-8")):
            if r["verdict"] == "undo":
                done.pop(r["file"], None)
            else:
                done[r["file"]] = r["verdict"]
    return done


def append_review(file, verdict):
    new = not REVIEWS.exists()
    with REVIEWS.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["file", "verdict"])
        w.writerow([file, verdict])


GOLD_LIST = build_gold()
GOLD_FILES = {g["file"] for g in GOLD_LIST}
BREED_KO = {}

PAGE = """<!doctype html><html lang="ko"><meta charset="utf-8"><title>에겐/테토 검수</title>
<style>
body{{margin:0;font-family:system-ui,'Malgun Gothic',sans-serif;background:#111;color:#eee;display:flex;flex-direction:column;align-items:center}}
header{{padding:12px;font-size:15px;color:#aaa}} b{{color:#fff}}
img{{max-width:92vw;max-height:68vh;border-radius:8px;margin:8px 0}}
.breed{{font-size:22px;margin:4px}} .keys{{display:flex;gap:12px;margin:12px}}
button{{font-size:18px;padding:12px 22px;border:0;border-radius:8px;cursor:pointer}}
.a{{background:#6d8cff;color:#fff}} .t{{background:#ff7a45;color:#fff}} .s{{background:#444;color:#ddd}} .z{{background:#222;color:#999}}
.def{{font-size:13px;color:#999;max-width:640px;text-align:center}}
</style>
<header>진행 <b>{done}</b> / {total} · 에겐 {na} · 테토 {nt} · 건너뜀 {ns}</header>
{body}
<p class="def">기준: 품종 성향 &gt; 차분한 모습 &gt; 나이 · 에겐 = 차분·신중·매력적 / 테토 = 활발·적극·야성적</p>
<script>
const f={file};
function go(v){{ if(!f && v!=='undo') return; location.href='/vote?f='+encodeURIComponent(f||'')+'&v='+v; }}
document.addEventListener('keydown',e=>{{const k=e.key.toLowerCase();
 if(k==='a')go('aegen'); else if(k==='t')go('teto'); else if(k==='s')go('skip'); else if(k==='z')go('undo');}});
</script></html>"""


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        if u.path == "/img":
            name = pathlib.Path(q.get("f", [""])[0]).name  # 경로 조작 차단
            if name not in GOLD_FILES:
                return self._send(404, "not found", "text/plain")
            return self._send(200, (IMG / name).read_bytes(), "image/jpeg")
        if u.path == "/vote":
            f, v = q.get("f", [""])[0], q.get("v", [""])[0]
            if v == "undo":
                done = load_reviews()
                last = None
                if REVIEWS.exists():
                    for r in csv.DictReader(REVIEWS.open(encoding="utf-8")):
                        if r["verdict"] != "undo" and r["file"] in done:
                            last = r["file"]
                if last:
                    append_review(last, "undo")
            elif f in GOLD_FILES and v in ("aegen", "teto", "skip"):
                append_review(f, v)
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
            return
        if u.path == "/":
            done = load_reviews()
            nxt = next((g for g in GOLD_LIST if g["file"] not in done), None)
            if nxt:
                body = (f'<img src="/img?f={urllib.parse.quote(nxt["file"])}" alt="">'
                        f'<div class="breed">{html.escape(nxt["breed"].replace("_", " "))} · {"고양이" if nxt["species"] == "cat" else "개"}</div>'
                        '<div class="keys"><button class="a" onclick="go(\'aegen\')">A 에겐</button>'
                        '<button class="t" onclick="go(\'teto\')">T 테토</button>'
                        '<button class="s" onclick="go(\'skip\')">S 건너뛰기</button>'
                        '<button class="z" onclick="go(\'undo\')">Z 되돌리기</button></div>')
                fjs = json.dumps(nxt["file"])
            else:
                body = '<div class="breed">검수 완료! 창을 닫으셔도 됩니다 🙌</div><div class="keys"><button class="z" onclick="go(\'undo\')">Z 마지막 되돌리기</button></div>'
                fjs = "null"
            vals = list(done.values())
            return self._send(200, PAGE.format(done=len(done), total=len(GOLD_LIST), na=vals.count("aegen"),
                                               nt=vals.count("teto"), ns=vals.count("skip"), body=body, file=fjs))
        self._send(404, "not found", "text/plain")


if __name__ == "__main__":
    print(f"gold set: {len(GOLD_LIST)} images, reviewed so far: {len(load_reviews())}")
    ThreadingHTTPServer(("127.0.0.1", 8090), H).serve_forever()

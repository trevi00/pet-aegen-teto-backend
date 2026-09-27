"""Oxford-IIIT Pet 에 에겐/테토 약한 라벨을 붙인다.

점수 = 0.6*품종 성향 + 0.3*차분한 모습(CLIP) + 0.1*나이(CLIP),  범위 -1(에겐) ~ +1(테토)
  에겐 = 차분·신중·매력적 / 테토 = 활발·적극·야성적
|점수| < REVIEW_MARGIN 이면 사람이 검수할 대상으로 표시한다.

출력: labels.csv (파일, 품종, 종, 세 신호, 최종 점수, 라벨, 검수 필요 여부)
"""
import csv
import pathlib
import sys

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "~/apps/agtt/data/oxford-pets").expanduser()
BREED_CSV = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "~/apps/agtt/labeling/breed_temperament.csv").expanduser()
OUT = ROOT / "labels.csv"
W_BREED, W_POSE, W_AGE = 0.6, 0.3, 0.1
REVIEW_MARGIN = 0.15
BATCH = 64

CALM = [
    "a photo of a calm, relaxed {s} lying down peacefully",
    "a photo of an elegant, graceful {s} with a gentle gaze",
    "a photo of a sleepy {s} resting quietly",
    "a photo of a dignified, charming {s} sitting still",
]
ACTIVE = [
    "a photo of an energetic {s} running or jumping",
    "a photo of a playful, excited {s} with its mouth open",
    "a photo of a wild, fierce-looking {s}",
    "a photo of an alert, bold {s} ready to pounce",
]
YOUNG = {"dog": "a photo of a puppy", "cat": "a photo of a kitten"}
ADULT = {"dog": "a photo of an adult dog", "cat": "a photo of an adult cat"}
SENIOR = {"dog": "a photo of an old senior dog with a grey muzzle", "cat": "a photo of an old senior cat"}


def _feat(o):
    # transformers 5.x 는 BaseModelOutputWithPooling 을 돌려주고 pooler_output 이 투영 임베딩이다
    return o if torch.is_tensor(o) else o.pooler_output


def load_breeds():
    with BREED_CSV.open(encoding="utf-8") as f:
        return {r["breed"].lower(): (r["species"], float(r["score"])) for r in csv.DictReader(f)}


def main():
    breeds = load_breeds()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    name = "openai/clip-vit-large-patch14"
    model = CLIPModel.from_pretrained(name, torch_dtype=torch.float16 if device == "cuda" else torch.float32).to(device).eval()
    proc = CLIPProcessor.from_pretrained(name)

    def text_emb(texts):
        t = proc(text=texts, return_tensors="pt", padding=True).to(device)
        with torch.no_grad():
            e = model.get_text_features(**t)
        return torch.nn.functional.normalize(_feat(e).float(), dim=-1)

    prompts = {}
    for sp in ("dog", "cat"):
        prompts[sp] = {
            "calm": text_emb([p.format(s=sp) for p in CALM]),
            "active": text_emb([p.format(s=sp) for p in ACTIVE]),
            "age": text_emb([YOUNG[sp], ADULT[sp], SENIOR[sp]]),
        }
    scale = model.logit_scale.exp().float()

    files = sorted((ROOT / "images").glob("*.jpg"))
    rows, skipped = [], 0
    for i in range(0, len(files), BATCH):
        chunk, imgs, meta = files[i:i + BATCH], [], []
        for p in chunk:
            breed = p.stem.rsplit("_", 1)[0].lower()
            if breed not in breeds:
                skipped += 1
                continue
            try:
                imgs.append(Image.open(p).convert("RGB"))
            except Exception:
                skipped += 1
                continue
            meta.append((p, breed))
        if not imgs:
            continue
        x = proc(images=imgs, return_tensors="pt").to(device)
        with torch.no_grad():
            ie = torch.nn.functional.normalize(_feat(model.get_image_features(**x)).float(), dim=-1)
        for j, (p, breed) in enumerate(meta):
            sp, b = breeds[breed]
            e = ie[j]
            calm = (scale * e @ prompts[sp]["calm"].T).mean()
            active = (scale * e @ prompts[sp]["active"].T).mean()
            p_active = torch.softmax(torch.stack([calm, active]), 0)[1].item()
            pose = 2 * p_active - 1                      # -1 차분 ~ +1 활발
            pa = torch.softmax(scale * e @ prompts[sp]["age"].T, 0).tolist()
            age = pa[0] - pa[2]                          # 어림 +, 노령 -
            final = W_BREED * b + W_POSE * pose + W_AGE * age
            rows.append({
                "file": p.name, "breed": breed, "species": sp,
                "breed_score": round(b, 3), "pose_score": round(pose, 3), "age_score": round(age, 3),
                "p_young": round(pa[0], 3), "p_senior": round(pa[2], 3),
                "final": round(final, 3), "label": "teto" if final > 0 else "aegen",
                "needs_review": int(abs(final) < REVIEW_MARGIN),
            })
        print(f"{min(i + BATCH, len(files))}/{len(files)}", flush=True)

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    n = len(rows)
    teto = sum(r["label"] == "teto" for r in rows)
    rev = sum(r["needs_review"] for r in rows)
    print(f"done: {n} labeled, skipped {skipped} | teto {teto} / aegen {n - teto} | needs_review {rev} -> {OUT}")


if __name__ == "__main__":
    main()

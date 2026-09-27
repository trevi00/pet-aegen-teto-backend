"""사람 판정 300장이 배울 수 있을 만큼 일관적인지 확인.

1) 세 신호(breed/pose/age)로 로지스틱 회귀 → 5-fold CV 정확도, 학습된 가중치
2) CLIP ViT-L/14 이미지 임베딩(+종 표시)으로 로지스틱 회귀 → 5-fold CV 정확도
외부 의존성 없이 torch 로 로지스틱 회귀를 직접 푼다.
"""
import csv
import json
import pathlib
import random
import sys

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

root = pathlib.Path(sys.argv[1]).expanduser()
labels = {r["file"]: r for r in csv.DictReader((root / "labels.csv").open(encoding="utf-8"))}
done = {}
for r in csv.DictReader((root / "reviews.csv").open(encoding="utf-8")):
    if r["verdict"] == "undo":
        done.pop(r["file"], None)
    else:
        done[r["file"]] = r["verdict"]
items = [(f, 1.0 if v == "teto" else 0.0) for f, v in done.items() if v in ("aegen", "teto")]
random.Random(0).shuffle(items)
y = torch.tensor([t for _, t in items])


def fit_eval(X, folds=5, l2=1e-2, epochs=400):
    n = len(X)
    accs = []
    for k in range(folds):
        te = list(range(k, n, folds))
        tr = [i for i in range(n) if i % folds != k]
        mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-6
        Xtr, Xte = (X[tr] - mu) / sd, (X[te] - mu) / sd
        w = torch.zeros(X.shape[1], requires_grad=True)
        b = torch.zeros(1, requires_grad=True)
        opt = torch.optim.LBFGS([w, b], max_iter=epochs)

        def closure():
            opt.zero_grad()
            loss = torch.nn.functional.binary_cross_entropy_with_logits(Xtr @ w + b, y[tr]) + l2 * (w ** 2).sum()
            loss.backward()
            return loss

        opt.step(closure)
        pred = ((Xte @ w + b) > 0).float()
        accs.append((pred == y[te]).float().mean().item())
    return sum(accs) / len(accs), w.detach(), mu, sd


# 1) 세 신호
S = torch.tensor([[float(labels[f][k]) for k in ("breed_score", "pose_score", "age_score")] for f, _ in items])
acc, w, mu, sd = fit_eval(S)
print(f"[3 signals] 5-fold CV acc = {acc:.1%} | weights (standardized) breed={w[0]:+.2f} pose={w[1]:+.2f} age={w[2]:+.2f}")

# 2) CLIP 임베딩
device = "cuda" if torch.cuda.is_available() else "cpu"
name = "openai/clip-vit-large-patch14"
model = CLIPModel.from_pretrained(name, torch_dtype=torch.float16).to(device).eval()
proc = CLIPProcessor.from_pretrained(name)
feats = []
for i in range(0, len(items), 64):
    imgs = [Image.open(root / "images" / f).convert("RGB") for f, _ in items[i:i + 64]]
    x = proc(images=imgs, return_tensors="pt").to(device)
    with torch.no_grad():
        o = model.get_image_features(**x)
    o = o if torch.is_tensor(o) else o.pooler_output
    feats.append(torch.nn.functional.normalize(o.float(), dim=-1).cpu())
E = torch.cat(feats)
sp = torch.tensor([[1.0 if labels[f]["species"] == "dog" else 0.0] for f, _ in items])
for l2 in (1e-1, 1e-2, 1e-3):
    acc2, *_ = fit_eval(torch.cat([E, sp], 1), l2=l2)
    print(f"[CLIP embedding, l2={l2}] 5-fold CV acc = {acc2:.1%}")
acc3, *_ = fit_eval(torch.cat([E, sp, S], 1), l2=1e-2)
print(f"[CLIP + 3 signals] 5-fold CV acc = {acc3:.1%}")
print(f"majority baseline = {max(y.mean().item(), 1 - y.mean().item()):.1%}")
torch.save({"files": [f for f, _ in items], "y": y, "E": E, "S": S, "sp": sp}, root / "gold_features.pt")

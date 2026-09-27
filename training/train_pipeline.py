"""경수님 판정(정답 세트)을 기준으로 서비스용 ResNet50 을 학습한다.

1. 정답 300장 → 홀드아웃 60장(끝까지 안 씀) + 취향 모델 학습 240장
2. 취향 모델 = CLIP ViT-L/14 임베딩 + 종 + 세 신호 → 로지스틱 회귀
3. 취향 모델로 나머지 이미지에 라벨(확신 높은 것만) → ResNet50 파인튜닝
4. 홀드아웃 60장으로 ResNet / 취향 모델 정확도(윌슨 95% 구간) 보고
출력: models/trained_model_v2.pth (서비스 형식: resnet50, fc=2, 0=aegen 1=teto), models/report.json
"""
import csv
import json
import math
import pathlib
import random
import sys

import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms
from transformers import CLIPModel, CLIPProcessor

ROOT = pathlib.Path(sys.argv[1]).expanduser()
OUTDIR = pathlib.Path(sys.argv[2]).expanduser()
OUTDIR.mkdir(parents=True, exist_ok=True)
SEED, HOLDOUT, CONF = 20260927, 60, 0.65
EPOCHS, BS, LR = 10, 64, 1e-4
dev = "cuda"
torch.manual_seed(SEED)
random.seed(SEED)

labels = {r["file"]: r for r in csv.DictReader((ROOT / "labels.csv").open(encoding="utf-8"))}
G = torch.load(ROOT / "gold_features.pt")
files, y, E, S, sp = G["files"], G["y"], G["E"], G["S"], G["sp"]

# 1) 홀드아웃: 라벨 비율을 맞춰 60장
idx0 = [i for i in range(len(files)) if y[i] == 0]
idx1 = [i for i in range(len(files)) if y[i] == 1]
rng = random.Random(SEED)
rng.shuffle(idx0)
rng.shuffle(idx1)
h0 = round(HOLDOUT * len(idx0) / len(files))
hold = set(idx0[:h0] + idx1[:HOLDOUT - h0])
tr = [i for i in range(len(files)) if i not in hold]
ho = sorted(hold)
print(f"gold: train {len(tr)}, holdout {len(ho)} (teto {int(y[ho].sum())})")


def feats(E, sp, S):
    return torch.cat([E, sp, S], 1)


X = feats(E, sp, S)
mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-6
w = torch.zeros(X.shape[1], requires_grad=True)
b = torch.zeros(1, requires_grad=True)
opt = torch.optim.LBFGS([w, b], max_iter=500)


def closure():
    opt.zero_grad()
    loss = nn.functional.binary_cross_entropy_with_logits(((X[tr] - mu) / sd) @ w + b, y[tr]) + 1e-2 * (w ** 2).sum()
    loss.backward()
    return loss


opt.step(closure)
w, b = w.detach(), b.detach()


def taste_prob(Xn):
    return torch.sigmoid(((Xn - mu) / sd) @ w + b)


# 2) 전체 이미지 CLIP 임베딩 → 취향 모델 라벨
clip = CLIPModel.from_pretrained("openai/clip-vit-large-patch14", torch_dtype=torch.float16).to(dev).eval()
proc = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14")
gold_files = set(files)
pool = [f for f in labels if f not in gold_files]
pseudo = []
for i in range(0, len(pool), 128):
    chunk = pool[i:i + 128]
    imgs = [Image.open(ROOT / "images" / f).convert("RGB") for f in chunk]
    x = proc(images=imgs, return_tensors="pt").to(dev)
    with torch.no_grad():
        o = clip.get_image_features(**x)
    o = o if torch.is_tensor(o) else o.pooler_output
    e = nn.functional.normalize(o.float(), dim=-1).cpu()
    s = torch.tensor([[float(labels[f][k]) for k in ("breed_score", "pose_score", "age_score")] for f in chunk])
    spc = torch.tensor([[1.0 if labels[f]["species"] == "dog" else 0.0] for f in chunk])
    p = taste_prob(feats(e, spc, s))
    for f, pp in zip(chunk, p.tolist()):
        if pp >= CONF or pp <= 1 - CONF:
            pseudo.append((f, int(pp >= 0.5)))
del clip
torch.cuda.empty_cache()
n_teto = sum(t for _, t in pseudo)
print(f"pseudo labels: {len(pseudo)} of {len(pool)} (teto {n_teto} / aegen {len(pseudo) - n_teto})")

# 3) ResNet50 파인튜닝
norm = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
t_train = transforms.Compose([transforms.RandomResizedCrop(224, scale=(0.7, 1.0)), transforms.RandomHorizontalFlip(),
                              transforms.ColorJitter(0.2, 0.2, 0.2), transforms.ToTensor(), norm])
t_eval = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(), norm])  # 서비스와 동일


class DS(torch.utils.data.Dataset):
    def __init__(self, items, tf):
        self.items, self.tf = items, tf

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        f, t = self.items[i]
        return self.tf(Image.open(ROOT / "images" / f).convert("RGB")), t


rng.shuffle(pseudo)
nval = len(pseudo) // 10
val_items, train_items = pseudo[:nval], pseudo[nval:]
dl_tr = torch.utils.data.DataLoader(DS(train_items, t_train), batch_size=BS, shuffle=True, num_workers=8, pin_memory=True)
dl_va = torch.utils.data.DataLoader(DS(val_items, t_eval), batch_size=BS, num_workers=8)
hold_items = [(files[i], int(y[i])) for i in ho]
dl_ho = torch.utils.data.DataLoader(DS(hold_items, t_eval), batch_size=BS, num_workers=4)

net = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
net.fc = nn.Linear(net.fc.in_features, 2)
net = net.to(dev)
cw = torch.tensor([len(pseudo) / (2 * (len(pseudo) - n_teto)), len(pseudo) / (2 * n_teto)], device=dev)
crit = nn.CrossEntropyLoss(weight=cw)
params = [{"params": [p for n, p in net.named_parameters() if not n.startswith("fc.")], "lr": LR},
          {"params": net.fc.parameters(), "lr": LR * 10}]
optim = torch.optim.AdamW(params, weight_decay=0.01)
sched = torch.optim.lr_scheduler.CosineAnnealingLR(optim, EPOCHS)
scaler = torch.amp.GradScaler()


def evaluate(dl):
    net.eval()
    c = n = 0
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16):
        for x, t in dl:
            p = net(x.to(dev)).argmax(1).cpu()
            c += (p == t).sum().item()
            n += len(t)
    return c / n


best, best_state = -1, None
for ep in range(EPOCHS):
    net.train()
    for x, t in dl_tr:
        x, t = x.to(dev, non_blocking=True), t.to(dev, non_blocking=True)
        optim.zero_grad(set_to_none=True)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            loss = crit(net(x), t)
        loss.backward()
        optim.step()
    sched.step()
    va = evaluate(dl_va)
    print(f"epoch {ep + 1}/{EPOCHS} loss {loss.item():.3f} val(pseudo) {va:.1%}", flush=True)
    if va > best:
        best, best_state = va, {k: v.detach().cpu().clone() for k, v in net.state_dict().items()}

net.load_state_dict(best_state)
torch.save(best_state, OUTDIR / "trained_model_v2.pth")


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(c - h, 3), round(c + h, 3)


# 4) 홀드아웃 평가
res_acc = evaluate(dl_ho)
taste_pred = (taste_prob(X[ho]) >= 0.5).float()
taste_acc = (taste_pred == y[ho]).float().mean().item()
k_res, k_taste = round(res_acc * len(ho)), round(taste_acc * len(ho))
report = {
    "holdout_n": len(ho),
    "resnet_holdout_acc": round(res_acc, 3), "resnet_holdout_ci95": wilson(k_res, len(ho)),
    "taste_model_holdout_acc": round(taste_acc, 3), "taste_model_ci95": wilson(k_taste, len(ho)),
    "majority_baseline": round(max(y[ho].mean().item(), 1 - y[ho].mean().item()), 3),
    "pseudo_labels": len(pseudo), "pseudo_teto": n_teto, "val_pseudo_best": round(best, 3),
    "conf_threshold": CONF, "epochs": EPOCHS,
}
(OUTDIR / "report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
print(json.dumps(report, indent=1))

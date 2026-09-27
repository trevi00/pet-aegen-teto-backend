"""v3 학습: 규칙 라벨(품종 성향 > 차분한 모습 > 나이)을 따르는 다중 과제 모델.

v2 는 사람 1명의 판정(300장)을 배워서 "작고 동그라면 에겐" 쪽으로 기울었고, 품종의 알려진 성향과
거의 무관해졌다(품종 평균 vs 알려진 성향 상관 -0.19). v3 는 설계 기준인 규칙 점수를 직접 목표로 한다.

입력 : data/oxford-pets/labels.csv (label_oxford.py 가 만든 품종·자세·나이 점수와 final)
분할 : 사람 홀드아웃 60장은 학습·시험에서 모두 빼고(사람 일치도 보고용), 나머지를 품종별 층화로 train 85 / val 5 / test 10
출력 : models/trained_model_v3.pth, models/model_v3_meta.json, models/report_v3.json
"""
import csv
import json
import math
import random
import sys
from pathlib import Path

import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

HOME = Path.home() / "apps/agtt"
sys.path.insert(0, str(HOME / "pet-aegen-teto-backend/app/ai"))
from agtt_net import EVAL_TRANSFORM, AgttNet  # noqa: E402

DATA = HOME / "data/oxford-pets"
OUT = HOME / "models"
K = 4.0            # 규칙 점수 → 에겐 확률: sigmoid(-K * final). final 0.25 → 에겐 27%, -0.5 → 88%
EPOCHS, BS, LR = 12, 64, 1e-4
W_BREED, W_POSE = 0.5, 0.5
SEED = 42

random.seed(SEED)
torch.manual_seed(SEED)

rows = list(csv.DictReader(open(DATA / "labels.csv", encoding="utf-8")))
breeds = sorted({r["breed"] for r in rows})
assert len(breeds) == 37, len(breeds)
bidx = {b: i for i, b in enumerate(breeds)}
hold = {it["file"] for it in json.load(open(DATA / "holdout.json", encoding="utf-8"))}

by_breed = {}
for r in rows:
    if r["file"] not in hold:
        by_breed.setdefault(r["breed"], []).append(r)
train, val, test = [], [], []
for b, items in by_breed.items():
    random.shuffle(items)
    n = len(items)
    nt, nv = round(n * 0.10), round(n * 0.05)
    test += items[:nt]
    val += items[nt:nt + nv]
    train += items[nt + nv:]
print(f"split train {len(train)} val {len(val)} test {len(test)} (human holdout {len(hold)} excluded)")

t_train = transforms.Compose([
    transforms.RandomResizedCrop(224, scale=(0.6, 1.0)), transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(0.2, 0.2, 0.2), transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


class DS(torch.utils.data.Dataset):
    def __init__(self, items, tf):
        self.items, self.tf = items, tf

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        r = self.items[i]
        x = self.tf(Image.open(DATA / "images" / r["file"]).convert("RGB"))
        final = float(r["final"])
        return x, torch.tensor(1 / (1 + math.exp(K * final)), dtype=torch.float32), bidx[r["breed"]], \
            torch.tensor(float(r["pose_score"]), dtype=torch.float32), torch.tensor(final, dtype=torch.float32)


def loader(items, tf, shuffle=False):
    return torch.utils.data.DataLoader(DS(items, tf), batch_size=BS, shuffle=shuffle, num_workers=8, pin_memory=True)


dl_tr, dl_va, dl_te = loader(train, t_train, True), loader(val, EVAL_TRANSFORM), loader(test, EVAL_TRANSFORM)
dev = torch.device("cuda")
net = AgttNet(pretrained=True).to(dev)
head_params = [p for n, p in net.named_parameters() if not n.startswith("backbone.")]
opt = torch.optim.AdamW([{"params": net.backbone.parameters(), "lr": LR}, {"params": head_params, "lr": LR * 10}], weight_decay=1e-4)
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, EPOCHS)


@torch.no_grad()
def predict(dl):
    net.eval()
    P, T, BP, BT, PP, PT, FF = [], [], [], [], [], [], []
    for x, t, b, pose, final in dl:
        with torch.autocast("cuda", dtype=torch.bfloat16):
            a, bl, pp = net(x.to(dev))
        P.append(torch.sigmoid(a.float()).cpu()); T.append(t); BP.append(bl.float().cpu()); BT.append(b)
        PP.append(pp.float().cpu()); PT.append(pose); FF.append(final)
    return [torch.cat(v) for v in (P, T, BP, BT, PP, PT, FF)]


def metrics(dl):
    p, t, bl, bt, pp, pt, final = predict(dl)
    rule = ((p >= 0.5) == (final <= 0)).float().mean().item()
    top1 = (bl.argmax(1) == bt).float().mean().item()
    top3 = (bl.topk(3, 1).indices == bt[:, None]).any(1).float().mean().item()
    pose_r = torch.corrcoef(torch.stack([pp, pt]))[0, 1].item()
    return {"rule_acc": rule, "mae_pct": (p - t).abs().mean().item() * 100, "breed_top1": top1, "breed_top3": top3, "pose_r": pose_r}, (p, bt)


best, best_state = -1, None
for ep in range(EPOCHS):
    net.train()
    for x, t, b, pose, _ in dl_tr:
        x, t, b, pose = x.to(dev), t.to(dev), b.to(dev), pose.to(dev)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            a, bl, pp = net(x)
            loss = F.binary_cross_entropy_with_logits(a.float(), t) + W_BREED * F.cross_entropy(bl.float(), b) \
                + W_POSE * F.mse_loss(pp.float(), pose)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    sched.step()
    m, _ = metrics(dl_va)
    score = m["rule_acc"] + m["breed_top1"]
    print(f"epoch {ep + 1}/{EPOCHS} loss {loss.item():.3f} val {json.dumps({k: round(v, 3) for k, v in m.items()})}", flush=True)
    if score > best:
        best, best_state = score, {k: v.detach().cpu().clone() for k, v in net.state_dict().items()}

net.load_state_dict(best_state)
test_m, (p_te, b_te) = metrics(dl_te)

# 품종 방향: 시험 세트의 품종별 평균 에겐 비율 vs 알려진 성향 점수
known = {r["breed"].lower(): float(r["score"]) for r in csv.DictReader(open(HOME / "pet-aegen-teto-backend/training/breed_temperament.csv", encoding="utf-8"))}
means = {}
for pi, bi in zip(p_te.tolist(), b_te.tolist()):
    means.setdefault(breeds[bi], []).append(pi * 100)
xs = [known[b] for b in means]
ys = [sum(v) / len(v) for v in means.values()]
breed_r = torch.corrcoef(torch.tensor([xs, ys]))[0, 1].item()

# 사람 홀드아웃(60장) 일치도 — 설계 기준이 바뀌었으므로 참고용으로만 보고한다
hold_items = [r for r in rows if r["file"] in hold]
human = {it["file"]: it["label"] for it in json.load(open(DATA / "holdout.json", encoding="utf-8"))}
p_h, *_ = predict(loader(hold_items, EVAL_TRANSFORM))
k_h = sum((pi >= 0.5) == (human[r["file"]] == "aegen") for pi, r in zip(p_h.tolist(), hold_items))

torch.save(best_state, OUT / "trained_model_v3.pth")
json.dump({"version": 3, "breeds": breeds, "k": K}, open(OUT / "model_v3_meta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
report = {
    "split": {"train": len(train), "val": len(val), "test": len(test), "human_holdout": len(hold)},
    "test": {k: round(v, 3) for k, v in test_m.items()},
    "breed_known_vs_ai_r": round(breed_r, 2),
    "human_holdout_agree": f"{k_h}/{len(hold_items)}",
    "k": K, "epochs": EPOCHS, "loss_weights": {"breed": W_BREED, "pose": W_POSE},
}
json.dump(report, open(OUT / "report_v3.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(report, ensure_ascii=False, indent=1))

"""ResNet 로짓 온도 보정: 정답 세트 중 홀드아웃이 아닌 240장으로 NLL 최소화 T 를 찾는다.
정확도(argmax)는 변하지 않고 확률만 현실적으로 바뀐다. 홀드아웃 60장에서 보정 전후 NLL/ECE 를 보고한다."""
import json
import pathlib
import sys

import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms

root = pathlib.Path(sys.argv[1]).expanduser()
model_path = pathlib.Path(sys.argv[2]).expanduser()
G = torch.load(root / "gold_features.pt")
hold = {h["file"] for h in json.loads((root / "holdout.json").read_text(encoding="utf-8"))}
files, y = G["files"], G["y"].long()
cal = [i for i, f in enumerate(files) if f not in hold]
ho = [i for i, f in enumerate(files) if f in hold]

tf = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(),
                         transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
net = models.resnet50()
net.fc = nn.Linear(net.fc.in_features, 2)
net.load_state_dict(torch.load(model_path, map_location="cpu"))
net = net.cuda().eval()


def logits(idx):
    out = []
    for i in range(0, len(idx), 64):
        x = torch.stack([tf(Image.open(root / "images" / files[j]).convert("RGB")) for j in idx[i:i + 64]]).cuda()
        with torch.no_grad():
            out.append(net(x).float().cpu())
    return torch.cat(out)


Lc, Lh = logits(cal), logits(ho)
yc, yh = y[cal], y[ho]
logT = torch.zeros(1, requires_grad=True)
opt = torch.optim.LBFGS([logT], max_iter=200)


def closure():
    opt.zero_grad()
    loss = nn.functional.cross_entropy(Lc / logT.exp(), yc)
    loss.backward()
    return loss


opt.step(closure)
T = logT.exp().item()


def ece(L, yy, bins=10):
    p = torch.softmax(L, 1)
    conf, pred = p.max(1)
    e = 0.0
    for b in range(bins):
        m = (conf > b / bins) & (conf <= (b + 1) / bins)
        if m.any():
            e += m.float().mean().item() * abs((pred[m] == yy[m]).float().mean().item() - conf[m].mean().item())
    return e


rep = {
    "temperature": round(T, 3),
    "holdout_acc": round((Lh.argmax(1) == yh).float().mean().item(), 3),
    "holdout_nll_before": round(nn.functional.cross_entropy(Lh, yh).item(), 3),
    "holdout_nll_after": round(nn.functional.cross_entropy(Lh / T, yh).item(), 3),
    "holdout_ece_before": round(ece(Lh, yh), 3),
    "holdout_ece_after": round(ece(Lh / T, yh), 3),
    "holdout_mean_conf_before": round(torch.softmax(Lh, 1).max(1).values.mean().item(), 3),
    "holdout_mean_conf_after": round(torch.softmax(Lh / T, 1).max(1).values.mean().item(), 3),
}
print(json.dumps(rep, indent=1))
(model_path.parent / "calibration.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")

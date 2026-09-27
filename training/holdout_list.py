"""train_pipeline.py 와 같은 규칙(시드)으로 홀드아웃 60장 목록을 재현해 holdout.json 으로 저장."""
import json
import pathlib
import random
import sys

import torch

root = pathlib.Path(sys.argv[1]).expanduser()
SEED, HOLDOUT = 20260927, 60
G = torch.load(root / "gold_features.pt")
files, y = G["files"], G["y"]
idx0 = [i for i in range(len(files)) if y[i] == 0]
idx1 = [i for i in range(len(files)) if y[i] == 1]
rng = random.Random(SEED)
rng.shuffle(idx0)
rng.shuffle(idx1)
h0 = round(HOLDOUT * len(idx0) / len(files))
hold = sorted(idx0[:h0] + idx1[:HOLDOUT - h0])
out = [{"file": files[i], "label": "teto" if y[i] == 1 else "aegen"} for i in hold]
(root / "holdout.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(len(out), "holdout items")

"""timm/oxford-iiit-pet parquet -> images/<Breed>_<n>.jpg (원본 Oxford 파일명 규칙과 동일하게)."""
import io
import pathlib
import sys

import pyarrow.parquet as pq

root = pathlib.Path(sys.argv[1]).expanduser()
out = root / "images"
out.mkdir(exist_ok=True)

t0 = pq.read_table(root / "train.parquet")
print(t0.schema)
names = None
meta = t0.schema.metadata or {}
if b"huggingface" in meta:
    import json
    feats = json.loads(meta[b"huggingface"]).get("info", {}).get("features", {})
    for k, v in feats.items():
        if isinstance(v, dict) and v.get("_type") == "ClassLabel" and len(v.get("names", [])) == 37:
            names = v["names"]
            print("label column:", k, "| first names:", names[:3])

count = 0
for split in ("train", "test"):
    tbl = pq.read_table(root / f"{split}.parquet")
    for row in tbl.to_pylist():
        img = row["image"]
        data = img["bytes"] if isinstance(img, dict) else img
        src = (img.get("path") if isinstance(img, dict) else None) or ""
        stem = pathlib.Path(src).stem if src else ""
        if not stem or "_" not in stem:
            sid = row.get("image_id") or row.get("id")
            stem = str(sid) if sid else f"{names[row['label']]}_{split}{count}"
        (out / f"{stem}.jpg").write_bytes(data)
        count += 1
print("extracted", count, "->", out)
print("sample:", sorted(p.name for p in out.glob("*.jpg"))[:5])

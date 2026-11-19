#!/usr/bin/env python3
"""Collect per-region build outputs into one upload folder with index.json.

Usage: make_index.py ARTIFACTS_DIR UPLOAD_DIR

ARTIFACTS_DIR holds one folder per region (region-<id>/ with manifest.json,
tiles/, pois/). Writes UPLOAD_DIR/<id>/... and UPLOAD_DIR/index.json, which the
app reads to find which regions cover a group.
"""
import datetime
import json
import os
import shutil
import sys

src, dst = sys.argv[1], sys.argv[2]
os.makedirs(dst, exist_ok=True)
regions = []
for d in sorted(os.listdir(src)):
    path = os.path.join(src, d)
    man = os.path.join(path, "manifest.json")
    if not os.path.isfile(man):
        continue
    rid = d[len("region-"):] if d.startswith("region-") else d
    with open(man) as f:
        m = json.load(f)
    shutil.copytree(path, os.path.join(dst, rid), dirs_exist_ok=True)
    has_pois = os.path.isfile(os.path.join(path, "pois", "manifest.json"))
    has_transit = os.path.isfile(os.path.join(path, "transit", "manifest.json"))
    regions.append({
        "id": rid, "name": m.get("name", rid), "bbox": m["bbox"], "built": m.get("built"),
        "roads": f"{rid}/manifest.json", "pois": f"{rid}/pois/manifest.json" if has_pois else None,
        "transit": f"{rid}/transit/manifest.json" if has_transit else None,
        "bytes": sum(t["bytes"] for t in m["tiles"]),
    })
with open(os.path.join(dst, "index.json"), "w") as f:
    json.dump({"version": 1, "built": datetime.date.today().isoformat(), "regions": regions}, f, separators=(",", ":"))
total = sum(r["bytes"] for r in regions)
print(f"{len(regions)} regions, {total / 1e6:.0f} MB of road tiles")

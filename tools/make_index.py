#!/usr/bin/env python3
# Copyright (c) 2026 Amar Latchman. All rights reserved. Proprietary; see LICENSE.
"""Collect per-region build outputs into one upload folder with index.json.

Usage: make_index.py ARTIFACTS_DIR UPLOAD_DIR [PREVIOUS_INDEX.json]

If a previous index is given, regions missing from this run (a failed download)
are carried over, so the app keeps using last month's tiles for them.

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
if len(sys.argv) > 3 and os.path.isfile(sys.argv[3]):
    try:
        with open(sys.argv[3]) as f:
            prev = json.load(f)
        have = {r["id"] for r in regions}
        kept = [r for r in prev.get("regions", []) if r["id"] not in have]
        regions += kept
        if kept:
            print("kept from previous run: " + ", ".join(r["id"] for r in kept))
    except (ValueError, KeyError) as e:
        print(f"could not read previous index: {e}")
with open(os.path.join(dst, "index.json"), "w") as f:
    json.dump({"version": 1, "built": datetime.date.today().isoformat(), "regions": regions}, f, separators=(",", ":"))
total = sum(r["bytes"] for r in regions)
print(f"{len(regions)} regions, {total / 1e6:.0f} MB of road tiles")

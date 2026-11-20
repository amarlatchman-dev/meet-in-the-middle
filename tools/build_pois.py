#!/usr/bin/env python3
# Copyright (c) 2026 Amar Latchman. All rights reserved. Proprietary; see LICENSE.
"""Build pre-loaded "things to do nearby" tiles for Meet in the Middle.

Usage: build_pois.py INPUT.osm.pbf OUT_DIR [--bbox S,W,N,E] [--step 0.5]

Reads named places (food, drink, activities, parks, libraries, malls...) from
an OSM extract and writes OUT_DIR/pois/manifest.json plus one JSON tile per
--step degree square: [[lat, lon, name, {tags}], ...]. Ways use the centre of
their nodes; relations (a few very large parks) are skipped.
"""
import argparse
import datetime
import math
import json
import os
import sys

import osmium

WANT = {
    "amenity": {"restaurant", "fast_food", "food_court", "cafe", "ice_cream", "bar", "pub", "biergarten",
                "cinema", "theatre", "arts_centre", "library", "marketplace", "community_centre"},
    "shop": {"bakery", "pastry", "confectionery", "chocolate", "mall", "department_store"},
    "leisure": {"park", "garden", "nature_reserve", "dog_park", "common", "bowling_alley", "escape_game",
                "amusement_arcade", "miniature_golf", "trampoline_park", "sports_centre", "ice_rink",
                "water_park", "climbing"},
    "tourism": {"museum", "gallery", "zoo", "aquarium", "theme_park", "attraction", "viewpoint"},
}
KEEP = ["amenity", "shop", "leisure", "tourism", "cuisine", "opening_hours", "fee",
        "diet:vegetarian", "diet:vegan", "diet:halal", "website"]


def wanted(tags):
    if not tags.get("name"):
        return False
    return any(tags.get(k) in v for k, v in WANT.items())


def slim(tags):
    out = {}
    for k in KEEP:
        v = tags.get(k)
        if v:
            out[k] = v[:120]
    return out


class Places(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.items = []

    def node(self, n):
        if wanted(n.tags) and n.location.valid():
            self.items.append((n.location.lat, n.location.lon, n.tags.get("name"), slim(n.tags)))

    def way(self, w):
        if not wanted(w.tags):
            return
        pts = [(nd.location.lat, nd.location.lon) for nd in w.nodes if nd.location.valid()]
        if not pts:
            return
        la = sum(p[0] for p in pts) / len(pts)
        lo = sum(p[1] for p in pts) / len(pts)
        self.items.append((la, lo, w.tags.get("name"), slim(w.tags)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("out_dir")
    ap.add_argument("--bbox", help="S,W,N,E (default: whole file)")
    ap.add_argument("--step", type=float, default=0.5)
    a = ap.parse_args()
    h = Places()
    h.apply_file(a.input, locations=True, idx="flex_mem")
    if a.bbox:
        s, w, n, e = (float(x) for x in a.bbox.split(","))
    elif h.items:
        s, n = min(i[0] for i in h.items), max(i[0] for i in h.items)
        w, e = min(i[1] for i in h.items), max(i[1] for i in h.items)
    else:
        s = w = n = e = 0.0
    s0, w0 = math.floor(s / a.step) * a.step, math.floor(w / a.step) * a.step

    buckets = {}
    for la, lo, name, tags in h.items:
        if not (s <= la <= n and w <= lo <= e):
            continue
        r, c = int((la - s0) // a.step), int((lo - w0) // a.step)
        buckets.setdefault((r, c), []).append([round(la, 6), round(lo, 6), name, tags])

    out = os.path.join(a.out_dir, "pois")
    os.makedirs(out, exist_ok=True)
    manifest = {"version": 1, "step": a.step, "bbox": [round(v, 5) for v in (s, w, n, e)],
                "built": datetime.date.today().isoformat(), "tiles": []}
    total = 0
    for (r, c), items in sorted(buckets.items()):
        name = f"{r}_{c}.json"
        path = os.path.join(out, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, separators=(",", ":"))
        size = os.path.getsize(path)
        total += size
        manifest["tiles"].append({
            "file": "pois/" + name, "bytes": size, "count": len(items),
            "bbox": [round(s0 + r * a.step, 4), round(w0 + c * a.step, 4),
                     round(s0 + (r + 1) * a.step, 4), round(w0 + (c + 1) * a.step, 4)],
        })
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, separators=(",", ":"))
    count = sum(len(v) for v in buckets.values())
    print(f"{count:,} places in {len(buckets)} tiles, {total / 1e6:.1f} MB", file=sys.stderr)


if __name__ == "__main__":
    main()

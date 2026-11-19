#!/usr/bin/env python3
"""Build rapid-transit tiles (subway, LRT, streetcar, commuter rail) for Meet in the Middle.

Usage: build_transit.py INPUT.osm.pbf OUT_DIR [--step 0.5]

Writes OUT_DIR/transit/manifest.json plus one JSON tile per --step degree square:
  {"s": [[lat1, lon1, lat2, lon2, cls], ...],   # track segments, coords * 1e6
   "st": [[lat, lon, cls, name], ...]}           # stations / stops
cls: 0 subway/metro, 1 light rail, 2 streetcar/tram, 3 commuter/intercity rail.
The app joins stations to the walking network with an average wait, so this is a
schedule-free estimate. Buses are not included.
"""
import argparse
import datetime
import json
import math
import os
import sys

import osmium

SIMPLIFY_M = 12.0
TRACK = {"subway": 0, "light_rail": 1, "tram": 2, "rail": 3}


def simplify(pts):
    if len(pts) <= 2:
        return pts
    k = math.cos(math.radians(pts[0][0]))
    xy = [(p[1] * 111320 * k, p[0] * 110540) for p in pts]
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        ax, ay = xy[i]
        bx, by = xy[j]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        best, bi = -1.0, -1
        for m in range(i + 1, j):
            px, py = xy[m]
            t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
            d = math.hypot(px - (ax + t * dx), py - (ay + t * dy))
            if d > best:
                best, bi = d, m
        if best > SIMPLIFY_M:
            keep[bi] = True
            stack += [(i, bi), (bi, j)]
    return [p for p, v in zip(pts, keep) if v]


def station_class(t):
    st = t.get("station")
    if st in ("subway", "metro") or t.get("subway") == "yes":
        return 0
    if st == "light_rail" or t.get("light_rail") == "yes":
        return 1
    if t.get("railway") == "tram_stop" or t.get("tram") == "yes":
        return 2
    if t.get("train") == "yes" or t.get("railway") in ("station", "halt"):
        return 3
    return None


class Transit(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.tracks = []    # (cls, [(lat, lon), ...])
        self.stations = []  # (lat, lon, cls, name)

    def way(self, w):
        t = w.tags
        cls = TRACK.get(t.get("railway"))
        if cls is None:
            return
        if t.get("service") in ("yard", "siding", "spur", "crossover"):
            return
        if cls == 3 and t.get("usage") not in ("main", "branch"):
            return  # skip freight-only and industrial rail
        pts = [(n.location.lat, n.location.lon) for n in w.nodes if n.location.valid()]
        if len(pts) >= 2:
            self.tracks.append((cls, simplify(pts)))

    def node(self, n):
        t = n.tags
        rw, pt = t.get("railway"), t.get("public_transport")
        if rw not in ("station", "halt", "tram_stop") and pt not in ("station", "stop_position"):
            return
        if pt == "stop_position" and not any(t.get(k) == "yes" for k in ("train", "subway", "light_rail", "tram")):
            return
        cls = station_class(t)
        if cls is not None and n.location.valid():
            self.stations.append((n.location.lat, n.location.lon, cls, t.get("name", "")[:60]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("out_dir")
    ap.add_argument("--step", type=float, default=0.5)
    a = ap.parse_args()
    h = Transit()
    h.apply_file(a.input, locations=True, idx="flex_mem")
    step = a.step

    def key(lat, lon):
        return int(math.floor(lat / step)), int(math.floor(lon / step))

    tiles = {}
    nseg = 0
    for cls, pts in h.tracks:
        for (la1, lo1), (la2, lo2) in zip(pts, pts[1:]):
            tiles.setdefault(key(la1, lo1), {"s": [], "st": []})["s"].append(
                [round(la1 * 1e6), round(lo1 * 1e6), round(la2 * 1e6), round(lo2 * 1e6), cls])
            nseg += 1
    for la, lo, cls, name in h.stations:
        tiles.setdefault(key(la, lo), {"s": [], "st": []})["st"].append([round(la * 1e6), round(lo * 1e6), cls, name])

    out = os.path.join(a.out_dir, "transit")
    os.makedirs(out, exist_ok=True)
    manifest = {"version": 1, "step": step, "built": datetime.date.today().isoformat(), "tiles": []}
    total = 0
    for (r, c), data in sorted(tiles.items()):
        name = f"{r}_{c}.json"
        path = os.path.join(out, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        size = os.path.getsize(path)
        total += size
        manifest["tiles"].append({"file": "transit/" + name, "bytes": size,
                                  "bbox": [r * step, c * step, (r + 1) * step, (c + 1) * step]})
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, separators=(",", ":"))
    print(f"{nseg:,} transit segments, {len(h.stations):,} stations, {len(tiles)} tiles, {total / 1e6:.1f} MB",
          file=sys.stderr)


if __name__ == "__main__":
    main()

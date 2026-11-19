#!/usr/bin/env python3
"""Build a compact road-network file for Meet in the Middle from an OSM extract.

Usage: build_region.py INPUT.osm.pbf OUT_DIR --bbox S,W,N,E [--step 0.5] [--name NAME]

Writes OUT_DIR/manifest.json plus one tile file per --step degree square
(OUT_DIR/tiles/<row>_<col>.bin). Each segment goes in the tile of its first
node; nodes shared across tiles are repeated and merged by exact coordinates
in the browser.

Keeps drivable/walkable public roads, splits ways at intersections, and
simplifies curves (Douglas-Peucker, ~12 m) so the file stays small.

Tile binary layout (little endian), all 4-byte arrays first so they stay aligned:
  char[4]  magic "MITM"
  uint32   version (1)
  uint32   node count N
  uint32   segment count E
  int32[N] lat * 1e6
  int32[N] lon * 1e6
  uint32[E] node a
  uint32[E] node b
  float32[E] length in metres
  uint8[E] road class (index into CLASSES)
  int8[E]  oneway: 0 both ways, 1 a->b only, -1 b->a only
  uint8[E] maxspeed km/h (0 = unknown)
"""
import argparse
import datetime
import json
import os
import math
import struct
import sys

import osmium

CLASSES = [
    "motorway", "trunk", "primary", "secondary", "tertiary", "unclassified",
    "residential", "living_street", "motorway_link", "trunk_link",
    "primary_link", "secondary_link", "tertiary_link", "pedestrian",
]
CLASS_IDX = {c: i for i, c in enumerate(CLASSES)}
SIMPLIFY_M = 12.0


def oneway_dir(t):
    o = t.get("oneway")
    if o in ("no", "false", "0"):
        return 0
    if o in ("-1", "reverse"):
        return -1
    if o in ("yes", "true", "1"):
        return 1
    if t.get("junction") in ("roundabout", "circular"):
        return 1
    if t.get("highway") == "motorway":
        return 1
    return 0


def parse_speed(v):
    if not v:
        return 0
    try:
        num = float(v.split()[0])
    except ValueError:
        return 0
    if "mph" in v:
        num *= 1.609
    return int(num) if 4 < num < 200 else 0


def hav(a1, o1, a2, o2):
    r = math.pi / 180
    da, do = (a2 - a1) * r, (o2 - o1) * r
    h = math.sin(da / 2) ** 2 + math.cos(a1 * r) * math.cos(a2 * r) * math.sin(do / 2) ** 2
    return 2 * 6371008 * math.asin(math.sqrt(h))


def simplify(pts):
    """Douglas-Peucker on (lat, lon) using a local metric projection. Returns kept indices."""
    if len(pts) <= 2:
        return list(range(len(pts)))
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
            if L2 == 0:
                d = math.hypot(px - ax, py - ay)
            else:
                t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
                d = math.hypot(px - (ax + t * dx), py - (ay + t * dy))
            if d > best:
                best, bi = d, m
        if best > SIMPLIFY_M:
            keep[bi] = True
            stack.append((i, bi))
            stack.append((bi, j))
    return [i for i, v in enumerate(keep) if v]


class Roads(osmium.SimpleHandler):
    def __init__(self, bbox):
        super().__init__()
        self.s, self.w, self.n, self.e = bbox
        self.ways = []  # (refs, coords, cls, oneway, speed)
        self.use = {}

    def way(self, w):
        t = w.tags
        hw = t.get("highway")
        if hw not in CLASS_IDX:
            return
        if t.get("area") == "yes" or t.get("access") in ("no", "private"):
            return
        refs, coords = [], []
        for nd in w.nodes:
            if not nd.location.valid():
                continue
            lat, lon = nd.location.lat, nd.location.lon
            refs.append(nd.ref)
            coords.append((lat, lon))
        if len(refs) < 2:
            return
        if not any(self.s <= la <= self.n and self.w <= lo <= self.e for la, lo in coords):
            return
        tags = {"oneway": t.get("oneway"), "junction": t.get("junction"), "highway": hw}
        self.ways.append((refs, coords, CLASS_IDX[hw], oneway_dir(tags), parse_speed(t.get("maxspeed"))))
        for i, r in enumerate(refs):
            self.use[r] = self.use.get(r, 0) + (2 if i in (0, len(refs) - 1) else 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("out_dir")
    ap.add_argument("--bbox", required=True, help="S,W,N,E")
    ap.add_argument("--step", type=float, default=0.5, help="tile size in degrees")
    ap.add_argument("--name", default="Southern Ontario")
    a = ap.parse_args()
    bbox = [float(x) for x in a.bbox.split(",")]

    h = Roads(bbox)
    h.apply_file(a.input, locations=True, idx="flex_mem")
    print(f"{len(h.ways):,} road ways", file=sys.stderr)

    node_id = {}
    lat, lon = [], []

    def nid(key, la, lo):
        i = node_id.get(key)
        if i is None:
            i = len(lat)
            node_id[key] = i
            lat.append(round(la * 1e6))
            lon.append(round(lo * 1e6))
        return i

    A, B, LEN, CLS, OW, SPD = [], [], [], [], [], []
    shape_seq = 0
    for refs, coords, cls, ow, spd in h.ways:
        # split at intersections (nodes used more than once)
        start = 0
        for k in range(1, len(refs)):
            if k == len(refs) - 1 or h.use[refs[k]] > 1:
                piece = coords[start:k + 1]
                prefs = refs[start:k + 1]
                kept = simplify(piece)
                prev = None
                for idx in kept:
                    la, lo = piece[idx]
                    if idx == 0 or idx == len(piece) - 1:
                        cur = nid(prefs[idx], la, lo)
                    else:
                        shape_seq += 1
                        cur = nid(("s", shape_seq), la, lo)
                    if prev is not None and prev[0] != cur:
                        A.append(prev[0])
                        B.append(cur)
                        LEN.append(hav(prev[1], prev[2], la, lo))
                        CLS.append(cls)
                        OW.append(ow)
                        SPD.append(min(255, spd))
                    prev = (cur, la, lo)
                start = k

    step = a.step
    s0, w0 = bbox[0], bbox[1]
    buckets = {}
    for k in range(len(A)):
        r = int((lat[A[k]] / 1e6 - s0) // step)
        c = int((lon[A[k]] / 1e6 - w0) // step)
        buckets.setdefault((r, c), []).append(k)

    os.makedirs(os.path.join(a.out_dir, "tiles"), exist_ok=True)
    manifest = {
        "version": 1, "name": a.name, "step": step, "bbox": bbox,
        "built": datetime.date.today().isoformat(), "tiles": [],
    }
    total_bytes = 0
    for (r, c), segs in sorted(buckets.items()):
        local = {}
        tlat, tlon = [], []

        def L(i):
            j = local.get(i)
            if j is None:
                j = len(tlat)
                local[i] = j
                tlat.append(lat[i])
                tlon.append(lon[i])
            return j

        ta = [L(A[k]) for k in segs]
        tb = [L(B[k]) for k in segs]
        N, E = len(tlat), len(segs)
        name = f"{r}_{c}.bin"
        path = os.path.join(a.out_dir, "tiles", name)
        with open(path, "wb") as f:
            f.write(b"MITM")
            f.write(struct.pack("<III", 1, N, E))
            f.write(struct.pack(f"<{N}i", *tlat))
            f.write(struct.pack(f"<{N}i", *tlon))
            f.write(struct.pack(f"<{E}I", *ta))
            f.write(struct.pack(f"<{E}I", *tb))
            f.write(struct.pack(f"<{E}f", *[LEN[k] for k in segs]))
            f.write(struct.pack(f"<{E}B", *[CLS[k] for k in segs]))
            f.write(struct.pack(f"<{E}b", *[OW[k] for k in segs]))
            f.write(struct.pack(f"<{E}B", *[SPD[k] for k in segs]))
        size = os.path.getsize(path)
        total_bytes += size
        tb_box = [round(s0 + r * step, 4), round(w0 + c * step, 4), round(s0 + (r + 1) * step, 4), round(w0 + (c + 1) * step, 4)]
        manifest["tiles"].append({"file": "tiles/" + name, "bbox": tb_box, "bytes": size})
    with open(os.path.join(a.out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, separators=(",", ":"))
    print(f"{len(lat):,} nodes, {len(A):,} segments, {len(buckets)} tiles, {total_bytes / 1e6:.1f} MB total, "
          f"largest tile {max(t['bytes'] for t in manifest['tiles']) / 1e6:.1f} MB", file=sys.stderr)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# Copyright (c) 2026 Amar Latchman. All rights reserved. Proprietary; see LICENSE.
"""Fallback downloader: fetch road ways for a bbox from Overpass in small tiles.

Usage: fetch_overpass.py OUT_DIR --bbox S,W,N,E [--step 0.15]
Writes one sorted-ready .osm XML file per tile into OUT_DIR. Merge them with
`osmium sort` + `osmium merge`.
"""
import argparse
import os
import sys
import time
import urllib.parse
import urllib.request

SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
CLASSES = ("motorway|trunk|primary|secondary|tertiary|unclassified|residential|living_street|"
           "motorway_link|trunk_link|primary_link|secondary_link|tertiary_link|pedestrian")


def fetch(query, tile_no):
    last = None
    for attempt in range(12):
        url = SERVERS[(tile_no + attempt) % len(SERVERS)]
        try:
            data = urllib.parse.urlencode({"data": query}).encode()
            req = urllib.request.Request(url, data=data, headers={"User-Agent": "meet-in-the-middle-map-builder"})
            with urllib.request.urlopen(req, timeout=300) as r:
                body = r.read()
            if b"<remark>" in body and (b"runtime error" in body or b"timed out" in body):
                raise RuntimeError("server ran out of time")
            return body
        except Exception as e:  # noqa: BLE001
            last = e
            wait = min(120, 10 * (attempt + 1))
            print(f"  tile {tile_no}: {url} failed ({e}); retrying in {wait}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"tile {tile_no} failed: {last}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--bbox", required=True)
    ap.add_argument("--step", type=float, default=0.15)
    ap.add_argument("--all", action="store_true", help="fetch every map object, not just roads (for small countries)")
    a = ap.parse_args()
    s, w, n, e = (float(x) for x in a.bbox.split(","))
    os.makedirs(a.out_dir, exist_ok=True)
    tiles = []
    lat = s
    while lat < n:
        lon = w
        while lon < e:
            tiles.append((lat, lon, min(lat + a.step, n), min(lon + a.step, e)))
            lon += a.step
        lat += a.step
    print(f"{len(tiles)} tiles", file=sys.stderr)
    for i, (ts, tw, tn, te) in enumerate(tiles):
        out = os.path.join(a.out_dir, f"tile{i:03d}.osm")
        if os.path.exists(out) and os.path.getsize(out) > 0:
            continue
        if a.all:
            q = f"[out:xml][timeout:600][maxsize:1073741824];(nwr({ts:.4f},{tw:.4f},{tn:.4f},{te:.4f}););(._;>;);out body;"
        else:
            q = (f'[out:xml][timeout:240];way["highway"~"^({CLASSES})$"]'
                 f"({ts:.4f},{tw:.4f},{tn:.4f},{te:.4f});(._;>;);out body;")
        body = fetch(q, i)
        with open(out, "wb") as f:
            f.write(body)
        print(f"tile {i + 1}/{len(tiles)}: {len(body) / 1e6:.1f} MB", file=sys.stderr)
        time.sleep(2)


if __name__ == "__main__":
    main()

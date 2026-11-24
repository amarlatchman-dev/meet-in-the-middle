#!/usr/bin/env python3
# Copyright (c) 2026 Amar Latchman. All rights reserved. Proprietary; see LICENSE.
"""
Post today's Halfwise reel to Instagram and the Facebook Page.

Picks one entry from social/schedule.json (cycling by day since start_date),
records it with tools/record_reel.js, then uploads it as a Reel to both
accounts through the Meta Graph API.

Environment:
  META_TOKEN   system-user access token (required; GitHub secret)
  PAGE_ID      Facebook Page ID (optional; found from the token if blank)
  POST_INDEX   force a schedule entry by number (optional)
  PLATFORMS    "instagram,facebook" (default both)
  DRY_RUN      "1" records the reel but posts nothing
"""
import datetime as dt
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

API = "https://graph.facebook.com/v21.0"
ROOT = Path(__file__).resolve().parent.parent


def pick_entry():
    sched = json.loads((ROOT / "social" / "schedule.json").read_text())
    posts = sched["posts"]
    if os.environ.get("POST_INDEX", "").strip():
        i = int(os.environ["POST_INDEX"]) % len(posts)
    else:
        start = dt.date.fromisoformat(sched["start_date"])
        i = max(0, (dt.date.today() - start).days) % len(posts)
    e = posts[i]
    n = len(e["people"].split("|"))
    body = e.get("caption") or "Everyone floods out along the real streets, and the fair spot is where they meet."
    caption = (
        f"{e['hook']} 📍 {body}\n\n"
        f"Try it with your group: halfwise.app (link in bio)\n\n"
        f"{e.get('tags', '')} {sched.get('hashtags_default', '')}".strip()
    )
    print(f"Entry #{i}: {e['city']} ({n} people, {e.get('mode', 'drive')})")
    return i, e, caption


def record(e, out):
    cmd = ["node", str(ROOT / "tools" / "record_reel.js"), "--people", e["people"],
           "--city", e["city"], "--out", str(out)]
    for k in ("mode", "goal", "place", "want", "feature", "when"):
        if e.get(k):
            cmd += [f"--{k}", e[k]]
    subprocess.run(cmd, check=True)


def g(method, path, **params):
    r = requests.request(method, f"{API}/{path}", params=params, timeout=120)
    if not r.ok:
        raise RuntimeError(f"{method} {path}: {r.status_code} {r.text}")
    return r.json()


def find_accounts(token):
    pages = g("GET", "me/accounts", access_token=token,
              fields="id,name,access_token,instagram_business_account")["data"]
    want = os.environ.get("PAGE_ID", "").strip()
    page = next((p for p in pages if not want or p["id"] == want), None)
    if not page:
        raise RuntimeError(f"No Facebook Page found for this token (pages: {[p['name'] for p in pages]})")
    ig = (page.get("instagram_business_account") or {}).get("id")
    print(f"Page: {page['name']} ({page['id']}), Instagram: {ig}")
    return page, ig


def upload_binary(url, token, video):
    data = video.read_bytes()
    r = requests.post(url, data=data, timeout=600, headers={
        "Authorization": f"OAuth {token}", "offset": "0", "file_size": str(len(data))})
    if not r.ok:
        raise RuntimeError(f"upload: {r.status_code} {r.text}")


def post_instagram(ig, token, video, caption):
    c = g("POST", f"{ig}/media", access_token=token, media_type="REELS",
          upload_type="resumable", caption=caption, share_to_feed="true")
    upload_binary(c.get("uri") or f"https://rupload.facebook.com/ig-api-upload/v21.0/{c['id']}", token, video)
    for _ in range(60):
        s = g("GET", c["id"], access_token=token, fields="status_code,status")
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") == "ERROR":
            raise RuntimeError(f"Instagram processing failed: {s}")
        time.sleep(10)
    else:
        raise RuntimeError("Instagram processing timed out")
    m = g("POST", f"{ig}/media_publish", access_token=token, creation_id=c["id"])
    print(f"Instagram reel published: {m['id']}")


def post_facebook(page, video, caption):
    pt = page["access_token"]
    s = g("POST", f"{page['id']}/video_reels", access_token=pt, upload_phase="start")
    upload_binary(s.get("upload_url") or f"https://rupload.facebook.com/video-upload/v21.0/{s['video_id']}", pt, video)
    g("POST", f"{page['id']}/video_reels", access_token=pt, upload_phase="finish",
      video_id=s["video_id"], video_state="PUBLISHED", description=caption)
    print(f"Facebook reel published: {s['video_id']}")


def main():
    sched = json.loads((ROOT / "social" / "schedule.json").read_text())
    if not os.environ.get("POST_INDEX", "").strip() and dt.date.today().isoformat() in sched.get("skip_dates", []):
        print("Today is in skip_dates (already posted by hand); nothing to do.")
        return
    i, e, caption = pick_entry()
    for attempt in range(4):  # if a city fails to record, fall back to the next entry
        video = ROOT / f"reel-{i}.mp4"
        try:
            record(e, video)
            break
        except subprocess.CalledProcessError:
            print(f"::warning::Recording entry #{i} failed; trying the next one")
            os.environ["POST_INDEX"] = str(i + 1)
            i, e, caption = pick_entry()
    else:
        sys.exit("Recording failed for 4 entries in a row")
    if os.environ.get("DRY_RUN") == "1":
        print("Dry run: recorded, not posting.\n" + caption)
        return
    token = os.environ["META_TOKEN"]
    page, ig = find_accounts(token)
    want = os.environ.get("PLATFORMS", "instagram,facebook")
    failures = []
    if "instagram" in want:
        try:
            if not ig:
                raise RuntimeError("Instagram account isn't linked to the Page")
            post_instagram(ig, token, video, caption)
        except Exception as ex:
            failures.append(f"Instagram: {ex}")
    if "facebook" in want:
        try:
            post_facebook(page, video, caption)
        except Exception as ex:
            failures.append(f"Facebook: {ex}")
    for f in failures:
        print("::error::" + f)
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()

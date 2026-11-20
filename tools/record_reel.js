#!/usr/bin/env node
// Copyright (c) 2026 Amar Latchman. All rights reserved. Proprietary; see LICENSE.
/*
  Record a vertical (1080x1920) Halfwise reel as an MP4, ready for Instagram Reels,
  Facebook Reels and YouTube Shorts.

  Needs Node, Playwright (npm i playwright && npx playwright install chromium) and ffmpeg.

  Example:
    node tools/record_reel.js \
      --people "Maya@43.5933,-79.6441|Jordan@43.7757,-79.2578|Leah@43.8255,-79.5385|Omar@43.6383,-79.4201" \
      --city "Greater Toronto Area" --mode drive --goal fair --out toronto.mp4

  Options:
    --people  "Name@lat,lon|Name@lat,lon|..."  (2 to 10 people)
    --city    subtitle shown under "Where should N friends meet?"
    --place   name to show for the meeting spot (otherwise looked up automatically)
    --mode    drive | transit | bike | walk     (default drive)
    --goal    fair | balanced | total            (default fair)
    --url     site to record                     (default https://halfwise.app/)
    --out     output file                        (default reel.mp4)
*/
const { chromium } = require("playwright");
const { execFileSync } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const args = {};
for (let i = 2; i < process.argv.length; i += 2) args[process.argv[i].replace(/^--/, "")] = process.argv[i + 1];
const people = (args.people || "").split("|").filter(Boolean).map((s) => {
  const [name, ll] = s.split("@");
  const [lat, lon] = ll.split(",").map(Number);
  return [name.trim(), lat, lon, ""];
});
if (people.length < 2) { console.error("Give at least two people with --people"); process.exit(1); }

const b64 = (str) => Buffer.from(str, "utf8").toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const group = { v: 1, p: people, m: args.mode || "drive", g: args.goal || "fair" };
const base = args.url || "https://halfwise.app/";
const qs = new URLSearchParams({ reel: "1" });
if (args.city) qs.set("city", args.city);
if (args.place) qs.set("place", args.place);
const url = `${base}?${qs}#g=${b64(JSON.stringify(group))}`;
const out = path.resolve(args.out || "reel.mp4");

(async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "reel-"));
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1080, height: 1920 }, recordVideo: { dir, size: { width: 1080, height: 1920 } } });
  if (args.leaflet) { // offline testing only: serve Leaflet from a local copy
    const js = fs.readFileSync(path.join(args.leaflet, "leaflet.js")), css = fs.readFileSync(path.join(args.leaflet, "leaflet.css"));
    await ctx.route(/leaflet\.min\.css$/, (r) => r.fulfill({ body: css, contentType: "text/css" }));
    await ctx.route(/leaflet\.js$/, (r) => r.fulfill({ body: js, contentType: "application/javascript" }));
  }
  const page = await ctx.newPage();
  const started = Date.now();
  await page.goto(url);
  await page.waitForFunction(() => document.body.dataset.reelDone === "1", null, { timeout: 120000 });
  await page.waitForTimeout(2500);
  const total = (Date.now() - started) / 1000;
  const video = page.video();
  await ctx.close(); await browser.close();
  const webm = await video.path();
  // skip the first moment of page loading, then encode H.264 at 30 fps for the social apps
  execFileSync("ffmpeg", ["-v", "error", "-y", "-ss", "0.8", "-i", webm, "-t", String(Math.max(5, total - 0.8)),
    "-r", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", "-movflags", "+faststart", out]);
  fs.rmSync(dir, { recursive: true, force: true });
  console.log(`Saved ${out} (${total.toFixed(1)} s)`);
})().catch((e) => { console.error(e); process.exit(1); });

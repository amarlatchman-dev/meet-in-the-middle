/*
  Halfwise group plans API.

  One Durable Object per plan holds its members, votes and final choice. Plans delete
  themselves 7 days after creation. Only names and rounded locations are stored:
  no accounts, emails or IP addresses.

  Routes (JSON):
    POST   /plans                         create  -> { id, hostKey, memberId, memberKey }
    GET    /plans/:id[?v=N]               state (304-like {unchanged:true} when version N is current)
    POST   /plans/:id/members             join or add someone  -> { memberId, memberKey }
    PUT    /plans/:id/members/:mid        update name/location (that member's key, or host)
    DELETE /plans/:id/members/:mid        leave / remove (that member's key, or host)
    PUT    /plans/:id/settings            mode, goal, want, when (host)
    POST   /plans/:id/vote                { venue: {key,name,lat,lon,kind} | null }  (member)
    POST   /plans/:id/lock                { venue, when } or { venue: null } to unlock (host)
  Auth: header "Authorization: Bearer <memberKey or hostKey>".
*/

const ALLOWED_ORIGINS = new Set([
  "https://halfwise.app", "https://www.halfwise.app", "https://amarlatchman-dev.github.io",
  "http://localhost:8123", "http://localhost:8124",
]);
const MAX_MEMBERS = 10;
const TTL_MS = 7 * 24 * 3600 * 1000;
const MAX_BODY = 8 * 1024;

const json = (data, status, origin) => new Response(JSON.stringify(data), {
  status: status || 200,
  headers: {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
    ...(origin ? { "access-control-allow-origin": origin, "vary": "Origin" } : {}),
  },
});
const randId = (bytes) => {
  const b = crypto.getRandomValues(new Uint8Array(bytes));
  return btoa(String.fromCharCode(...b)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
};
const str = (v, max) => (typeof v === "string" ? v.replace(/[\u0000-\u001f\u007f]/g, "").trim().slice(0, max) : "");
const coord = (v, lim) => (typeof v === "number" && isFinite(v) && Math.abs(v) <= lim ? Math.round(v * 1e4) / 1e4 : null);
const cleanVenue = (v) => {
  if (!v || typeof v !== "object") return null;
  const lat = coord(v.lat, 85), lon = coord(v.lon, 180), key = str(v.key, 120), name = str(v.name, 80);
  return lat == null || lon == null || !key || !name ? null : { key, name, lat, lon, kind: str(v.kind, 80) };
};
const SETTINGS = {
  mode: (v) => (["drive", "transit", "bike", "walk"].includes(v) ? v : undefined),
  goal: (v) => (["fair", "balanced", "total"].includes(v) ? v : undefined),
  want: (v) => (["any", "food", "drinks", "coffee", "activity", "free"].includes(v) ? v : undefined),
  when: (v) => (typeof v === "string" && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(v) ? v : undefined),
};

export default {
  async fetch(req, env) {
    const origin = req.headers.get("origin");
    const okOrigin = origin && ALLOWED_ORIGINS.has(origin) ? origin : null;
    if (req.method === "OPTIONS") {
      return new Response(null, { status: okOrigin ? 204 : 403, headers: okOrigin ? {
        "access-control-allow-origin": okOrigin, "access-control-allow-methods": "GET, POST, PUT, DELETE",
        "access-control-allow-headers": "content-type, authorization", "access-control-max-age": "86400", "vary": "Origin",
      } : {} });
    }
    if (origin && !okOrigin) return json({ error: "origin not allowed" }, 403);
    const url = new URL(req.url);
    if (url.pathname === "/" || url.pathname === "/health") return json({ ok: true, service: "halfwise-api" }, 200, okOrigin);

    // rate limits per client IP (kept only in memory-backed counters, never stored with plans)
    const ip = req.headers.get("cf-connecting-ip") || "local";
    const isWrite = req.method !== "GET";
    const isCreate = req.method === "POST" && url.pathname === "/plans";
    const lim = env.LIMITER.get(env.LIMITER.idFromName(ip));
    const verdict = await (await lim.fetch("https://limiter/", { method: "POST", body: JSON.stringify({ write: isWrite, create: isCreate }) })).json();
    if (!verdict.ok) return json({ error: "Too many requests. Wait a minute and try again." }, 429, okOrigin);

    if (isWrite) {
      const len = +(req.headers.get("content-length") || 0);
      if (len > MAX_BODY) return json({ error: "request too large" }, 413, okOrigin);
    }
    const m = url.pathname.match(/^\/plans(?:\/([A-Za-z0-9_-]{22}))?(\/.*)?$/);
    if (!m) return json({ error: "not found" }, 404, okOrigin);
    let id = m[1];
    if (!id) {
      if (!isCreate) return json({ error: "not found" }, 404, okOrigin);
      id = randId(16);
    }
    const stub = env.PLAN.get(env.PLAN.idFromName(id));
    const fwd = new Request(`https://plan/${id}${m[2] || ""}${url.search}`, {
      method: req.method, headers: { authorization: req.headers.get("authorization") || "", "x-create": isCreate ? "1" : "" },
      body: isWrite ? (await req.text()).slice(0, MAX_BODY) : undefined,
    });
    const res = await stub.fetch(fwd);
    const out = new Response(res.body, res);
    if (okOrigin) { out.headers.set("access-control-allow-origin", okOrigin); out.headers.set("vary", "Origin"); }
    return out;
  },
};

// Simple fixed-window counters per IP: 240 requests/min, 60 writes/min, 20 new plans/hour.
export class Limiter {
  constructor(state) { this.state = state; this.win = {}; }
  async fetch(req) {
    const { write, create } = await req.json();
    const now = Date.now(), min = Math.floor(now / 60000), hour = Math.floor(now / 3600000);
    const bump = (k, w, max) => { const key = `${k}:${w}`; this.win[key] = (this.win[key] || 0) + 1; return this.win[key] <= max; };
    for (const k of Object.keys(this.win)) { const w = +k.split(":")[1]; if (w < min - 1 && w < hour - 1) delete this.win[k]; }
    const ok = bump("all", min, 240) && (!write || bump("w", min, 60)) && (!create || bump("c", hour, 20));
    return Response.json({ ok });
  }
}

export class Plan {
  constructor(state) { this.state = state; this.plan = null; }
  async load() { if (!this.plan) this.plan = (await this.state.storage.get("plan")) || null; return this.plan; }
  async save() { this.plan.version++; this.plan.updated = Date.now(); await this.state.storage.put("plan", this.plan); }
  async alarm() { await this.state.storage.deleteAll(); this.plan = null; }
  // public view: never includes keys
  view() {
    const p = this.plan;
    return { id: p.id, version: p.version, created: p.created, expires: p.created + TTL_MS, settings: p.settings,
      members: p.members.map(({ key, ...m }) => m), votes: p.votes, venues: p.venues, locked: p.locked };
  }
  who(req) {
    const tok = (req.headers.get("authorization") || "").replace(/^Bearer\s+/i, "");
    if (!tok) return {};
    if (tok === this.plan.hostKey) return { host: true };
    const m = this.plan.members.find((x) => x.key === tok);
    return m ? { member: m } : {};
  }
  async fetch(req) {
    const url = new URL(req.url);
    const parts = url.pathname.split("/").filter(Boolean); // [id, ...rest]
    const id = parts[0], rest = parts.slice(1);
    const body = req.method === "GET" || req.method === "DELETE" ? {} : await req.json().catch(() => null);
    if (body === null) return Response.json({ error: "invalid JSON" }, { status: 400 });

    if (req.headers.get("x-create") === "1") {
      if (await this.load()) return Response.json({ error: "try again" }, { status: 409 });
      const now = Date.now();
      this.plan = { id, version: 0, created: now, hostKey: randId(24), settings: {}, members: [], votes: {}, venues: [], locked: null };
      for (const [k, f] of Object.entries(SETTINGS)) { const v = f(body.settings && body.settings[k]); if (v !== undefined) this.plan.settings[k] = v; }
      await this.state.storage.setAlarm(now + TTL_MS);
      await this.save();
      return Response.json({ id, hostKey: this.plan.hostKey, plan: this.view() }, { status: 201 });
    }
    if (!(await this.load())) return Response.json({ error: "This plan has expired or doesn't exist." }, { status: 404 });
    const p = this.plan, who = this.who(req);

    if (req.method === "GET" && rest.length === 0) {
      const v = +url.searchParams.get("v");
      if (v && v === p.version) return Response.json({ unchanged: true, version: p.version });
      return Response.json(this.view());
    }
    if (rest[0] === "members" && req.method === "POST" && rest.length === 1) {
      if (p.members.length >= MAX_MEMBERS) return Response.json({ error: "This plan already has 10 people." }, { status: 409 });
      const m = { id: randId(9), key: randId(24), name: str(body.name, 40) || "Friend", lat: coord(body.lat, 85), lon: coord(body.lon, 180), label: str(body.label, 80) };
      p.members.push(m); await this.save();
      return Response.json({ memberId: m.id, memberKey: m.key, plan: this.view() }, { status: 201 });
    }
    if (rest[0] === "members" && rest[1]) {
      const m = p.members.find((x) => x.id === rest[1]);
      if (!m) return Response.json({ error: "not found" }, { status: 404 });
      if (!who.host && who.member !== m) return Response.json({ error: "not allowed" }, { status: 403 });
      if (req.method === "DELETE") {
        p.members = p.members.filter((x) => x !== m); delete p.votes[m.id];
      } else if (req.method === "PUT") {
        if ("name" in body) m.name = str(body.name, 40) || m.name;
        if ("label" in body) m.label = str(body.label, 80);
        if ("lat" in body || "lon" in body) { const la = coord(body.lat, 85), lo = coord(body.lon, 180); if (la != null && lo != null) { m.lat = la; m.lon = lo; } }
      } else return Response.json({ error: "not found" }, { status: 404 });
      await this.save(); return Response.json(this.view());
    }
    if (rest[0] === "settings" && req.method === "PUT") {
      if (!who.host) return Response.json({ error: "Only the host can change this." }, { status: 403 });
      for (const [k, f] of Object.entries(SETTINGS)) { const v = f(body[k]); if (v !== undefined) p.settings[k] = v; }
      await this.save(); return Response.json(this.view());
    }
    if (rest[0] === "vote" && req.method === "POST") {
      if (!who.member) return Response.json({ error: "Join the plan to vote." }, { status: 403 });
      const v = cleanVenue(body.venue);
      if (!v) delete p.votes[who.member.id];
      else {
        p.votes[who.member.id] = v.key;
        if (!p.venues.some((x) => x.key === v.key)) { p.venues.push(v); if (p.venues.length > 20) p.venues.shift(); }
      }
      await this.save(); return Response.json(this.view());
    }
    if (rest[0] === "lock" && req.method === "POST") {
      if (!who.host) return Response.json({ error: "Only the host can lock the plan." }, { status: 403 });
      const v = body.venue === null ? null : cleanVenue(body.venue);
      if (body.venue !== null && !v) return Response.json({ error: "invalid venue" }, { status: 400 });
      p.locked = v ? { venue: v, when: SETTINGS.when(body.when) || p.settings.when || null, at: Date.now() } : null;
      await this.save(); return Response.json(this.view());
    }
    return Response.json({ error: "not found" }, { status: 404 });
  }
}

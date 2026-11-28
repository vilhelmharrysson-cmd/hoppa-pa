// Fordonspositioner i realtid (GTFS Sweden 3 Realtime, SL) – för att känna av vilket fordon man sitter i.
//
//   GET /api/rt?op=near&lat=59.33&lon=18.06&r=80   → fordon inom r meter: linje, destination, kurs, fart
//
// Flödet anger bara tur-id; linje och destination slås upp i public/data/rt/sl-trips.json (byggs varje natt).
// Kräver hemligheten TRAFIKLAB_SWEDEN3_RT_KEY.

const FEED = "https://opendata.samtrafiken.se/gtfs-rt-sweden/sl/VehiclePositionsSweden.pb";
let feed = null, feedAt = 0, trips = null, tripsAt = 0;

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });

// --- minimal protobuf-läsare för GTFS-realtime FeedMessage → VehiclePosition ---
function reader(buf) {
  let p = 0;
  const dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength);
  const varint = () => { let r = 0, s = 1, b; do { b = buf[p++]; r += (b & 127) * s; s *= 128; } while (b & 128); return r; };
  return {
    get pos() { return p; }, end: buf.length, varint,
    tag() { const t = varint(); return [Math.floor(t / 8), t & 7]; },
    bytes() { const n = varint(); const s = buf.subarray(p, p + n); p += n; return s; },
    float() { const v = dv.getFloat32(p, true); p += 4; return v; },
    skip(w) { if (w === 0) varint(); else if (w === 1) p += 8; else if (w === 2) { const n = varint(); p += n; } else if (w === 5) p += 4; else throw new Error("wire " + w); },
  };
}
const td = new TextDecoder();
function parseVehicle(b) {
  const v = {}; const r = reader(b);
  while (r.pos < r.end) {
    const [f, w] = r.tag();
    if (f === 1 && w === 2) { const t = reader(r.bytes()); while (t.pos < t.end) { const [g, x] = t.tag(); if (g === 1 && x === 2) v.trip = td.decode(t.bytes()); else t.skip(x); } }
    else if (f === 2 && w === 2) { const q = reader(r.bytes()); while (q.pos < q.end) { const [g, x] = q.tag();
        if (x === 5 && g === 1) v.lat = q.float(); else if (x === 5 && g === 2) v.lon = q.float();
        else if (x === 5 && g === 3) v.bearing = q.float(); else if (x === 5 && g === 5) v.speed = q.float(); else q.skip(x); } }
    else if (f === 5 && w === 0) v.ts = r.varint();
    else if (f === 8 && w === 2) { const q = reader(r.bytes()); while (q.pos < q.end) { const [g, x] = q.tag(); if (g === 1 && x === 2) v.id = td.decode(q.bytes()); else q.skip(x); } }
    else r.skip(w);
  }
  return v;
}
function parseFeed(buf) {
  const out = []; const r = reader(buf);
  while (r.pos < r.end) {
    const [f, w] = r.tag();
    if (f === 2 && w === 2) { const e = reader(r.bytes()); while (e.pos < e.end) { const [g, x] = e.tag(); if (g === 4 && x === 2) out.push(parseVehicle(e.bytes())); else e.skip(x); } }
    else r.skip(w);
  }
  return out;
}

async function vehicles(env) {
  if (feed && Date.now() - feedAt < 10000) return feed;
  const r = await fetch(`${FEED}?key=${encodeURIComponent(env.TRAFIKLAB_SWEDEN3_RT_KEY)}`, { headers: { "accept-encoding": "gzip" } });
  if (!r.ok) throw new Error(`realtidsflödet svarade ${r.status}`);
  let buf = new Uint8Array(await r.arrayBuffer());
  if (buf[0] === 0x1f && buf[1] === 0x8b) buf = new Uint8Array(await new Response(new Blob([buf]).stream().pipeThrough(new DecompressionStream("gzip"))).arrayBuffer());
  feed = parseFeed(buf); feedAt = Date.now();
  return feed;
}

async function tripTable(req, env) {
  if (trips && Date.now() - tripsAt < 3600e3) return trips;
  const r = await env.ASSETS.fetch(new Request(new URL("/data/rt/sl-trips.json", req.url)));
  const j = r.ok ? await r.json() : { lines: {} };
  trips = new Map();
  for (const [k, list] of Object.entries(j.lines || {})) {
    let id = BigInt(list[0]); trips.set(id.toString(), k);
    for (let i = 1; i < list.length; i++) { id += BigInt(list[i]); trips.set(id.toString(), k); }
  }
  tripsAt = Date.now();
  return trips;
}

const dist = (a, b) => Math.hypot((a.lat - b.lat) * 111320, (a.lon - b.lon) * 111320 * Math.cos(a.lat * Math.PI / 180));

export async function handle(req, env = {}) {
  if (!env.TRAFIKLAB_SWEDEN3_RT_KEY) return json({ error: "TRAFIKLAB_SWEDEN3_RT_KEY saknas" }, 503);
  const q = Object.fromEntries(new URL(req.url).searchParams);
  try {
    if (q.op === "near") {
      const here = { lat: +q.lat, lon: +q.lon }, rad = Math.min(500, +q.r || 80);
      if (!isFinite(here.lat) || !isFinite(here.lon)) return json({ error: "lat och lon krävs" }, 400);
      const [vs, tt] = await Promise.all([vehicles(env), tripTable(req, env)]);
      const now = Date.now() / 1000, out = [];
      for (const v of vs) {
        if (v.lat == null) continue;
        const d = dist(here, v); if (d > rad) continue;
        const k = v.trip ? tt.get(v.trip) : null; const [line, dest] = k ? k.split("|") : ["", ""];
        out.push({ line, dest, dist: Math.round(d), bearing: v.bearing ?? null, speed: v.speed ?? null,
                   age: v.ts ? Math.round(now - v.ts) : null, trip: v.trip || "", vehicle: v.id || "" });
      }
      out.sort((a, b) => a.dist - b.dist);
      return json({ vehicles: out.slice(0, 20), feedAge: Math.round((Date.now() - feedAt) / 1000) });
    }
    return json({ error: "okänd op" }, 400);
  } catch (e) {
    return json({ error: e.message }, 502);
  }
}

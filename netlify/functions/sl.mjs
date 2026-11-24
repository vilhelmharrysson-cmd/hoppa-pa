// Hoppa på – liten server mot SL:s öppna API:er via Trafiklab (ingen nyckel krävs):
//   transport.integration.sl.se (hållplatser, avgångar)
//   deviations.integration.sl.se (störningar)
//   journeyplanner.integration.sl.se (reseplanerare)
//
// GET /api/sl?op=departures&stop=Hornstull&line=66[&lat=..&lon=..]
// GET /api/sl?op=situations&line=66
// GET /api/sl?op=journey&fromLat=..&fromLon=..&toStop=Hornstull[&toLat=..&toLon=..]
// Svaren har samma form som /api/vt, så appen kan använda båda likadant.

const cache = new Map();
class HttpError extends Error { constructor(status, msg) { super(msg); this.status = status; } }

async function get(url, ttlMs = 0) {
  const hit = cache.get(url);
  if (ttlMs && hit && hit.expires > Date.now()) return hit.value;
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  if (!res.ok) throw new HttpError(502, `SL svarade ${res.status}`);
  const value = await res.json();
  if (ttlMs) cache.set(url, { value, expires: Date.now() + ttlMs });
  return value;
}

const norm = (s) => (s || "").toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]/g, "");
const dist = (a, b) => Math.hypot((a.lat - b.lat) * 111320, (a.lon - b.lon) * 111320 * Math.cos(a.lat * Math.PI / 180));

// Hållplatsnamn -> SL-site. Flera kan heta likadant, så närmast angiven position vinner.
async function site(name, lat, lon) {
  const sites = await get("https://transport.integration.sl.se/v1/sites?expand=false", 24 * 3600_000);
  const want = norm(name);
  let cands = sites.filter((s) => norm(s.name) === want);
  if (!cands.length) cands = sites.filter((s) => norm(s.name).startsWith(want));
  if (!cands.length) throw new HttpError(404, `Hittade ingen SL-hållplats som heter ${name}`);
  if (lat && lon && cands.length > 1) {
    const p = { lat: +lat, lon: +lon };
    cands.sort((a, b) => dist(p, a) - dist(p, b));
  }
  return cands[0];
}

// SL ger lokal tid utan zon i avgångar; gör om till ISO med svensk tidszon.
function isoLocal(s) {
  if (!s || /[zZ]|[+-]\d\d:?\d\d$/.test(s)) return s || null;
  const d = new Date(s + "Z");
  const fmt = new Intl.DateTimeFormat("sv-SE", { timeZone: "Europe/Stockholm", timeZoneName: "longOffset" });
  const off = (fmt.formatToParts(d).find((p) => p.type === "timeZoneName")?.value || "GMT+01:00").replace("GMT", "") || "+00:00";
  return s + (off.length === 3 ? off + ":00" : off);
}

async function departures(q) {
  const s = await site(q.stop, q.lat, q.lon);
  const j = await get(`https://transport.integration.sl.se/v1/sites/${s.id}/departures?forecast=90`, 20_000);
  const line = (q.line || "").toString();
  const out = (j.departures || [])
    .filter((d) => !line || d.line?.designation === line)
    .map((d) => ({
      line: d.line?.designation, direction: d.destination || d.direction,
      planned: isoLocal(d.scheduled), estimated: isoLocal(d.expected),
      platform: d.stop_point?.designation || null,
      cancelled: d.state === "CANCELLED",
      realtime: d.state === "EXPECTED" || d.state === "ATSTOP",
    }));
  return { stop: s.name, stopGid: s.gid, departures: out.slice(0, 12) };
}

async function situations(q) {
  const line = (q.line || "").toString();
  const list = await get(`https://deviations.integration.sl.se/v1/messages?line=${encodeURIComponent(line)}`, 120_000);
  const now = Date.now();
  return {
    line,
    situations: (list || [])
      .filter((m) => !m.publish?.from || Date.parse(m.publish.from) <= now + 2 * 3600_000)
      .map((m) => {
        const v = (m.message_variants || []).find((x) => x.language === "sv") || (m.message_variants || [])[0] || {};
        return { id: m.deviation_case_id, title: v.header, description: v.details, start: m.publish?.from, end: m.publish?.upto,
                 stops: (m.scope?.stop_areas || []).map((s) => s.name) };
      }),
  };
}

async function journey(q) {
  const dest = await site(q.toStop, q.toLat, q.toLon);
  const lon = (+q.fromLon).toFixed(5), lat = (+q.fromLat).toFixed(5);
  const url = "https://journeyplanner.integration.sl.se/v2/trips?" + new URLSearchParams({
    type_origin: "coord", name_origin: `${lon}:${lat}:WGS84[dd.ddddd]`,
    type_destination: "any", name_destination: String(dest.gid), calc_number_of_trips: "3",
  });
  const j = await get(url);
  const short = (n) => (n || "").split(",")[0];
  const journeys = (j.journeys || []).map((jr) => {
    const legs = (jr.legs || []).map((l) => {
      const tr = l.transportation || {};
      const walk = /footpath|fussweg|gang/i.test(tr.product?.name || "") || (!tr.disassembledName && !tr.number);
      if (walk) return { type: "walk", minutes: Math.round((l.duration || 0) / 60), meters: l.distance || null, label: "Gå" };
      return {
        type: "ride", line: tr.disassembledName || tr.number, direction: tr.destination?.name || "",
        mode: tr.product?.name, from: short(l.origin?.name), to: short(l.destination?.name),
        departs: l.origin?.departureTimeEstimated || l.origin?.departureTimePlanned,
        arrives: l.destination?.arrivalTimeEstimated || l.destination?.arrivalTimePlanned,
        cancelled: !!l.isCancelled,
      };
    }).filter((l) => l.type === "ride" || l.minutes > 0);
    const rides = (jr.legs || []);
    return {
      departs: rides[0]?.origin?.departureTimeEstimated || rides[0]?.origin?.departureTimePlanned,
      arrives: rides.at(-1)?.destination?.arrivalTimeEstimated || rides.at(-1)?.destination?.arrivalTimePlanned,
      legs,
    };
  });
  return { to: dest.name, journeys };
}

export default async (req) => {
  const q = Object.fromEntries(new URL(req.url).searchParams);
  try {
    let body;
    if (q.op === "departures" && q.stop) body = await departures(q);
    else if (q.op === "situations" && q.line) body = await situations(q);
    else if (q.op === "journey" && q.toStop && q.fromLat && q.fromLon) body = await journey(q);
    else throw new HttpError(400, "Okänd fråga. Använd op=departures, op=situations eller op=journey.");
    return Response.json(body, { headers: { "Cache-Control": "public, max-age=15" } });
  } catch (e) {
    const status = e.status || 500;
    if (status >= 500) console.error(e);
    return Response.json({ error: e.message }, { status });
  }
};

export const config = { path: "/api/sl" };

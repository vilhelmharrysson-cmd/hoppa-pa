// Tågavgångar i realtid via Trafiklab Realtime APIs (alla operatörer: SJ, VR, Mälartåg, Västtågen m.fl.).
//
//   GET /api/trv?op=departures&name=Skövde&lat=58.39&lon=13.85   → nästa tåg från stationen
//
// Stationen slås upp på namn (Stop Lookup) och väljs som den tågstation som ligger närmast punkten.
// Kräver hemligheten TRAFIKLAB_RT_KEY (nyckel för "Trafiklab Realtime APIs" på trafiklab.se).

const BASE = "https://realtime-api.trafiklab.se/v1";
let ENV = {};
const areaCache = new Map();

const json = (data, status = 200, maxAge = 0) =>
  new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json; charset=utf-8",
    "cache-control": maxAge ? `public, max-age=${maxAge}` : "no-store" } });

async function get(path) {
  const r = await fetch(`${BASE}${path}${path.includes("?") ? "&" : "?"}key=${encodeURIComponent(ENV.TRAFIKLAB_RT_KEY)}`,
    { headers: { accept: "application/json" } });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.message || j.error || `Trafiklab svarade ${r.status}`);
  return j;
}

const dist = (a, b) => Math.hypot((a.lat - b.lat) * 111320, (a.lon - b.lon) * 111320 * Math.cos(a.lat * Math.PI / 180));

// "Skövde C" → "Skövde"; "Södertälje syd" behålls
const searchName = (n) => n.replace(/\s+(C|Central|centralstation|station)$/i, "").trim();

async function findArea(name, lat, lon) {
  const key = `${name}|${lat.toFixed(3)}|${lon.toFixed(3)}`;
  if (areaCache.has(key)) return areaCache.get(key);
  const j = await get(`/stops/name/${encodeURIComponent(searchName(name))}`);
  const here = { lat, lon };
  let best = null, bd = Infinity;
  for (const g of j.stop_groups || []) {
    // bara hållplatsområden där det går tåg; närmast vinner
    if (!(g.transport_modes || []).map((m) => String(m).toUpperCase()).includes("TRAIN")) continue;
    for (const s of g.stops || []) {
      if (s.lat == null) continue;
      const d = dist(here, { lat: s.lat, lon: s.lon });
      if (d < bd) { bd = d; best = { id: g.id, name: g.name }; }
    }
  }
  const area = bd <= 2500 ? best : null;
  areaCache.set(key, area);
  return area;
}

export async function handle(req, env = {}) {
  ENV = env;
  if (!ENV.TRAFIKLAB_RT_KEY) return json({ error: "TRAFIKLAB_RT_KEY saknas" }, 503);
  const q = Object.fromEntries(new URL(req.url).searchParams);
  try {
    if (q.op === "departures") {
      const lat = +q.lat, lon = +q.lon;
      if (!q.name || !isFinite(lat) || !isFinite(lon)) return json({ error: "name, lat och lon krävs" }, 400);
      const area = await findArea(q.name, lat, lon);
      if (!area) return json({ error: "ingen tågstation hittades" }, 404);
      const j = await get(`/departures/${encodeURIComponent(area.id)}`);
      const out = [];
      for (const d of j.departures || []) {
        const r = d.route || {};
        if (String(r.transport_mode || "").toUpperCase() !== "TRAIN") continue;
        // pendeltåg (SL) hör inte till långfärdsturen
        if (r.transport_mode_code === 109 || /^(SL|Storstockholms Lokaltrafik)$/i.test(d.agency?.operator || "")) continue;
        out.push({
          planned: d.scheduled,
          estimated: d.realtime && d.realtime !== d.scheduled ? d.realtime : null,
          to: r.direction || r.destination?.name || "",
          product: [r.name || (d.agency?.operator || "").replace(/ AB$/, "") || "", d.trip?.technical_number || r.designation || ""].filter(Boolean).join(" "),
          track: d.realtime_platform?.designation || d.scheduled_platform?.designation || "",
          cancelled: !!d.canceled,
          realtime: !!d.is_realtime,
        });
      }
      return json({ station: area.name, departures: out.slice(0, 15) }, 200, 30);
    }
    return json({ error: "okänd op" }, 400);
  } catch (e) {
    return json({ error: e.message }, 502);
  }
}

// Hoppa på – liten server mot Västtrafiks API:er (Planera Resa v4 och Störning v1).
// Nyckeln läses från miljövariabeln VT_AUTH_KEY (Västtrafiks "Autentiseringsnyckel",
// alltså base64(klientidentifierare:hemlighet)). Den skickas aldrig till webbläsaren.
//
// GET /api/vt?op=departures&stop=Järntorget&line=11[&lat=..&lon=..]
// GET /api/vt?op=situations&line=11
// GET /api/vt?op=journey&fromLat=..&fromLon=..&toStop=Järntorget[&toLat=..&toLon=..]

const BASE = "https://ext-api.vasttrafik.se";
let token = null;          // { value, expires }
let ENV = {};
const cache = new Map();   // nyckel -> { value, expires }

async function getToken() {
  if (token && token.expires > Date.now() + 60_000) return token.value;
  const key = ENV.VT_AUTH_KEY;
  if (!key) throw new HttpError(500, "VT_AUTH_KEY saknas. Lägg in Västtrafiks autentiseringsnyckel som miljövariabel på servern.");
  const res = await fetch(`${BASE}/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded", Authorization: `Basic ${key}` },
    body: "grant_type=client_credentials",
  });
  if (!res.ok) throw new HttpError(502, `Kunde inte hämta token från Västtrafik (${res.status}). Kontrollera nyckeln.`);
  const j = await res.json();
  token = { value: j.access_token, expires: Date.now() + (j.expires_in || 3600) * 1000 };
  return token.value;
}

async function vt(path, params = {}, ttlMs = 0) {
  const url = new URL(BASE + path);
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue;
    if (Array.isArray(v)) v.forEach((x) => url.searchParams.append(k, x));
    else url.searchParams.set(k, v);
  }
  const ck = url.toString();
  const hit = cache.get(ck);
  if (ttlMs && hit && hit.expires > Date.now()) return hit.value;
  let res = await fetch(ck, { headers: { Authorization: `Bearer ${await getToken()}`, Accept: "application/json" } });
  if (res.status === 401) { token = null; res = await fetch(ck, { headers: { Authorization: `Bearer ${await getToken()}`, Accept: "application/json" } }); }
  if (!res.ok) throw new HttpError(502, `Västtrafik svarade ${res.status} på ${path}`);
  const value = await res.json();
  if (ttlMs) cache.set(ck, { value, expires: Date.now() + ttlMs });
  return value;
}

class HttpError extends Error { constructor(status, msg) { super(msg); this.status = status; } }

const norm = (s) => (s || "").toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]/g, "");

// Hållplatsnamn (från OpenStreetMap) -> Västtrafiks hållplatsområde (gid). Cachas länge.
async function stopArea(name, lat, lon) {
  const r = await vt("/pr/v4/locations/by-text", { q: name, types: "stoparea", limit: 10, latitude: lat, longitude: lon }, 24 * 3600_000);
  const list = r.results || [];
  const want = norm(name);
  const exact = list.find((l) => norm(l.name.split(",")[0]) === want)
    || list.find((l) => norm(l.name).startsWith(want))
    || list[0];
  if (!exact) throw new HttpError(404, `Hittade ingen hållplats som heter ${name}`);
  return exact;
}

const t = (x) => x || null;

async function departures(q) {
  const area = await stopArea(q.stop, q.lat, q.lon);
  const r = await vt(`/pr/v4/stop-areas/${area.gid}/departures`, { timeSpanInMinutes: 90, limit: 60, maxDeparturesPerLineAndDirection: 4 }, 20_000);
  const line = (q.line || "").toString();
  const out = (r.results || [])
    .filter((d) => !line || d.serviceJourney?.line?.shortName === line || d.serviceJourney?.line?.designation === line)
    .map((d) => ({
      line: d.serviceJourney?.line?.shortName || d.serviceJourney?.line?.designation,
      direction: d.serviceJourney?.directionDetails?.shortDirection || d.serviceJourney?.direction,
      planned: t(d.plannedTime), estimated: t(d.estimatedTime),
      platform: d.stopPoint?.platform || null,
      cancelled: !!d.isCancelled,
      realtime: !!d.estimatedTime,
    }));
  return { stop: area.name, stopGid: area.gid, departures: out.slice(0, 12) };
}

async function situations(q) {
  const all = await vt("/ts/v1/traffic-situations", {}, 120_000);
  const line = (q.line || "").toString();
  const now = Date.now();
  const list = (Array.isArray(all) ? all : all.results || [])
    .filter((s) => (s.affectedLines || []).some((l) => l.designation === line || l.name === line))
    .filter((s) => !s.startTime || Date.parse(s.startTime) <= now + 2 * 3600_000)   // pågående eller strax
    .map((s) => ({
      id: s.situationNumber, title: s.title, description: s.description, severity: s.severity,
      start: s.startTime, end: s.endTime,
      stops: [...new Set((s.affectedStopPoints || []).map((p) => p.name).filter(Boolean))].slice(0, 20),
    }));
  return { line, situations: list };
}

async function journey(q) {
  const dest = await stopArea(q.toStop, q.toLat, q.toLon);
  const r = await vt("/pr/v4/journeys", {
    originLatitude: q.fromLat, originLongitude: q.fromLon, destinationGid: dest.gid, limit: 3,
  });
  const name = (c) => c?.stopPoint?.name || null;
  const time = (c) => c?.estimatedTime || c?.plannedTime || null;
  const journeys = (r.results || []).map((j) => {
    const legs = [];
    const walk = (l, label) => l && legs.push({ type: "walk", minutes: l.estimatedDurationInMinutes ?? l.plannedDurationInMinutes, meters: l.distanceInMeters, label });
    walk(j.departureAccessLink, "Gå till hållplatsen");
    (j.tripLegs || []).forEach((leg, i) => {
      legs.push({
        type: "ride", line: leg.serviceJourney?.line?.shortName, direction: leg.serviceJourney?.directionDetails?.shortDirection || leg.serviceJourney?.direction,
        mode: leg.serviceJourney?.line?.transportMode,
        colors: { bg: leg.serviceJourney?.line?.backgroundColor, fg: leg.serviceJourney?.line?.foregroundColor },
        from: name(leg.origin), to: name(leg.destination),
        departs: time(leg.origin), arrives: time(leg.destination), cancelled: !!leg.isCancelled,
      });
      const c = (j.connectionLinks || []).find((x) => x.journeyLegIndex === leg.journeyLegIndex + 1);
      walk(c, "Byte");
    });
    walk(j.arrivalAccessLink, "Gå till målet");
    const first = j.tripLegs?.[0], last = j.tripLegs?.[j.tripLegs.length - 1];
    return { departs: time(first?.origin), arrives: time(last?.destination), legs };
  });
  return { to: dest.name, journeys };
}

// Hållplatser nära en position och linjerna som avgår därifrån den närmaste halvtimmen.
const VT_MODE = { tram: "tram", bus: "bus", ferry: "boat", ship: "boat", boat: "boat" };
async function nearby(q) {
  const r = await vt("/pr/v4/locations/by-coordinates", { latitude: q.lat, longitude: q.lon, radiusInMeters: 700, types: "stoparea", limit: 6 }, 60_000);
  const areas = (r.results || []).filter((l) => l.gid).slice(0, 4);
  const seen = new Map();
  for (const a of areas) {
    let d; try { d = await vt(`/pr/v4/stop-areas/${a.gid}/departures`, { timeSpanInMinutes: 40, limit: 60, maxDeparturesPerLineAndDirection: 2 }, 20_000); } catch { continue; }
    for (const x of d.results || []) {
      const line = x.serviceJourney?.line?.shortName; if (!line) continue;
      const mode = VT_MODE[(x.serviceJourney?.line?.transportMode || "").toLowerCase()]; if (!mode) continue;
      const dir = x.serviceJourney?.directionDetails?.shortDirection || x.serviceJourney?.direction;
      const time = x.estimatedTime || x.plannedTime;
      const k = `${mode}|${line}|${dir}`;
      if (!seen.has(k) || Date.parse(time) < Date.parse(seen.get(k).time))
        seen.set(k, { line, mode, direction: dir, stop: a.name.split(",")[0], dist: a.straightLineDistanceInMeters ?? null, time, cancelled: !!x.isCancelled });
    }
  }
  const lines = [...seen.values()].sort((a, b) => Date.parse(a.time) - Date.parse(b.time));
  return { stops: areas.map((a) => ({ name: a.name.split(",")[0], dist: a.straightLineDistanceInMeters ?? null })), lines };
}

export async function handle(req, env = {}) {
  ENV = env;
  const q = Object.fromEntries(new URL(req.url).searchParams);
  try {
    let body;
    if (q.op === "departures" && q.stop) body = await departures(q);
    else if (q.op === "situations" && q.line) body = await situations(q);
    else if (q.op === "journey" && q.toStop && q.fromLat && q.fromLon) body = await journey(q);
    else if (q.op === "nearby" && q.lat && q.lon) body = await nearby(q);
    else throw new HttpError(400, "Okänd fråga. Använd op=departures, op=situations, op=journey eller op=nearby.");
    return Response.json(body, { headers: { "Cache-Control": "public, max-age=15" } });
  } catch (e) {
    const status = e.status || 500;
    if (status >= 500) console.error(e);
    return Response.json({ error: e.message }, { status });
  }
}

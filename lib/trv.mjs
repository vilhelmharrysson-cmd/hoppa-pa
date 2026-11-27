// Tågavgångar i realtid från Trafikverkets öppna API (alla operatörer: SJ, Mälartåg, Västtågen m.fl.).
//
//   GET /api/trv?op=departures&lat=58.39&lon=13.85      → nästa avgångar från stationen närmast punkten
//
// Kräver hemligheten TRV_API_KEY (gratis nyckel från api.trafikinfo.trafikverket.se).

const URL_ = "https://api.trafikinfo.trafikverket.se/v2/data.json";
let ENV = {};
let stations = null, stationsAt = 0;

const json = (data, status = 200, maxAge = 0) =>
  new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json; charset=utf-8",
    "cache-control": maxAge ? `public, max-age=${maxAge}` : "no-store" } });
const esc = (s) => String(s).replace(/[<>&"']/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;", "'": "&apos;" }[c]));

async function query(inner) {
  const body = `<REQUEST><LOGIN authenticationkey="${esc(ENV.TRV_API_KEY)}"/>${inner}</REQUEST>`;
  const r = await fetch(URL_, { method: "POST", headers: { "content-type": "text/xml" }, body });
  const j = await r.json().catch(() => ({}));
  const res = j?.RESPONSE?.RESULT?.[0];
  if (!r.ok || !res || res.ERROR) throw new Error(res?.ERROR?.MESSAGE || `Trafikverket svarade ${r.status}`);
  return res;
}

async function allStations() {
  if (stations && Date.now() - stationsAt < 864e5) return stations;
  const res = await query(`<QUERY objecttype="TrainStation" namespace="rail.infrastructure" schemaversion="1.5">
    <FILTER><EQ name="Advertised" value="true"/></FILTER>
    <INCLUDE>AdvertisedLocationName</INCLUDE><INCLUDE>LocationSignature</INCLUDE><INCLUDE>Geometry.WGS84</INCLUDE></QUERY>`);
  stations = {};
  for (const s of res.TrainStation || []) {
    const m = /POINT \(([-\d.]+) ([-\d.]+)\)/.exec(s.Geometry?.WGS84 || "");
    stations[s.LocationSignature] = { name: s.AdvertisedLocationName, lat: m ? +m[2] : null, lon: m ? +m[1] : null };
  }
  stationsAt = Date.now();
  return stations;
}

function nearest(st, lat, lon) {
  let best = null, bd = Infinity;
  for (const [sig, s] of Object.entries(st)) {
    if (s.lat == null) continue;
    const d = Math.hypot((s.lat - lat) * 111320, (s.lon - lon) * 111320 * Math.cos(lat * Math.PI / 180));
    if (d < bd) { bd = d; best = sig; }
  }
  return bd <= 2000 ? best : null;
}

export async function handle(req, env = {}) {
  ENV = env;
  if (!ENV.TRV_API_KEY) return json({ error: "TRV_API_KEY saknas" }, 503);
  const q = Object.fromEntries(new URL(req.url).searchParams);
  try {
    if (q.op === "departures") {
      const st = await allStations();
      const sig = q.sig && st[q.sig] ? q.sig : nearest(st, +q.lat, +q.lon);
      if (!sig) return json({ error: "ingen station i närheten" }, 404);
      const res = await query(`<QUERY objecttype="TrainAnnouncement" schemaversion="1.9" orderby="AdvertisedTimeAtLocation">
        <FILTER><AND>
          <EQ name="ActivityType" value="Avgang"/><EQ name="LocationSignature" value="${esc(sig)}"/><EQ name="Advertised" value="true"/>
          <GT name="AdvertisedTimeAtLocation" value="$dateadd(-00:10:00)"/><LT name="AdvertisedTimeAtLocation" value="$dateadd(03:00:00)"/>
        </AND></FILTER>
        <INCLUDE>AdvertisedTrainIdent</INCLUDE><INCLUDE>AdvertisedTimeAtLocation</INCLUDE><INCLUDE>EstimatedTimeAtLocation</INCLUDE>
        <INCLUDE>TimeAtLocation</INCLUDE><INCLUDE>ToLocation</INCLUDE><INCLUDE>ProductInformation</INCLUDE><INCLUDE>Operator</INCLUDE>
        <INCLUDE>TrackAtLocation</INCLUDE><INCLUDE>Canceled</INCLUDE><INCLUDE>Deviation</INCLUDE></QUERY>`);
      const out = [];
      for (const a of res.TrainAnnouncement || []) {
        if (a.TimeAtLocation) continue;                     // redan avgått
        const to = (a.ToLocation || []).sort((x, y) => (y.Priority ?? 0) - (x.Priority ?? 0))[0];
        out.push({
          train: a.AdvertisedTrainIdent,
          planned: a.AdvertisedTimeAtLocation,
          estimated: a.EstimatedTimeAtLocation || null,
          to: to ? (st[to.LocationName]?.name || to.LocationName) : "",
          product: (a.ProductInformation || []).map((p) => p.Description || p).join(", "),
          operator: a.Operator || "",
          track: a.TrackAtLocation || "",
          cancelled: !!a.Canceled,
          note: (a.Deviation || []).map((d) => d.Description || d).join(", "),
        });
      }
      return json({ station: st[sig].name, departures: out.slice(0, 15) }, 200, 30);
    }
    return json({ error: "okänd op" }, 400);
  } catch (e) {
    return json({ error: e.message }, 502);
  }
}

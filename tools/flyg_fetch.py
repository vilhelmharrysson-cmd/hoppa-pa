"""Hämtar flygbussarnas linjer (Vy Flygbussarna) ur Trafiklabs rikstäckande GTFS ("GTFS Sweden 3 Static").

Plockar ut alla turer till och från Landvetter, Arlanda, Bromma och Skavsta: hållplatser i ordning,
linjedragning (shapes) och hur ofta varje variant går. Körs i GitHub Actions (filen är stor).

  TRAFIKLAB_SWEDEN3_KEY=... python3 tools/flyg_fetch.py
Resultat: tools/flyg/patterns.json
"""
import collections, csv, io, json, os, sys, urllib.request, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "flyg", "patterns.json")
AIRPORTS = ("landvetter", "arlanda", "bromma", "skavsta")

def rows(z, name):
    with z.open(name) as f:
        yield from csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))

def main():
    key = os.environ.get("TRAFIKLAB_SWEDEN3_KEY")
    if not key: sys.exit("TRAFIKLAB_SWEDEN3_KEY saknas")
    path = "/tmp/sweden.zip"
    if not os.path.exists(path):
        req = urllib.request.Request(f"https://opendata.samtrafiken.se/gtfs-sweden/sweden.zip?key={key}",
                                     headers={"Accept-Encoding": "gzip", "User-Agent": "hoppa-pa-databygge"})
        with urllib.request.urlopen(req, timeout=900) as r, open(path, "wb") as f:
            while True:
                b = r.read(1 << 20)
                if not b: break
                f.write(b)
    z = zipfile.ZipFile(path)
    print("filer:", z.namelist(), flush=True)
    agencies = {a["agency_id"]: a["agency_name"] for a in rows(z, "agency.txt")}
    fb = {k for k, v in agencies.items() if "flygbuss" in v.lower() or v.strip().lower() in ("vy", "vy buss", "vy flygbussarna")}
    print("operatörer med flygbuss/vy:", {k: agencies[k] for k in fb}, flush=True)
    routes = {r["route_id"]: r for r in rows(z, "routes.txt") if r.get("agency_id") in fb}
    print(len(routes), "linjer:", [(r.get("route_short_name"), r.get("route_long_name")) for r in routes.values()], flush=True)
    trips = {t["trip_id"]: t for t in rows(z, "trips.txt") if t["route_id"] in routes}
    print(len(trips), "turer", flush=True)
    seqs = collections.defaultdict(list)
    for st in rows(z, "stop_times.txt"):
        if st["trip_id"] in trips:
            seqs[st["trip_id"]].append((int(st["stop_sequence"]), st["stop_id"], st.get("departure_time", "")))
    stop_ids = {s for v in seqs.values() for _, s, _ in v}
    stops = {}
    for s in rows(z, "stops.txt"):
        if s["stop_id"] in stop_ids:
            stops[s["stop_id"]] = {"name": s["stop_name"], "lat": float(s["stop_lat"]), "lon": float(s["stop_lon"])}
    shape_ids = {t.get("shape_id") for t in trips.values() if t.get("shape_id")}
    shapes = collections.defaultdict(list)
    if shape_ids and "shapes.txt" in z.namelist():
        for p in rows(z, "shapes.txt"):
            if p["shape_id"] in shape_ids:
                shapes[p["shape_id"]].append((int(p["shape_pt_sequence"]), round(float(p["shape_pt_lat"]), 6), round(float(p["shape_pt_lon"]), 6)))
    # mönster: samma linje och samma hållplatsföljd
    pats = {}
    for tid, seq in seqs.items():
        seq.sort(); t = trips[tid]; r = routes[t["route_id"]]
        names = [stops[s]["name"] for _, s, _ in seq if s in stops]
        if not any(a in " ".join(names).lower() for a in AIRPORTS): continue
        k = (t["route_id"], tuple(names))
        p = pats.setdefault(k, {"route": r.get("route_short_name") or "", "long": r.get("route_long_name") or "",
                                "agency": agencies.get(r.get("agency_id"), ""), "headsign": t.get("trip_headsign", ""),
                                "stops": [dict(stops[s], id=s, dep=d) for _, s, d in seq if s in stops],
                                "shape": [[a, b] for _, a, b in sorted(shapes.get(t.get("shape_id"), []))], "trips": 0})
        p["trips"] += 1
    out = sorted(pats.values(), key=lambda p: -p["trips"])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf8"), ensure_ascii=False)
    for p in out: print(p["trips"], "turer:", p["route"], p["long"], "|", p["stops"][0]["name"], "→", p["stops"][-1]["name"], len(p["stops"]), "hpl", len(p["shape"]), "punkter")

if __name__ == "__main__":
    main()

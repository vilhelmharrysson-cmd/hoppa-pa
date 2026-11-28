"""Tabell över dagens och morgondagens SL-turer: tur-id → linje och destination.

Realtidsflödet (GTFS Sweden 3 Realtime) anger bara tur-id för fordonen, så appen behöver den här
tabellen för att veta vilken linje ett fordon kör. Körs i den nattliga GitHub Action.

  TRAFIKLAB_SWEDEN3_KEY=... python3 tools/rt_trips.py [sweden.zip]
Resultat: public/data/rt/sl-trips.json  {"date": ..., "lines": {"linje|destination": [tur-id, ...]}}
Tur-id lagras sorterade: första som text, sedan skillnader mot föregående, så att filen blir liten.
"""
import collections, csv, datetime, io, json, os, sys, urllib.request, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "public", "data", "rt", "sl-trips.json")

def rows(z, name):
    with z.open(name) as f:
        yield from csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/sweden.zip"
    if not os.path.exists(path):
        key = os.environ.get("TRAFIKLAB_SWEDEN3_KEY") or sys.exit("TRAFIKLAB_SWEDEN3_KEY saknas")
        req = urllib.request.Request(f"https://opendata.samtrafiken.se/gtfs-sweden/sweden.zip?key={key}", headers={"Accept-Encoding": "gzip", "User-Agent": "hoppa-pa-databygge"})
        with urllib.request.urlopen(req, timeout=900) as r, open(path, "wb") as f:
            while (b := r.read(1 << 20)): f.write(b)
    z = zipfile.ZipFile(path)
    sl = {a["agency_id"] for a in rows(z, "agency.txt") if a["agency_name"].strip().lower() in ("sl", "storstockholms lokaltrafik")}
    print("SL:", sl)
    routes = {r["route_id"]: r.get("route_short_name") or "" for r in rows(z, "routes.txt") if r.get("agency_id") in sl}
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1))).date()
    days = {(today + datetime.timedelta(days=d)).strftime("%Y%m%d") for d in (0, 1)}
    active = set()
    if "calendar_dates.txt" in z.namelist():
        for c in rows(z, "calendar_dates.txt"):
            if c["date"] in days and c["exception_type"] == "1": active.add(c["service_id"])
    if "calendar.txt" in z.namelist():
        wd = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for c in rows(z, "calendar.txt"):
            for d in days:
                dt = datetime.datetime.strptime(d, "%Y%m%d").date()
                if c["start_date"] <= d <= c["end_date"] and c[wd[dt.weekday()]] == "1": active.add(c["service_id"])
    lines = collections.defaultdict(list)
    for t in rows(z, "trips.txt"):
        if t["route_id"] in routes and t["service_id"] in active:
            try: lines[f"{routes[t['route_id']]}|{t.get('trip_headsign', '')}"].append(int(t["trip_id"]))
            except ValueError: pass
    out = {}
    for k, ids in lines.items():
        # första id som text (för stort för JavaScripts tal), sedan skillnader
        ids.sort(); d = [str(ids[0])] + [b - a for a, b in zip(ids, ids[1:])]
        out[k] = d
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"date": sorted(days)[0], "lines": out}, open(OUT, "w"), separators=(",", ":"))
    print(len(out), "linje/destinationer,", sum(len(v) for v in out.values()), "turer,", os.path.getsize(OUT) // 1024, "kB")

if __name__ == "__main__":
    main()

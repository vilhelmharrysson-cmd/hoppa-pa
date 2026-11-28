"""Vägsträckning för flygbussarna: GTFS-datan har bara raka streck mellan hållplatserna, så vägen
räknas ut med OSRM (OpenStreetMap-baserad vägvisning) genom hållplatserna i ordning.
Körs i GitHub Actions efter flyg_fetch.py.

  python3 tools/flyg_route.py
Uppdaterar tools/flyg/patterns.json (fältet "road").
"""
import json, os, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "flyg", "patterns.json")
UA = {"User-Agent": "hoppa-pa-databygge/1.0 (open source travel guide prototype)"}

def route(stops):
    coords = ";".join(f"{s['lon']},{s['lat']}" for s in stops)
    url = f"https://router.project-osrm.org/route/v1/driving/{coords}?overview=full&geometries=geojson"
    for a in range(5):
        try:
            j = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read())
            if j.get("code") == "Ok":
                return [[round(lat, 6), round(lon, 6)] for lon, lat in j["routes"][0]["geometry"]["coordinates"]]
            print("  OSRM:", j.get("code"), j.get("message"))
        except Exception as e:
            print("  väntar:", e, flush=True)
        time.sleep(5 * (a + 1))
    return None

def main():
    pats = json.load(open(P, encoding="utf8"))
    for p in pats:
        if p.get("road"): continue
        r = route(p["stops"])
        if r: p["road"] = r
        print(p["route"], p["stops"][0]["name"], "→", p["stops"][-1]["name"], len(r or []), "punkter", flush=True)
        time.sleep(1.5)
    json.dump(pats, open(P, "w", encoding="utf8"), ensure_ascii=False)

if __name__ == "__main__":
    main()

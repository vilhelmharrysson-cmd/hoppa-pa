"""Bygger turer för flygbussarna (Vy Flygbussarna) och lägger in dem i public/data.

Körs efter gtfs_build.py. Underlag:
  tools/flyg/patterns.json   linjer, hållplatser och vägsträckning (flyg_fetch.py, flyg_route.py)
  tools/flyg_content.json    {"stops": {"Stad|Hållplats": {story, story_en, tips, tips_en}},
                              "looks": {linje: [{title, lat, lon, r, text, text_en}]}}
Hållplatser i stan som redan har en berättelse i kunskapsbanken (places_extra.json) får den,
med bilder och "Läs mer". I "titta ut" byts {sida}/{side} mot vänster/höger efter färdriktning.
"""
import json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "public", "data")
sys.path.insert(0, HERE)
from train_build import side_left, track_dist, SIDE  # noqa: E402

CITY = {"202": "Göteborg"}            # övriga linjer: Stockholm
SKIP = {"110", "981", "977"}          # Malmö, Linköping, Västerås – utanför appens städer

def slug(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def length_m(route):
    return sum(math.hypot((b[0] - a[0]) * 110540, (b[1] - a[1]) * 111320 * math.cos(math.radians(a[0]))) for a, b in zip(route, route[1:]))

def main():
    pp = os.path.join(HERE, "flyg", "patterns.json"); cp = os.path.join(HERE, "flyg_content.json")
    if not os.path.exists(pp) or not os.path.exists(cp):
        print("Inga flygbussturer än"); return
    pats = json.load(open(pp, encoding="utf8")); C = json.load(open(cp, encoding="utf8"))
    X = json.load(open(os.path.join(HERE, "places_extra.json"), encoding="utf8"))
    more = json.load(open(os.path.join(HERE, "more.json"), encoding="utf8"))
    tours, seen = [], set()
    for p in pats:
        line = p["route"]
        if line in SKIP or not p.get("road") or p["trips"] < 2: continue
        city = CITY.get(line, "Stockholm")
        first, last = p["stops"][0]["name"], p["stops"][-1]["name"]
        tid = f"{slug(city)}-flyg-{line}-{slug(last)}"
        if tid in seen: continue
        seen.add(tid)
        route = p["road"]
        mins = round(length_m(route) / (60 / 3.6) / 60 + len(p["stops"]) * 0.7)
        stops = []
        for k, s in enumerate(p["stops"]):
            st = {"name": s["name"], "lat": s["lat"], "lon": s["lon"]}
            own = C["stops"].get(f"{city}|{s['name']}")
            lib = X.get(city, {}).get(s["name"]) or {}
            story = (own or {}).get("story") or lib.get("story") or ""
            tips = (own or {}).get("tips") or lib.get("tips") or []
            if k == 0:
                story = f"Välkommen ombord på flygbuss {line} mot {last}! Resan tar ungefär {mins} minuter. " + (story or "Luta dig tillbaka och titta ut genom fönstret.")
            elif k == len(p["stops"]) - 1:
                story = f"Snart är vi framme vid ändhållplatsen {s['name']}." + (" " + story if story else "") + " Tack för att du åkte med!"
            if story:
                st.update({"story": story.strip(), "tips": tips, "dur": round(len(story) / 14, 1)})
                if own and own.get("story_en") and 0 < k < len(p["stops"]) - 1: st["story_en"] = own["story_en"]
                if own and own.get("tips_en"): st["tips_en"] = own["tips_en"]
                if lib.get("images"): st["images"] = lib["images"][:4]
                m = more.get(f"{city}|{s['name']}")
                if m: st["more"] = m
            stops.append(st)
        looks = []
        for n, L in enumerate(C["looks"].get(line, [])):
            left = side_left(route, L["lat"], L["lon"])
            if track_dist(route, L["lat"], L["lon"]) > 4000: continue
            lk = {"id": f"l{n}", "title": L.get("title", ""), "lat": L["lat"], "lon": L["lon"],
                  "r": max(L.get("r", 1200), round(track_dist(route, L["lat"], L["lon"]) + 300)),
                  "text": L["text"].replace("{sida}", SIDE["sv"][left])}
            if L.get("text_en"): lk["text_en"] = L["text_en"].replace("{side}", SIDE["en"][left])
            if L.get("images"): lk["images"] = L["images"][:1]
            looks.append(lk)
        tours.append({"id": tid, "group": f"{slug(city)}-flyg-{line}", "city": city, "mode": "flyg", "line": line,
                      "vehicle": "buss", "vehicleLong": "flygbuss", "operator": "Flygbussarna", "tab": "Flygbussarna",
                      "guide": None, "speedKmh": 60, "dwellSec": 40, "route": route, "stops": stops, "looks": looks,
                      "from": first, "to": last, "variant": "Mot " + last, "color": ["#0b5e43", "#ffffff"],
                      "source": "Linjer och hållplatser: Samtrafiken (GTFS Sverige) via Trafiklab. Vägen: © OpenStreetMaps bidragsgivare (ODbL), OSRM."})
    ip = os.path.join(DATA, "index.json"); index = json.load(open(ip, encoding="utf8"))
    index["tours"] = [e for e in index["tours"] if e.get("mode") != "flyg"]
    for t in tours:
        json.dump(t, open(os.path.join(DATA, "tours", t["id"] + ".json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
        index["tours"].append({k: t.get(k) for k in ("id", "group", "city", "mode", "line", "vehicleLong", "from", "to", "variant",
                                                     "color", "tab", "guide", "operator")} | {"guided": sum(1 for s in t["stops"] if s.get("story"))})
    json.dump(index, open(ip, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    print("Flygbussarna:", [(t["id"], len(t["stops"]), len(t["looks"])) for t in tours])

if __name__ == "__main__":
    main()

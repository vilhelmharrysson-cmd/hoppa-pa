"""Bygger tågturen Stockholm C ↔ Göteborg C (Västra stambanan) och lägger in den i public/data.

Körs efter gtfs_build.py. Innehållet kommer från tools/train_content.json:
  {"welcome": {"sg": text, "gs": text, "sg_en": ..., "gs_en": ...},
   "stations": [{"title": wikipedia-titel, "name": "Skövde C", "story", "story_en", "tips": [[vad, gång, lat?, lon?]], "tips_en": [...],
                 "images": [...]}],
   "looks": [{"title", "lat", "lon", "r", "text", "text_en", "images"?}]}
I "titta ut"-texterna byts {sida}/{side} mot vänster/höger beroende på färdriktning.
Banans sträckning: tools/train/vsb_route.json (OpenStreetMap, Västra stambanan via Grödingebanan).
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "public", "data")
ROUTE = json.load(open(os.path.join(HERE, "train", "vsb_route.json")))
SIDE = {"sv": {True: "vänster", False: "höger"}, "en": {True: "left", False: "right"}}

def xy(lat, lon): return (lon * 111320 * math.cos(math.radians(58.5)), lat * 110540)

def side_left(route, lat, lon):
    """True om punkten ligger till vänster om färdriktningen längs route."""
    P = [xy(*q) for q in route]; x, y = xy(lat, lon); best = (1e18, True)
    for (ax, ay), (bx, by) in zip(P, P[1:]):
        dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy or 1e-9
        t = max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / L))
        d = math.hypot(x - ax - t * dx, y - ay - t * dy)
        if d < best[0]: best = (d, dx * (y - ay) - dy * (x - ax) > 0)
    return best[1]

def km_along(route, lat, lon):
    P = [xy(*q) for q in route]; x, y = xy(lat, lon); best = (1e18, 0); cum = 0
    for (ax, ay), (bx, by) in zip(P, P[1:]):
        dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy or 1e-9
        t = max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / L))
        d = math.hypot(x - ax - t * dx, y - ay - t * dy)
        if d < best[0]: best = (d, cum + t * math.sqrt(L))
        cum += math.sqrt(L)
    return best[1]

def build(C, key, route):
    stations = sorted(C["stations"], key=lambda s: km_along(route, s["lat"], s["lon"]))
    stops = []
    for i, s in enumerate(stations):
        st = {"name": s["name"], "lat": s["lat"], "lon": s["lon"]}
        if s.get("story"):
            story, story_en = s["story"], s.get("story_en", "")
            if i == 0:
                story = C["welcome"][key] + " " + story
                story_en = (C["welcome"].get(key + "_en", "") + " " + story_en).strip()
            if i == len(stations) - 1:
                story += " " + C.get("farewell", {}).get("sv", "")
                story_en += " " + C.get("farewell", {}).get("en", "")
            st.update({"story": story.strip(), "tips": s.get("tips", [])})
            if story_en.strip(): st["story_en"] = story_en.strip()
            if s.get("tips_en"): st["tips_en"] = s["tips_en"]
            if s.get("images"): st["images"] = s["images"][:4]
        stops.append(st)
    looks = []
    for k, L in enumerate(C["looks"]):
        left = side_left(route, L["lat"], L["lon"])
        lk = {"id": f"l{k}", "lat": L["lat"], "lon": L["lon"], "r": L.get("r", 1500),
              "text": L["text"].replace("{sida}", SIDE["sv"][left])}
        if L.get("text_en"): lk["text_en"] = L["text_en"].replace("{side}", SIDE["en"][left])
        looks.append(lk)
    looks.sort(key=lambda L: km_along(route, L["lat"], L["lon"]))
    city = "Stockholm" if key == "sg" else "Göteborg"
    to = stations[-1]["name"]
    return {"id": f"{'stockholm' if key == 'sg' else 'goteborg'}-train-vsb-{'goteborg' if key == 'sg' else 'stockholm'}",
            "group": "train-vsb", "city": city, "cities": ["Stockholm", "Göteborg"], "mode": "train", "line": "Tåg",
            "vehicle": "tåg", "vehicleLong": "tåg", "operator": "Trafikverket", "tab": "Stockholm–Göteborg",
            "guide": None, "speedKmh": 150, "dwellSec": 45, "route": route, "stops": stops, "looks": looks,
            "from": stations[0]["name"], "to": to, "variant": "Mot " + to, "color": ["#1f3a5f", "#ffffff"],
            "source": "Banans sträckning: © OpenStreetMaps bidragsgivare (ODbL), Västra stambanan. Fakta: svenska Wikipedia"}

def main():
    p = os.path.join(HERE, "train_content.json")
    if not os.path.exists(p):
        print("Ingen tågtur än (tools/train_content.json saknas)"); return
    C = json.load(open(p, encoding="utf8"))
    tours = [build(C, "sg", ROUTE), build(C, "gs", ROUTE[::-1])]
    ip = os.path.join(DATA, "index.json")
    index = json.load(open(ip, encoding="utf8"))
    index["tours"] = [e for e in index["tours"] if e.get("mode") != "train"]
    for t in tours:
        json.dump(t, open(os.path.join(DATA, "tours", t["id"] + ".json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
        index["tours"].append({k: t.get(k) for k in ("id", "group", "city", "cities", "mode", "line", "vehicleLong", "from", "to",
                                                     "variant", "color", "tab", "guide", "operator")} |
                              {"guided": sum(1 for s in t["stops"] if s.get("story"))})
    json.dump(index, open(ip, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    print("Tågturen:", [(t["id"], len(t["stops"]), len(t["looks"])) for t in tours])

if __name__ == "__main__":
    main()

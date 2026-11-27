"""Faktaunderlag för tågturen Stockholm–Göteborg (Västra stambanan).

Hämtar från Wikidata alla platser med svensk Wikipedia-artikel inom några km från banan, och
stationerna längs banan, och sedan artikeltexterna från sv.wikipedia. Körs i GitHub Actions
(Wikipedia stryper anrop från molnmiljöer).

  python3 tools/train_research.py
Resultat: tools/research/train.json
  {"stations": [{title, lat, lon, km, text}], "places": [{title, lat, lon, km, dist, side_sg, text}]}
km = avstånd längs banan från Stockholm C, dist = meter från spåret,
side_sg = "vänster"/"höger" sett i färdriktningen Stockholm → Göteborg.
"""
import json, math, os, re, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROUTE = json.load(open(os.path.join(HERE, "train", "vsb_route.json")))
OUT = os.path.join(HERE, "research", "train.json")
UA = {"User-Agent": "hoppa-pa-research/1.3 (open source travel guide prototype)"}
TILE = 0.1
MAXD = 3500          # meter från spåret
MAX_MIN = float(os.environ.get("MAX_MIN", "150"))
# tågtyper som kan gå på sträckan (för korten "Om ditt tåg"); slås upp med Wikipedias sökning
TYPE_QUERIES = ["X 2000 snabbtåg", "SJ X 55 Regina snabbtåg", "Regina tåg Bombardier", "Coradia Nordic", "Stadler FLIRT X74",
                "Zefiro Express SJ", "SJ 3000", "Västtågen", "Mälartåg", "MTR Express", "SJ Regional", "Rc lok SJ"]

def xy(lat, lon): return (lon * 111320 * math.cos(math.radians(58.5)), lat * 110540)
P = [xy(*q) for q in ROUTE]
CUM = [0.0]
for a, b in zip(P, P[1:]): CUM.append(CUM[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))

def project(lat, lon):
    x, y = xy(lat, lon); best = (1e18, 0, 0)
    for i in range(len(P) - 1):
        (ax, ay), (bx, by) = P[i], P[i + 1]
        dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy or 1e-9
        t = max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / L))
        d = math.hypot(x - ax - t * dx, y - ay - t * dy)
        if d < best[0]:
            cross = dx * (y - ay) - dy * (x - ax)    # > 0: vänster om färdriktningen
            best = (d, CUM[i] + t * math.sqrt(L), cross)
    return best

def sparql(q):
    for a in range(5):
        try:
            r = urllib.request.urlopen(urllib.request.Request("https://query.wikidata.org/sparql",
                data=urllib.parse.urlencode({"query": q}).encode(),
                headers=dict(UA, **{"Accept": "application/sparql-results+json", "Content-Type": "application/x-www-form-urlencoded"})), timeout=120)
            return json.loads(r.read())["results"]["bindings"]
        except Exception as e:
            print("  väntar:", e, flush=True); time.sleep(20 * (a + 1))
    return []

def wp(params):
    params = dict(params, format="json", formatversion="2", maxlag="5")
    url = "https://sv.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)
    for a in range(6):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read())
        except Exception as e:
            print("  väntar:", e, flush=True); time.sleep(30 * (a + 1))
    return {}

def clean(text, n):
    text = re.split(r"\n==\s*(Se även|Referenser|Noter|Källor|Externa länkar|Vidare läsning|Litteratur)\s*==", text)[0]
    return re.sub(r"\n{3,}", "\n\n", text).strip()[:n]

def point(v):
    m = re.match(r"Point\(([-\d.eE]+) ([-\d.eE]+)\)", v)
    return (float(m.group(2)), float(m.group(1))) if m else None

def main():
    t0 = time.time()
    # 1) platser längs banan
    tiles = set()
    for lat, lon in ROUTE:
        a, b = math.floor(lat / TILE), math.floor(lon / TILE)
        for da in (-1, 0, 1):
            for db in (-1, 0, 1): tiles.add((a + da, b + db))
    print(len(tiles), "rutor", flush=True)
    pts = {}
    for a, b in sorted(tiles):
        s, w = round(a * TILE, 2), round(b * TILE, 2)
        q = f"""SELECT ?title ?coord ?inst WHERE {{ SERVICE wikibase:box {{ ?item wdt:P625 ?coord .
          bd:serviceParam wikibase:cornerSouthWest "Point({w} {s})"^^geo:wktLiteral .
          bd:serviceParam wikibase:cornerNorthEast "Point({round(w + TILE, 2)} {round(s + TILE, 2)})"^^geo:wktLiteral . }}
          ?art schema:about ?item ; schema:isPartOf <https://sv.wikipedia.org/> ; schema:name ?title .
          OPTIONAL {{ ?item wdt:P31 ?i . ?i rdfs:label ?inst . FILTER(lang(?inst)="sv") }} }}"""
        for r in sparql(q):
            p = point(r["coord"]["value"])
            if p: pts.setdefault(r["title"]["value"], (p, r.get("inst", {}).get("value", "")))
        time.sleep(1)
    print(len(pts), "artiklar i rutorna", flush=True)
    places = []
    for title, ((lat, lon), inst) in pts.items():
        d, km, cross = project(lat, lon)
        if d <= MAXD:
            places.append({"title": title, "lat": round(lat, 6), "lon": round(lon, 6), "km": round(km / 1000, 2),
                           "dist": round(d), "side_sg": "vänster" if cross > 0 else "höger", "type": inst})
    # 2) stationer (Västra stambanan och Grödingebanan)
    stations = []
    for line in ("Västra stambanan", "Grödingebanan"):
        for r in sparql(f"""SELECT ?title ?coord WHERE {{ ?line rdfs:label "{line}"@sv . ?st wdt:P81 ?line ; wdt:P625 ?coord .
            ?art schema:about ?st ; schema:isPartOf <https://sv.wikipedia.org/> ; schema:name ?title . }}"""):
            p = point(r["coord"]["value"])
            if not p: continue
            d, km, _ = project(*p)
            if d < 400 and not any(s["title"] == r["title"]["value"] for s in stations):
                stations.append({"title": r["title"]["value"], "lat": round(p[0], 6), "lon": round(p[1], 6), "km": round(km / 1000, 2)})
    stations.sort(key=lambda s: s["km"])
    print(len(places), "platser nära banan,", len(stations), "stationer", flush=True)
    # 3) texter: stationer i sin helhet, platser med ingress (de närmaste/viktigaste först)
    done = json.load(open(OUT, encoding="utf8")) if os.path.exists(OUT) else {"texts": {}}
    texts = done.get("texts", {})
    want = [(s["title"], 6000) for s in stations]
    places.sort(key=lambda p: (p["dist"] > 1500, p["km"]))
    want += [(p["title"], 2500) for p in places]
    for n, (title, cap) in enumerate(want):
        if title in texts: continue
        if time.time() - t0 > MAX_MIN * 60: print("tidsgräns"); break
        r = wp({"action": "query", "prop": "extracts", "explaintext": "1", "redirects": "1", "titles": title})
        for p in r.get("query", {}).get("pages", []):
            if p.get("extract"): texts[title] = clean(p["extract"], cap)
        time.sleep(1.2)
        if n % 50 == 0:
            print(n, "av", len(want), flush=True)
            json.dump({"stations": stations, "places": places, "texts": texts}, open(OUT, "w", encoding="utf8"), ensure_ascii=False)
    types = done.get("types", {})
    for qy in TYPE_QUERIES:
        if qy in types: continue
        r = wp({"action": "query", "list": "search", "srsearch": qy, "srlimit": "2"})
        for h in r.get("query", {}).get("search", [])[:2]:
            t = h["title"]
            if t not in texts:
                rr = wp({"action": "query", "prop": "extracts", "explaintext": "1", "redirects": "1", "titles": t})
                for p in rr.get("query", {}).get("pages", []):
                    if p.get("extract"): texts[t] = clean(p["extract"], 6000)
                time.sleep(1.2)
            types.setdefault(qy, []).append(t)
        time.sleep(1)
    json.dump({"stations": stations, "places": places, "texts": texts, "types": types}, open(OUT, "w", encoding="utf8"), ensure_ascii=False)
    print("Klart:", len(stations), "stationer,", len(places), "platser,", len(texts), "texter")

if __name__ == "__main__":
    main()

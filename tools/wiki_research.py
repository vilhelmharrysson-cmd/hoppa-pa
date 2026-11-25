"""Faktainsamling från svenska Wikipedia för alla hållplatser som saknar berättelse.

1. Alla Wikipedia-artiklar med koordinater i områdena hämtas från Wikidata med ett fåtal SPARQL-frågor
   (i stället för en geosökning per hållplats, som Wikipedia stryper hårt).
2. För varje hållplats räknas närliggande artiklar (inom 800 m) och kandidater för stadsdel/ort (inom 3 km) ut lokalt.
3. select_fill.py väljer de hållplatser som behövs för att fylla luckorna längs linjerna.
4. Ingresser hämtas bara för de valda hållplatsernas artiklar, med kontrollpunkt och tidsgräns
   (kör igen för att fortsätta).

Sparar till tools/research/research.json:
  {"stops": [{"city","name","lat","lon","lines","near":[[titel, m]], "area":[[titel, m]]}],
   "selected": [[stad, namn]], "articles": {titel: {"desc", "extract"}}}

Körs av .github/workflows/research.yml (manuellt).
"""
import json, math, os, re, sys, time, unicodedata, urllib.parse, urllib.request, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOURS = os.path.join(ROOT, "public", "data", "tours")
OUT = os.path.join(HERE, "research")
UA = {"User-Agent": "hoppa-pa-research/1.1 (open source travel guide prototype)"}
MAX_MIN = float(os.environ.get("MAX_MIN", "240"))
MAX_GAP = float(os.environ.get("MAX_GAP", "1200"))
AREA = re.compile(r"(stadsdel|tätort|småort|ort i|bostadsområde|primärområde|stadsområde|kommundel|ö i|förort|område i)", re.I)
TILE = 0.1

def norm(s):
    return re.sub(r"[^a-z0-9]+", "", unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower())

def dist(la1, lo1, la2, lo2):
    return math.hypot((la1 - la2) * 111320, (lo1 - lo2) * 111320 * math.cos(math.radians(la1)))

def get(url, data=None, headers=None, tries=6):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers=dict(UA, **(headers or {})))
            return json.loads(urllib.request.urlopen(req, timeout=120).read())
        except Exception as e:
            print("  väntar:", e, flush=True); time.sleep(30 * (a + 1))
    return {}

def sparql_tile(s, w):
    q = f"""SELECT ?title ?coord WHERE {{
  SERVICE wikibase:box {{ ?item wdt:P625 ?coord .
    bd:serviceParam wikibase:cornerSouthWest "Point({w} {s})"^^geo:wktLiteral .
    bd:serviceParam wikibase:cornerNorthEast "Point({round(w + TILE, 2)} {round(s + TILE, 2)})"^^geo:wktLiteral . }}
  ?art schema:about ?item ; schema:isPartOf <https://sv.wikipedia.org/> ; schema:name ?title .
}}"""
    r = get("https://query.wikidata.org/sparql", data=urllib.parse.urlencode({"query": q}).encode(),
            headers={"Accept": "application/sparql-results+json", "Content-Type": "application/x-www-form-urlencoded"})
    out = []
    for b in r.get("results", {}).get("bindings", []):
        m = re.match(r"Point\(([-\d.eE]+) ([-\d.eE]+)\)", b["coord"]["value"])
        if m: out.append((b["title"]["value"], float(m.group(2)), float(m.group(1))))
    return out

def wiki(params):
    params = dict(params, format="json", formatversion="2", maxlag="5")
    return get("https://sv.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params))

def save(path, data):
    json.dump(data, open(path, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))

def main():
    sys.path.insert(0, HERE)
    from content_sthlm import PLACES as STH
    G = json.load(open(os.path.join(HERE, "places_gbg.json"), encoding="utf8"))["places"]
    X = json.load(open(os.path.join(HERE, "places_extra.json"), encoding="utf8"))
    have = {"Göteborg": {norm(k) for k in list(G) + list(X.get("Göteborg", {}))},
            "Stockholm": {norm(k) for k in list(STH) + list(X.get("Stockholm", {}))}}
    info = collections.defaultdict(lambda: {"lines": set(), "lat": [], "lon": []})
    for f in os.listdir(TOURS):
        t = json.load(open(os.path.join(TOURS, f), encoding="utf8"))
        if t.get("guide"): continue
        for s in t["stops"]:
            i = info[(t["city"], s["name"])]; i["lines"].add(t["group"]); i["lat"].append(s["lat"]); i["lon"].append(s["lon"])
    stops = [{"city": c, "name": n, "lat": round(sum(i["lat"]) / len(i["lat"]), 5), "lon": round(sum(i["lon"]) / len(i["lon"]), 5),
              "lines": len(i["lines"])} for (c, n), i in info.items() if norm(n) not in have[c]]
    stops.sort(key=lambda s: -s["lines"])
    print(len(stops), "hållplatser att undersöka", flush=True)
    os.makedirs(OUT, exist_ok=True)
    rpath = os.path.join(OUT, "research.json")
    prev = json.load(open(rpath, encoding="utf8")) if os.path.exists(rpath) else {}

    if prev.get("selected"):
        stops, selected = prev["stops"], prev["selected"]
        print("Återanvänder tidigare geodata och urval", flush=True)
    else:
        # 1: artiklar med koordinater, ruta för ruta
        base = {(math.floor(s["lat"] / TILE), math.floor(s["lon"] / TILE)) for s in stops}
        tiles = sorted({(a + da, b + db) for a, b in base for da in (-1, 0, 1) for db in (-1, 0, 1)})
        print(len(tiles), "rutor att fråga Wikidata om", flush=True)
        pts = {}
        for n, (a, b) in enumerate(tiles):
            for title, la, lo in sparql_tile(round(a * TILE, 2), round(b * TILE, 2)): pts[title] = (la, lo)
            if n % 10 == 0: print(" ruta", n, len(pts), "artiklar", flush=True)
            time.sleep(1.0)
        print(len(pts), "artiklar med koordinater", flush=True)
        if len(pts) < 1000:
            sys.exit("För få artiklar från Wikidata, avbryter")
        # 2: närhet per hållplats
        grid = collections.defaultdict(list)
        for title, (la, lo) in pts.items(): grid[(int(la / 0.03), int(lo / 0.05))].append((title, la, lo))
        for s in stops:
            ga, gb = int(s["lat"] / 0.03), int(s["lon"] / 0.05)
            hits = [[title, round(dist(s["lat"], s["lon"], la, lo))]
                    for da in range(-2, 3) for db in range(-2, 3) for title, la, lo in grid[(ga + da, gb + db)]]
            hits = sorted([h for h in hits if h[1] <= 3000], key=lambda h: h[1])
            s["near"] = [h for h in hits if h[1] <= 800][:15]
            s["area_cand"] = hits[:60]
        # 3: urval
        import select_fill
        selected = select_fill.select(stops, MAX_GAP)
        print(len(selected), "hållplatser valda för nya berättelser", flush=True)
        prev = {"stops": stops, "selected": selected, "articles": {}}
        save(rpath, prev)

    # 4: ingresser för de valda hållplatsernas artiklar
    articles = prev.get("articles", {})
    sel = {tuple(k) for k in selected}
    want = set()
    for s in stops:
        if (s["city"], s["name"]) in sel:
            want |= {t for t, _ in s["near"][:10]} | {t for t, _ in s.get("area_cand", [])[:20]}
    todo = sorted(t for t in want if t not in articles)
    print(len(want), "artiklar behövs,", len(todo), "kvar att hämta", flush=True)
    t0 = time.time()
    for i in range(0, len(todo), 20):
        e = wiki({"action": "query", "prop": "extracts|description", "exintro": "1", "explaintext": "1", "exchars": "900",
                  "exlimit": "max", "titles": "|".join(todo[i:i + 20])})
        for p in e.get("query", {}).get("pages", []):
            articles[p["title"]] = {"desc": p.get("description", ""), "extract": p.get("extract", "")}
        if (i // 20) % 25 == 0:
            print(" ", i, "av", len(todo), f"{(time.time() - t0) / 60:.0f} min", flush=True)
            save(rpath, dict(prev, articles=articles))
        if time.time() - t0 > MAX_MIN * 60:
            save(rpath, dict(prev, articles=articles))
            print("Tidsgräns nådd, sparat. Kör igen för att fortsätta.", flush=True)
            return
        time.sleep(1.0)
    for s in stops:
        cand = s.get("area_cand") or []
        s["area"] = [[t, d] for t, d in cand if AREA.search(articles.get(t, {}).get("desc", "") + " " + articles.get(t, {}).get("extract", "")[:160])][:3]
    save(rpath, dict(prev, stops=stops, articles=articles))
    print("Klart:", len(stops), "hållplatser,", len(selected), "valda,", sum(1 for a in articles.values() if a.get("extract")), "artiklar med text")

if __name__ == "__main__":
    main()

"""Faktaunderlag för flygbussarna: platser med svensk Wikipedia-artikel nära vägen (Wikidata) och
artikeltexterna, plus hållplatsernas artiklar. Körs i GitHub Actions efter flyg_route.py.

  python3 tools/flyg_research.py
Resultat: tools/research/flyg.json
  {"routes": {linje: {"stops": [...], "places": [{title, lat, lon, km, dist, side, type}]}}, "texts": {titel: text}}
side = vänster/höger i färdriktningen från flygplatsen in mot staden.
"""
import json, math, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from train_research import sparql, wp, clean, point, TILE  # noqa: E402

P = os.path.join(HERE, "flyg", "patterns.json")
OUT = os.path.join(HERE, "research", "flyg.json")
MAXD = 1800
BAD = ("gata", "kvarter", "restaurang", "biograf", "hotell", "gränd", "skola", "tunnelbanestation", "företag", "organisation",
       "församling", "socken", "kommun", "distrikt", "tingslag", "trappa", "butik", "bostadsområde", "grannskap", "kolonilott")

def xy(lat, lon): return (lon * 111320 * math.cos(math.radians(59)), lat * 110540)

def measure(route):
    Q = [xy(*q) for q in route]; cum = [0.0]
    for a, b in zip(Q, Q[1:]): cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return Q, cum

def project(Q, cum, lat, lon):
    x, y = xy(lat, lon); best = (1e18, 0, 0)
    for i in range(len(Q) - 1):
        (ax, ay), (bx, by) = Q[i], Q[i + 1]
        dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy or 1e-9
        t = max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / L))
        d = math.hypot(x - ax - t * dx, y - ay - t * dy)
        if d < best[0]: best = (d, cum[i] + t * math.sqrt(L), dx * (y - ay) - dy * (x - ax))
    return best

def main():
    pats = json.load(open(P, encoding="utf8"))
    # en riktning per linje räcker: den som börjar vid flygplatsen
    chosen = {}
    air = lambda p: any(w in p["stops"][0]["name"].lower() for w in ("flygplats", "terminal", "airport", "skavsta"))
    for p in pats:
        if not p.get("road"): continue
        c = chosen.get(p["route"])
        if c is None or (air(p) and not air(c)) or (air(p) == air(c) and len(p["stops"]) > len(c["stops"])):
            chosen[p["route"]] = p
    done = json.load(open(OUT, encoding="utf8")) if os.path.exists(OUT) else {"texts": {}}
    texts = done.get("texts", {})
    out = {}
    for line, p in chosen.items():
        road = p["road"]; Q, cum = measure(road)
        tiles = {(math.floor(a / TILE), math.floor(b / TILE)) for a, b in road}
        pts = {}
        for a, b in sorted(tiles):
            s, w = round(a * TILE, 2), round(b * TILE, 2)
            q = f"""SELECT ?title ?coord ?inst WHERE {{ SERVICE wikibase:box {{ ?item wdt:P625 ?coord .
              bd:serviceParam wikibase:cornerSouthWest "Point({w} {s})"^^geo:wktLiteral .
              bd:serviceParam wikibase:cornerNorthEast "Point({round(w + TILE, 2)} {round(s + TILE, 2)})"^^geo:wktLiteral . }}
              ?art schema:about ?item ; schema:isPartOf <https://sv.wikipedia.org/> ; schema:name ?title .
              OPTIONAL {{ ?item wdt:P31 ?i . ?i rdfs:label ?inst . FILTER(lang(?inst)="sv") }} }}"""
            for r in sparql(q):
                pt = point(r["coord"]["value"])
                if pt: pts.setdefault(r["title"]["value"], (pt, r.get("inst", {}).get("value", "")))
            time.sleep(1)
        places = []
        for title, ((lat, lon), inst) in pts.items():
            if any(b in (inst or "").lower() for b in BAD): continue
            d, km, cross = project(Q, cum, lat, lon)
            if d <= MAXD:
                places.append({"title": title, "lat": round(lat, 6), "lon": round(lon, 6), "km": round(km / 1000, 2),
                               "dist": round(d), "side": "vänster" if cross > 0 else "höger", "type": inst})
        bins = {}
        for pl in places: bins.setdefault(int(pl["km"] // 1.5), []).append(pl)
        keep = []
        for b, ps in sorted(bins.items()): keep += sorted(ps, key=lambda q: q["dist"])[:5]
        out[line] = {"from": p["stops"][0]["name"], "to": p["stops"][-1]["name"], "stops": p["stops"], "places": keep}
        print(line, len(places), "platser,", len(keep), "valda", flush=True)
    want = [pl["title"] for r in out.values() for pl in r["places"]]
    for n, t in enumerate(want):
        if t in texts: continue
        rr = wp({"action": "query", "prop": "extracts", "explaintext": "1", "redirects": "1", "titles": t})
        for pg in rr.get("query", {}).get("pages", []):
            if pg.get("extract"): texts[t] = clean(pg["extract"], 2000)
        time.sleep(1.2)
        if n % 50 == 0: print(n, "av", len(want), flush=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"routes": out, "texts": texts}, open(OUT, "w", encoding="utf8"), ensure_ascii=False)
    print("Klart:", len(texts), "texter")

if __name__ == "__main__":
    main()

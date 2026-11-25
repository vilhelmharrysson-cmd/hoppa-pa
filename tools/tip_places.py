"""Kopplar "om du kliver av"-tipsen till en plats med koordinater, så att appen kan öppna
telefonens kartapp med gångväg dit.

Alla Wikipedia-artiklar med koordinater runt hållplatserna hämtas från Wikidata (några få SPARQL-frågor).
För varje tips väljs den artikel inom 2,5 km från hållplatsen vars namn står i tipstexten.
Resultat: tools/tip_places.json  {"Stad|tipstext": [lat, lon, artikel]}. Tips utan träff får i appen
en vanlig kartsökning på tipstexten i stället.

  python3 tools/tip_places.py
"""
import json, math, os, re, sys, time, unicodedata, urllib.parse, urllib.request, collections

HERE = os.path.dirname(os.path.abspath(__file__))
TOURS = os.path.join(os.path.dirname(HERE), "public", "data", "tours")
OUT = os.path.join(HERE, "tip_places.json")
UA = {"User-Agent": "hoppa-pa-tips/1.0 (open source travel guide prototype)",
      "Accept": "application/sparql-results+json", "Content-Type": "application/x-www-form-urlencoded"}
TILE = 0.1

def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()).strip()

def core(title):
    t = re.sub(r"\s*\(.*?\)", "", title)
    t = re.sub(r",\s*(Göteborg|Stockholm|Solna|Nacka|Mölndal|Lidingö|Sundbyberg|Huddinge|Danderyd|Partille|Kungälv|Täby|Järfälla|Sollentuna)$", "", t)
    return norm(t)

def dist(a, b):
    return math.hypot((a[0] - b[0]) * 110540, (a[1] - b[1]) * 111320 * math.cos(math.radians(a[0])))

def tile(s, w):
    q = f"""SELECT ?title ?coord WHERE {{ SERVICE wikibase:box {{ ?item wdt:P625 ?coord .
      bd:serviceParam wikibase:cornerSouthWest "Point({w} {s})"^^geo:wktLiteral .
      bd:serviceParam wikibase:cornerNorthEast "Point({round(w + TILE, 2)} {round(s + TILE, 2)})"^^geo:wktLiteral . }}
      ?art schema:about ?item ; schema:isPartOf <https://sv.wikipedia.org/> ; schema:name ?title . }}"""
    for a in range(5):
        try:
            r = urllib.request.urlopen(urllib.request.Request("https://query.wikidata.org/sparql",
                data=urllib.parse.urlencode({"query": q}).encode(), headers=UA), timeout=120)
            out = []
            for b in json.loads(r.read())["results"]["bindings"]:
                m = re.match(r"Point\(([-\d.eE]+) ([-\d.eE]+)\)", b["coord"]["value"])
                if m: out.append((b["title"]["value"], float(m.group(2)), float(m.group(1))))
            return out
        except Exception as e:
            print("  väntar:", e, flush=True); time.sleep(20 * (a + 1))
    return []

def main():
    tips = {}     # (stad, tips) -> hållplatskoordinat
    for f in os.listdir(TOURS):
        t = json.load(open(os.path.join(TOURS, f), encoding="utf8"))
        for s in t["stops"]:
            for tip in s.get("tips", []):
                tips.setdefault((t["city"], tip[0]), (s["lat"], s["lon"]))
    print(len(tips), "tips", flush=True)
    tiles = {(math.floor(la / TILE), math.floor(lo / TILE)) for la, lo in tips.values()}
    tiles = sorted({(a + da, b + db) for a, b in tiles for da in (-1, 0, 1) for db in (-1, 0, 1)})
    print(len(tiles), "rutor", flush=True)
    pts = {}
    for n, (a, b) in enumerate(tiles):
        for title, la, lo in tile(round(a * TILE, 2), round(b * TILE, 2)): pts[title] = (la, lo)
        time.sleep(1)
    print(len(pts), "artiklar med koordinater", flush=True)
    grid = collections.defaultdict(list)
    for title, p in pts.items(): grid[(int(p[0] / 0.03), int(p[1] / 0.05))].append((title, p, core(title)))
    out, hit = {}, 0
    for (city, tip), stop in tips.items():
        nt = " " + norm(tip) + " "
        best = None
        ga, gb = int(stop[0] / 0.03), int(stop[1] / 0.05)
        for da in range(-3, 4):
            for db in range(-3, 4):
                for title, p, c in grid[(ga + da, gb + db)]:
                    if len(c) < 4 or (" " + c + " ") not in nt: continue
                    d = dist(stop, p)
                    if d > 2500: continue
                    key = (len(c), -d)
                    if not best or key > best[0]: best = (key, title, p)
        if best:
            out[f"{city}|{tip}"] = [round(best[2][0], 6), round(best[2][1], 6), best[1]]; hit += 1
    json.dump(out, open(OUT, "w", encoding="utf8"), ensure_ascii=False, indent=0, sort_keys=True)
    print(f"Klart: {hit} av {len(tips)} tips fick koordinater")

if __name__ == "__main__":
    main()

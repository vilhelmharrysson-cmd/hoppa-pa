"""Faktainsamling från svenska Wikipedia för alla hållplatser som saknar berättelse.

För varje hållplats: artiklar inom 800 m (närmast först) och artiklar om stadsdelen/orten inom 3 km.
Sparar till tools/research/research.json:
  {"stops": [{"city","name","lat","lon","lines","near":[[titel, m]], "area":[[titel, m]]}],
   "articles": {titel: {"desc", "extract"}}}

Körs av .github/workflows/research.yml (manuellt).
"""
import json, math, os, re, sys, time, unicodedata, urllib.parse, urllib.request, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOURS = os.path.join(ROOT, "public", "data", "tours")
OUT = os.path.join(HERE, "research")
UA = {"User-Agent": "hoppa-pa-research/1.0 (open source travel guide prototype)"}
MAX_MIN = float(os.environ.get("MAX_MIN", "240"))
AREA = re.compile(r"(stadsdel|tätort|småort|ort i|bostadsområde|primärområde|stadsområde|kommundel|ö i|förort|område i)", re.I)

def norm(s):
    return re.sub(r"[^a-z0-9]+", "", unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower())

def api(params):
    params = dict(params, format="json", formatversion="2", maxlag="5")
    url = "https://sv.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)
    for a in range(6):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read())
        except Exception as e:
            print("  väntar:", e, flush=True); time.sleep(60 * (a + 1))
    return {}

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
    articles = {}
    # kontrollpunkt: avbruten körning fortsätter där den slutade
    ck_path = os.path.join(OUT, "partial.json")
    done = json.load(open(ck_path, encoding="utf8")) if os.path.exists(ck_path) else {}
    t0 = time.time()
    for n, s in enumerate(stops):
        k = s["city"] + "|" + s["name"]
        if k in done:
            s["near"], s["area_cand"] = done[k]; continue
        # en sökning räcker: träffarna kommer i avståndsordning
        g = api({"action": "query", "list": "geosearch", "gscoord": f"{s['lat']}|{s['lon']}", "gsradius": "3000", "gslimit": "60"})
        hits = [[h["title"], round(h["dist"])] for h in g.get("query", {}).get("geosearch", [])]
        s["near"] = [h for h in hits if h[1] <= 800][:15]
        s["area_cand"] = hits
        done[k] = [s["near"], s["area_cand"]]
        if n % 100 == 0:
            print(n, s["city"], s["name"], len(s["near"]), f"{(time.time()-t0)/60:.0f} min", flush=True)
            json.dump(done, open(ck_path, "w", encoding="utf8"), ensure_ascii=False)
        if time.time() - t0 > MAX_MIN * 60:
            json.dump(done, open(ck_path, "w", encoding="utf8"), ensure_ascii=False)
            print("Tidsgräns nådd, sparar kontrollpunkt och avslutar. Kör igen för att fortsätta.", flush=True)
            return
        time.sleep(1.0)
    titles = sorted({t for s in stops for t, _ in s["near"] + s["area_cand"]})
    print(len(titles), "artiklar att hämta", flush=True)
    for i in range(0, len(titles), 20):
        e = api({"action": "query", "prop": "extracts|description", "exintro": "1", "explaintext": "1", "exchars": "900",
                 "exlimit": "max", "titles": "|".join(titles[i:i + 20])})
        for p in e.get("query", {}).get("pages", []):
            articles[p["title"]] = {"desc": p.get("description", ""), "extract": p.get("extract", "")}
        time.sleep(1.0)
    for s in stops:
        s["area"] = [[t, d] for t, d in s.pop("area_cand") if AREA.search(articles.get(t, {}).get("desc", "") + " " + articles.get(t, {}).get("extract", "")[:160])][:3]
    used = {t for s in stops for t, _ in s["near"] + s["area"]}
    articles = {t: a for t, a in articles.items() if t in used and a.get("extract")}
    if os.path.exists(ck_path): os.remove(ck_path)
    json.dump({"stops": stops, "articles": articles}, open(os.path.join(OUT, "research.json"), "w", encoding="utf8"),
              ensure_ascii=False, separators=(",", ":"))
    print("Klart:", len(stops), "hållplatser,", len(articles), "artiklar,",
          sum(1 for s in stops if s["near"] or s["area"]), "med material")

if __name__ == "__main__":
    main()

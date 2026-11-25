"""Kopplar fria bilder från Wikimedia Commons till platserna i kunskapsbanken (places_extra.json).

För varje plats används bilden (P18) som Wikidata anger för de Wikipedia-artiklar berättelsen bygger på
("sources"). Det hämtas med några få SPARQL-frågor; Wikipedias egen "pageimages" används bara som
reserv med en tidsgräns, eftersom Wikipedia stryper många anrop hårt.
Bara fritt licensierade bilder (CC BY, CC BY-SA, CC0, public domain) tas med, med fotograf och licens.
Platser som redan har fältet "images" hoppas över, så bara nya platser slår upp något.

  python3 tools/wiki_images.py
"""
import html, json, os, re, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "places_extra.json")
UA = {"User-Agent": "hoppa-pa-bilder/1.0 (open source travel guide prototype)"}
FREE = re.compile(r"^(CC BY(-SA)?( \d\.\d)?|CC0|Public domain|PD\b.*)", re.I)

def api(params):
    params = dict(params, format="json", formatversion="2", maxlag="5")
    url = "https://sv.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)
    for a in range(5):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read())
        except Exception as e:
            print("  väntar:", e); time.sleep(60 * (a + 1))
    return {}

def get(url, data=None, headers=None, tries=5):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers=dict(UA, **(headers or {})))
            return json.loads(urllib.request.urlopen(req, timeout=120).read())
        except Exception as e:
            print("  väntar:", e, flush=True); time.sleep(30 * (a + 1))
    return {}

def wikidata_images(titles):
    """titel -> filnamn på Commons, via Wikidata P18."""
    out = {}
    for i in range(0, len(titles), 200):
        vals = " ".join('"%s"@sv' % t.replace("\\", "\\\\").replace('"', '\\"') for t in titles[i:i + 200])
        q = ("SELECT ?title ?img WHERE { VALUES ?title { %s } ?art schema:name ?title ; "
             "schema:isPartOf <https://sv.wikipedia.org/> ; schema:about ?item . ?item wdt:P18 ?img . }" % vals)
        r = get("https://query.wikidata.org/sparql", data=urllib.parse.urlencode({"query": q}).encode(),
                headers={"Accept": "application/sparql-results+json", "Content-Type": "application/x-www-form-urlencoded"})
        for b in r.get("results", {}).get("bindings", []):
            f = urllib.parse.unquote(b["img"]["value"].rsplit("/", 1)[-1]).replace("_", " ")
            out.setdefault(b["title"]["value"], f)
        time.sleep(1)
    return out

def commons(params):
    params = dict(params, format="json", formatversion="2", maxlag="5")
    return get("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params))

def clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s or ""))).strip()

def main():
    data = json.load(open(PATH, encoding="utf8"))
    # nya platser, och platser som inte fick någon bild förra gången (försöker igen)
    todo = [(c, k) for c, d in data.items() for k, v in d.items() if not v.get("images") and v.get("sources")]
    titles = sorted({t for c, k in todo for t in data[c][k]["sources"]})
    print(len(todo), "platser,", len(titles), "artiklar", flush=True)
    page_img = wikidata_images(titles)
    print(len(page_img), "artiklar har bild i Wikidata", flush=True)
    # reserv: Wikipedias sidbild för resten, med tidsgräns
    rest = [t for t in titles if t not in page_img]; t0 = time.time()
    for i in range(0, len(rest), 40):
        if time.time() - t0 > 20 * 60: print("  reservsökning avbruten (tidsgräns)"); break
        q = api({"action": "query", "prop": "pageimages", "piprop": "name", "redirects": "1", "titles": "|".join(rest[i:i + 40])})
        red = {r["to"]: r["from"] for r in q.get("query", {}).get("redirects", [])}
        for p in q.get("query", {}).get("pages", []):
            if p.get("pageimage"): page_img[red.get(p["title"], p["title"])] = p["pageimage"].replace("_", " ")
        time.sleep(2)
    files = sorted(set(page_img.values()))
    print(len(files), "bildfiler att kontrollera licens för", flush=True)
    info = {}
    for i in range(0, len(files), 50):
        q = commons({"action": "query", "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": "1280",
                     "titles": "|".join("File:" + f for f in files[i:i + 50])})
        norm_map = {n["to"]: n["from"] for n in q.get("query", {}).get("normalized", [])}
        for p in q.get("query", {}).get("pages", []):
            ii = (p.get("imageinfo") or [{}])[0]; m = ii.get("extmetadata", {})
            lic = clean(m.get("LicenseShortName", {}).get("value", ""))
            if not lic or not FREE.match(lic) or str(m.get("NonFree", {}).get("value", "")).lower() == "true": continue
            if (ii.get("width") or 0) < 700: continue
            name = norm_map.get(p["title"], p["title"]).split(":", 1)[1]
            info[name] = {"src": ii.get("thumburl") or ii.get("url"),
                "credit": (clean(m.get("Artist", {}).get("value", "")) or "Okänd")[:80], "license": lic,
                "page": ii.get("descriptionurl", ""), "title": clean(m.get("ObjectName", {}).get("value", ""))[:100]}
        time.sleep(1)
    n = 0
    for c, k in todo:
        imgs, seen = [], set()
        for t in data[c][k]["sources"]:
            f = page_img.get(t)
            if f in info and info[f]["src"] not in seen:
                imgs.append(info[f]); seen.add(info[f]["src"])
        data[c][k]["images"] = imgs[:3]
        n += bool(imgs)
    print(f"{n} av {len(todo)} platser fick bilder via artiklarna", flush=True)
    json.dump(data, open(PATH, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    # handskrivna platser (places_gbg.json, content_sthlm.py) får bilder via en post utan text här;
    # bygget lägger bilderna på den handskrivna platsen
    import sys; sys.path.insert(0, HERE)
    from content_sthlm import PLACES as STH
    G = json.load(open(os.path.join(HERE, "places_gbg.json"), encoding="utf8"))["places"]
    for city, names in (("Göteborg", G), ("Stockholm", STH)):
        for k in names:
            if k not in data.setdefault(city, {}):
                data[city][k] = {"story": "", "imageOnly": True, "images": []}
    near_photos(data)
    json.dump(data, open(PATH, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print("Klart:", sum(1 for d in data.values() for v in d.values() if v.get("images")), "av",
          sum(len(d) for d in data.values()), "platser har bilder")

SKIP = re.compile(r"(karta|map|logo|vapen|coat of arms|\.svg|\.pdf|\.tif|diagram|plan\b|ritning|skylt|sign\b|flag)", re.I)

def stop_coords():
    """hållplatsnamn -> (lat, lon) från de byggda turerna."""
    tours = os.path.join(os.path.dirname(HERE), "public", "data", "tours")
    co = {}
    for f in os.listdir(tours):
        t = json.load(open(os.path.join(tours, f), encoding="utf8"))
        for st in t["stops"]: co.setdefault((t["city"], st["name"]), (st["lat"], st["lon"]))
    return co

def near_photos(data, budget_min=float(os.environ.get("PHOTO_MIN", "60"))):
    """Fria, geotaggade foton på Commons nära hållplatsen för platser som fortfarande saknar bild."""
    co = stop_coords()
    todo = [(c, k) for c, d in data.items() for k, v in d.items() if not v.get("images") and (c, k) in co]
    print(len(todo), "platser utan bild: söker geotaggade foton på Commons", flush=True)
    t0, n = time.time(), 0
    for i, (c, k) in enumerate(todo):
        if time.time() - t0 > budget_min * 60: print("  tidsgräns, fortsätter nästa natt"); break
        lat, lon = co[(c, k)]
        g = commons({"action": "query", "generator": "geosearch", "ggscoord": f"{lat}|{lon}", "ggsradius": "300",
                     "ggslimit": "20", "ggsnamespace": "6", "prop": "imageinfo|coordinates",
                     "iiprop": "url|extmetadata|size", "iiurlwidth": "1280"})
        cands = []
        for p in g.get("query", {}).get("pages", []):
            ii = (p.get("imageinfo") or [{}])[0]; m = ii.get("extmetadata", {})
            lic = clean(m.get("LicenseShortName", {}).get("value", ""))
            if SKIP.search(p["title"]) or not lic or not FREE.match(lic): continue
            if str(m.get("NonFree", {}).get("value", "")).lower() == "true": continue
            w, h = ii.get("width") or 0, ii.get("height") or 0
            if w < 1000 or h < 600 or w < h: continue      # liggande foton i bra upplösning
            d = (p.get("coordinates") or [{}])[0].get("dist", 300)
            cands.append((d, {"src": ii.get("thumburl") or ii.get("url"),
                "credit": (clean(m.get("Artist", {}).get("value", "")) or "Okänd")[:80], "license": lic,
                "page": ii.get("descriptionurl", ""),
                "title": (clean(m.get("ImageDescription", {}).get("value", "")) or clean(m.get("ObjectName", {}).get("value", "")))[:100],
                "near": True}))
        cands.sort(key=lambda x: x[0])
        if cands:
            data[c][k]["images"] = [x[1] for x in cands[:3]]; n += 1
        if i % 100 == 0:
            print(" ", i, "av", len(todo), n, "med foto", flush=True)
            json.dump(data, open(PATH, "w", encoding="utf8"), ensure_ascii=False, indent=1)
        time.sleep(1)
    print(n, "platser fick foton från omgivningen", flush=True)

if __name__ == "__main__":
    main()

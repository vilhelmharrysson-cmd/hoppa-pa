"""Kopplar fria bilder från Wikimedia Commons till platserna i kunskapsbanken (places_extra.json).

För varje plats används huvudbilden i de Wikipedia-artiklar berättelsen bygger på ("sources").
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

def clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s or ""))).strip()

def main():
    data = json.load(open(PATH, encoding="utf8"))
    # nya platser, och platser som inte fick någon bild förra gången (försöker igen)
    todo = [(c, k) for c, d in data.items() for k, v in d.items() if not v.get("images") and v.get("sources")]
    titles = sorted({t for c, k in todo for t in data[c][k]["sources"]})
    print(len(todo), "platser,", len(titles), "artiklar", flush=True)
    page_img = {}
    for i in range(0, len(titles), 40):
        q = api({"action": "query", "prop": "pageimages", "piprop": "name", "redirects": "1", "titles": "|".join(titles[i:i + 40])})
        red = {r["to"]: r["from"] for r in q.get("query", {}).get("redirects", [])}
        for p in q.get("query", {}).get("pages", []):
            if p.get("pageimage"): page_img[red.get(p["title"], p["title"])] = p["pageimage"]
        time.sleep(2)
    files = sorted(set(page_img.values()))
    info = {}
    for i in range(0, len(files), 40):
        q = api({"action": "query", "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": "1280",
                 "titles": "|".join("Fil:" + f for f in files[i:i + 40])})
        for p in q.get("query", {}).get("pages", []):
            ii = (p.get("imageinfo") or [{}])[0]; m = ii.get("extmetadata", {})
            lic = clean(m.get("LicenseShortName", {}).get("value", ""))
            if not lic or not FREE.match(lic) or str(m.get("NonFree", {}).get("value", "")).lower() == "true": continue
            if (ii.get("width") or 0) < 700: continue
            info[p["title"].split(":", 1)[1]] = {"src": ii.get("thumburl") or ii.get("url"),
                "credit": (clean(m.get("Artist", {}).get("value", "")) or "Okänd")[:80], "license": lic,
                "page": ii.get("descriptionurl", ""), "title": clean(m.get("ObjectName", {}).get("value", ""))[:100]}
        time.sleep(2)
    n = 0
    for c, k in todo:
        imgs, seen = [], set()
        for t in data[c][k]["sources"]:
            f = page_img.get(t)
            if f in info and info[f]["src"] not in seen:
                imgs.append(info[f]); seen.add(info[f]["src"])
        data[c][k]["images"] = imgs[:3]
        n += bool(imgs)
    json.dump(data, open(PATH, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print(f"Klart: {n} av {len(todo)} platser fick bilder")

if __name__ == "__main__":
    main()

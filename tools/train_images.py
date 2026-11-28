"""Bilder till tågturen: Wikidata-bilden (P18) för varje station och "titta ut" i tools/train_content.json.

Bara fritt licensierade bilder från Wikimedia Commons, med fotograf och licens.
  python3 tools/train_images.py
"""
import json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wiki_images import wikidata_images, commons, clean, FREE  # noqa: E402

def main():
    p = os.path.join(HERE, "train_content.json")
    C = json.load(open(p, encoding="utf8"))
    items = C["stations"] + C["looks"]
    titles = sorted({x["title"] for x in items if x.get("title")})
    page_img = wikidata_images(titles)
    files = sorted(set(page_img.values()))
    info = {}
    for i in range(0, len(files), 50):
        q = commons({"action": "query", "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": "1280",
                     "titles": "|".join("File:" + f for f in files[i:i + 50])})
        norm = {n["to"]: n["from"] for n in q.get("query", {}).get("normalized", [])}
        for pg in q.get("query", {}).get("pages", []):
            ii = (pg.get("imageinfo") or [{}])[0]; m = ii.get("extmetadata", {})
            lic = clean(m.get("LicenseShortName", {}).get("value", ""))
            if not lic or not FREE.match(lic) or str(m.get("NonFree", {}).get("value", "")).lower() == "true": continue
            if (ii.get("width") or 0) < 600: continue
            name = norm.get(pg["title"], pg["title"]).split(":", 1)[1]
            info[name] = {"src": ii.get("thumburl") or ii.get("url"),
                          "credit": (clean(m.get("Artist", {}).get("value", "")) or "Okänd")[:80], "license": lic,
                          "page": ii.get("descriptionurl", ""), "title": clean(m.get("ObjectName", {}).get("value", ""))[:100]}
        time.sleep(1)
    n = 0
    for x in items:
        f = page_img.get(x.get("title"))
        if f in info: x["images"] = [info[f]]; n += 1
    json.dump(C, open(p, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print(n, "av", len(items), "fick bild")

if __name__ == "__main__":
    main()

"""Historiska foton från K-samsök (Riksantikvarieämbetets söktjänst över museernas samlingar).

För varje plats i kunskapsbanken söks foton som nämner platsens namn i beskrivningen, i rätt kommun
(Göteborg/Stockholm), med fri licens (public domain, CC0, CC BY, CC BY-SA). Gamla bilder går före.
Resultatet sparas i fältet "historic" i tools/places_extra.json; bygget visar dem efter de moderna
bilderna ("Förr: ..."). Platser som redan har fältet hoppas över.

  python3 tools/historic_images.py
"""
import html, json, os, re, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "places_extra.json")
UA = {"User-Agent": "hoppa-pa-bilder/1.0 (open source travel guide prototype)"}
API = "https://kulturarvsdata.se/ksamsok/api"
LIC = {"pdmark": "Public domain", "cc0": "CC0", "by": "CC BY", "by-sa": "CC BY-SA"}
BUDGET_MIN = float(os.environ.get("HISTORIC_MIN", "45"))

def search(name, city):
    q = f'text="{name}" and thumbnailExists=j and municipalityName={city}'
    url = API + "?" + urllib.parse.urlencode({"method": "search", "hitsPerPage": "40", "recordSchema": "presentation", "query": q})
    for a in range(4):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode("utf8")
        except Exception as e:
            print("  väntar:", e, flush=True); time.sleep(20 * (a + 1))
    return ""

def tag(x, t):
    m = re.search(r"<pres:%s[^>]*>(.*?)</pres:%s>" % (t, t), x, re.S)
    return html.unescape(m.group(1)).strip() if m else ""

def caption(desc):
    d = re.sub(r"(Anmärkning \(övrig\):.*?(?=Beskrivning:|$))", "", desc, flags=re.S)
    d = re.sub(r"^\s*Beskrivning:\s*", "", d).split("Fotosyfte:")[0]
    d = re.sub(r"\s+", " ", d).strip(" .")
    return d[:110]

def year_of(item):
    for ctx in re.findall(r"<pres:context>(.*?)</pres:context>", item, re.S):
        if re.search(r"<pres:event[^>]*>(Förvärv|Inventer|Registrer)", ctx): continue
        m = re.search(r"\b(1[89]\d\d|20[0-2]\d)\b(?!-tal)", tag(ctx, "timeLabel"))
        if m and int(m.group(1)) >= 1850: return int(m.group(1))
    m = re.search(r"\b(1[89]\d)\d-talet", tag(item, "description"))
    return int(m.group(1) + "0") if m else None

def pick(xml, name):
    out = []
    nm = name.lower()
    for item in xml.split("<record>")[1:]:
        desc = tag(item, "description"); label = tag(item, "itemLabel")
        if nm not in (desc + " " + label).lower(): continue
        if tag(item, "type") not in ("Foto", "Photo", "Bild", "Del av föremål", "Fotografi"): continue
        img = re.search(r"<pres:image>(.*?)</pres:image>", item, re.S)
        if not img: continue
        img = img.group(1)
        lic = tag(img, "mediaLicense").split("#")[-1].lower()
        if lic not in LIC: continue
        src = (re.search(r'<pres:src type="(?:lowres|highres)"[^>]*>(.*?)</pres:src>', img) or [None, None])[1]
        if not src: continue
        src = html.unescape(src).replace("http://", "https://")
        page = (re.search(r'<pres:representation format="HTML">(.*?)</pres:representation>', item) or [None, ""])[1]
        yr = year_of(item)
        cap = caption(desc) or name
        score = (2 if lic == "pdmark" else 0) + (3 if yr and yr < 1970 else 1 if yr and yr < 1995 else 0) \
                - (1 if yr and yr >= 2000 else 0) + (1 if nm in desc.lower() else 0)
        out.append((score, {"src": src, "credit": (tag(img, "byline") or tag(item, "organization") or "Okänd")[:80],
                            "license": LIC[lic], "page": page.replace("http://", "https://"),
                            "title": cap, "old": bool(yr and yr < 1995) or lic == "pdmark", "year": yr if yr and yr < 1995 else None,
                            "museum": tag(item, "organization")[:60]}))
    out = [o for o in out if o[1]["old"]]      # bara bilder som faktiskt visar "förr"
    out.sort(key=lambda x: -x[0])
    seen, res = set(), []
    for _, im in out:
        if im["title"] in seen: continue      # undvik flera bilder av samma motiv
        seen.add(im["title"]); res.append(im)
        if len(res) == 2: break
    return res

def main():
    sys.path.insert(0, HERE)
    from content_sthlm import PLACES as STH
    G = json.load(open(os.path.join(HERE, "places_gbg.json"), encoding="utf8"))["places"]
    data = json.load(open(PATH, encoding="utf8"))
    for city, names in (("Göteborg", G), ("Stockholm", STH)):
        for k in names:
            if k not in data.setdefault(city, {}):
                data[city][k] = {"story": "", "imageOnly": True, "images": []}
    todo = [(c, k) for c, d in data.items() for k, v in d.items() if "historic" not in v and len(k) >= 5]
    print(len(todo), "platser att söka historiska foton för", flush=True)
    t0, n = time.time(), 0
    for i, (c, k) in enumerate(todo):
        if time.time() - t0 > BUDGET_MIN * 60:
            print("  tidsgräns, fortsätter nästa gång"); break
        name = re.sub(r"\s+(station|centrum|torg|södra|norra|östra|västra)$", "", k, flags=re.I) if len(k) > 12 else k
        imgs = pick(search(k, c), k) or (pick(search(name, c), name) if name != k else [])
        data[c][k]["historic"] = imgs
        n += bool(imgs)
        if i % 100 == 0:
            print(" ", i, "av", len(todo), n, "med historiska foton", flush=True)
            json.dump(data, open(PATH, "w", encoding="utf8"), ensure_ascii=False, indent=1)
        time.sleep(0.3)
    json.dump(data, open(PATH, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print(f"Klart: {n} nya platser fick historiska foton,",
          sum(1 for d in data.values() for v in d.values() if v.get("historic")), "totalt")

if __name__ == "__main__":
    main()

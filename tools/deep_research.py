"""Hämtar hela Wikipedia-artiklar för de mest trafikerade hållplatserna, som underlag för "Läs mer".

Hållplatserna rangordnas efter hur många turer som passerar och har en berättelse. För varje plats används
artiklarna i "sources" (kunskapsbanken) och, för handskrivna platser, Wikipedias bästa sökträff.
Resultat: tools/research/deep.json  {"Stad|Hållplats": {"city","name","story","texts":{titel: text}}}

  TOP=300 python3 tools/deep_research.py
"""
import json, os, re, sys, time, urllib.parse, urllib.request, collections, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
TOURS = os.path.join(os.path.dirname(HERE), "public", "data", "tours")
OUT = os.path.join(HERE, "research", "deep.json")
UA = {"User-Agent": "hoppa-pa-research/1.2 (open source travel guide prototype)"}
TOP = int(os.environ.get("TOP", "300"))
MAX_MIN = float(os.environ.get("MAX_MIN", "300"))

def norm(s):
    return re.sub(r"[^a-z0-9]+", "", unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower())

def api(params):
    params = dict(params, format="json", formatversion="2", maxlag="5")
    url = "https://sv.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)
    for a in range(6):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read())
        except Exception as e:
            print("  väntar:", e, flush=True); time.sleep(30 * (a + 1))
    return {}

def clean(text):
    # bort med listor av typen "Se även", "Referenser", "Externa länkar" och tomma rubriker
    text = re.split(r"\n==\s*(Se även|Referenser|Noter|Källor|Externa länkar|Vidare läsning|Litteratur)\s*==", text)[0]
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()[:7000]

def main():
    sys.path.insert(0, HERE)
    X = json.load(open(os.path.join(HERE, "places_extra.json"), encoding="utf8"))
    cnt, story = collections.Counter(), {}
    for f in os.listdir(TOURS):
        t = json.load(open(os.path.join(TOURS, f), encoding="utf8"))
        for s in t["stops"]:
            if not s.get("story"): continue
            k = (t["city"], s["name"]); cnt[k] += 1
            st = s["story"]
            if not st.startswith(("Välkommen ombord", "Snart är vi framme")): story.setdefault(k, st)
    top = [k for k, _ in cnt.most_common() if k in story][:TOP]
    done = json.load(open(OUT, encoding="utf8")) if os.path.exists(OUT) else {}
    print(len(top), "platser,", len(done), "redan klara", flush=True)
    t0 = time.time()
    for n, (city, name) in enumerate(top):
        key = f"{city}|{name}"
        if key in done: continue
        if time.time() - t0 > MAX_MIN * 60: print("tidsgräns"); break
        titles = list((X.get(city, {}).get(name) or {}).get("sources", []))[:3]
        if not titles:
            r = api({"action": "query", "list": "search", "srsearch": f"{name} {city}", "srlimit": "3"})
            for h in r.get("query", {}).get("search", []):
                if norm(name)[:6] in norm(h["title"]): titles.append(h["title"]); break
            time.sleep(1)
        texts = {}
        for title in titles:
            r = api({"action": "query", "prop": "extracts", "explaintext": "1", "redirects": "1", "titles": title})
            for p in r.get("query", {}).get("pages", []):
                if p.get("extract"): texts[p["title"]] = clean(p["extract"])
            time.sleep(1.5)
        done[key] = {"city": city, "name": name, "lines": cnt[(city, name)], "story": story[(city, name)], "texts": texts}
        if n % 20 == 0:
            print(n, key, len(texts), flush=True)
            os.makedirs(os.path.dirname(OUT), exist_ok=True)
            json.dump(done, open(OUT, "w", encoding="utf8"), ensure_ascii=False)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(done, open(OUT, "w", encoding="utf8"), ensure_ascii=False)
    print("Klart:", len(done), "platser,", sum(1 for v in done.values() if v["texts"]), "med artiklar")

if __name__ == "__main__":
    main()

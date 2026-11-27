"""Lägger till engelska texter, barnversioner och färdiga rundor i de byggda turerna.

Körs efter gtfs_build.py (i den nattliga GitHub Action), och går att köra lokalt:

  python3 tools/enrich.py

Källor:
  tools/en.json      {"svensk text": "English text"}  berättelser, "titta ut" och tips
  tools/kids.json    {"Stad|Hållplats": {"t": text, "q": spana/gissa-fråga}}
  tools/rounds.json  färdiga rundor (tema och dagsturer), se tools/round_legs.py
Resultat: fälten story_en, tips_en, text_en (titta ut) och kids i public/data/tours/*.json,
samt public/data/rounds.json.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "public", "data")
TOURS = os.path.join(DATA, "tours")

def jload(name, default):
    p = os.path.join(HERE, name)
    return json.load(open(p, encoding="utf8")) if os.path.exists(p) else default

def main():
    EN = jload("en.json", {})
    KIDS = jload("kids.json", {})
    ROUNDS = jload("rounds.json", [])
    n_en = n_tot = n_kids = 0
    stops_by_tour = {}
    index = json.load(open(os.path.join(DATA, "index.json"), encoding="utf8"))
    en_share = {}
    for f in sorted(os.listdir(TOURS)):
        path = os.path.join(TOURS, f)
        t = json.load(open(path, encoding="utf8"))
        stops_by_tour[t["id"]] = [s["name"] for s in t["stops"]]
        got = tot = 0
        for st in t["stops"]:
            for k in ("story_en", "tips_en", "kids"): st.pop(k, None)
            if st.get("story"):
                tot += 1
                if st["story"] in EN: st["story_en"] = EN[st["story"]]; got += 1
                kid = KIDS.get(f"{t['city']}|{st['name']}")
                if kid and kid.get("t"): st["kids"] = {"t": kid["t"], "q": kid.get("q", "")}; n_kids += 1
            if st.get("tips"):
                tr = [EN.get(tp[0]) for tp in st["tips"]]
                if any(tr): st["tips_en"] = [x or tp[0] for x, tp in zip(tr, st["tips"])]
        for L in t.get("looks", []):
            L.pop("text_en", None)
            if L["text"] in EN: L["text_en"] = EN[L["text"]]
        n_en += got; n_tot += tot
        en_share[t["id"]] = round(got / tot, 2) if tot else 0
        json.dump(t, open(path, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    for e in index["tours"]:
        e["en"] = en_share.get(e["id"], 0) >= 0.9
    json.dump(index, open(os.path.join(DATA, "index.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    # rundor: behåll bara de vars alla åksteg finns i turerna (linjer kan läggas ner eller byta väg)
    ok = []
    for r in ROUNDS:
        good = True
        for s in r.get("steps", []):
            if s.get("tour"):
                names = stops_by_tour.get(s["tour"])
                if not names or s["from"] not in names or s["to"] not in names or names.index(s["from"]) >= len(names) - 1 - names[::-1].index(s["to"]):
                    good = False; print("  rundan", r["id"], "har ett ogiltigt steg:", s.get("tour"), s.get("from"), "→", s.get("to"))
                    break
        if good: ok.append(r)
    json.dump(ok, open(os.path.join(DATA, "rounds.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    print(f"Engelska: {n_en} av {n_tot} berättelser · barnversioner: {n_kids} · rundor: {len(ok)} av {len(ROUNDS)}")

if __name__ == "__main__":
    main()

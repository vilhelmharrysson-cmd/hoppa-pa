"""Hjälpverktyg för att sätta ihop rundor (tools/rounds.json) av befintliga turer.

  python3 tools/round_legs.py Göteborg "Järntorget" "Saltholmen"   # turer som går från A till B
  python3 tools/round_legs.py Göteborg --stop "Järntorget"         # turer som passerar en hållplats
  python3 tools/round_legs.py --check                               # kontrollera tools/rounds.json

Tiderna är ungefärliga (turens medelhastighet och uppehåll), precis som i appen.
"""
import json, os, sys, math

HERE = os.path.dirname(os.path.abspath(__file__))
TOURS = os.path.join(os.path.dirname(HERE), "public", "data", "tours")

def load():
    out = []
    for f in sorted(os.listdir(TOURS)):
        t = json.load(open(os.path.join(TOURS, f), encoding="utf8"))
        if t.get("guide"): continue
        cum, s = [0.0], 0.0
        for a, b in zip(t["stops"], t["stops"][1:]):
            s += math.hypot((b["lat"] - a["lat"]) * 110540, (b["lon"] - a["lon"]) * 111320 * math.cos(math.radians(a["lat"])))
            cum.append(s)
        t["_cum"] = cum
        out.append(t)
    return out

def minutes(t, i, j):
    return round((t["_cum"][j] - t["_cum"][i]) * 1.25 / (t["speedKmh"] / 3.6) / 60 + (j - i) * t["dwellSec"] / 60)

def legs(tours, city, a, b):
    res = []
    for t in tours:
        if t["city"] != city: continue
        names = [s["name"] for s in t["stops"]]
        if a in names and b in names:
            i, j = names.index(a), len(names) - 1 - names[::-1].index(b)
            if i < j:
                g = [s["name"] for s in t["stops"][i + 1:j] if s.get("story")]
                res.append((minutes(t, i, j), t["id"], t["line"], t["to"], len(g), g))
    return sorted(res)

def check():
    tours = load(); byid = {t["id"]: t for t in tours}
    R = json.load(open(os.path.join(HERE, "rounds.json"), encoding="utf8"))
    bad = 0
    for r in R:
        for st in r["steps"]:
            if st.get("tour"):
                t = byid.get(st["tour"])
                names = [s["name"] for s in t["stops"]] if t else []
                ok = t and st["from"] in names and st["to"] in names and names.index(st["from"]) < len(names) - 1 - names[::-1].index(st["to"])
                if not ok: bad += 1; print("FEL", r["id"], st)
    print(len(R), "rundor,", bad, "fel")
    return bad

if __name__ == "__main__":
    if sys.argv[1:] == ["--check"]: sys.exit(1 if check() else 0)
    tours = load()
    if len(sys.argv) == 4 and sys.argv[2] == "--stop":
        for t in tours:
            names = [s["name"] for s in t["stops"]]
            if t["city"] == sys.argv[1] and sys.argv[3] in names:
                print(t["id"], "linje", t["line"], "mot", t["to"], "| hållplats", names.index(sys.argv[3]) + 1, "av", len(names))
    else:
        for m, tid, line, to, ng, g in legs(tours, *sys.argv[1:4])[:15]:
            print(f"{m:3d} min  {tid}  (linje {line} mot {to})  {ng} guidade emellan: {', '.join(g[:12])}")

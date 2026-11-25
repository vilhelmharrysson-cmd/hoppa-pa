"""Väljer vilka hållplatser som behöver nya berättelser för att fylla luckor längs linjerna.

Mål: på varje tur ska guiden ha något att säga ungefär var MAX_GAP meter. För varje lucka väljs den
hållplats i luckan som har mest underlag (Wikipedia-artiklar i närheten) och som flest linjer passerar,
så att en berättelse kommer så många turer som möjligt till nytta.

Används av wiki_research.py. Fristående: python3 tools/select_fill.py [MAX_GAP=1200] > urval.json
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOURS = os.path.join(ROOT, "public", "data", "tours")

def dist(a, b):
    return math.hypot((a["lat"] - b["lat"]) * 111320, (a["lon"] - b["lon"]) * 111320 * math.cos(math.radians(a["lat"])))

def score(s):
    near = [d for _, d in s["near"]]
    return (len([d for d in near if d <= 400]) * 3 + len(near) + min(len(s.get("area_cand", s.get("area", []))), 10)) * (1 + 0.3 * s["lines"])

def select(stops, max_gap=1200):
    cand = {(s["city"], s["name"]): s for s in stops}
    chosen = set()
    tours = [json.load(open(os.path.join(TOURS, f), encoding="utf8")) for f in sorted(os.listdir(TOURS))]
    tours = [t for t in tours if not t.get("guide")]
    for _ in range(3):   # upprepa: val för en linje hjälper ofta andra
        for t in tours:
            st = t["stops"]; cum = [0.0]
            for i in range(1, len(st)): cum.append(cum[-1] + dist(st[i - 1], st[i]))
            covered = [i for i, s in enumerate(st) if s.get("story") or (t["city"], s["name"]) in chosen]
            anchors = sorted(set(covered) | {0, len(st) - 1})
            for a, b in zip(anchors, anchors[1:]):
                gap = cum[b] - cum[a]
                if gap <= max_gap: continue
                n_new = int(gap // max_gap)
                for k in range(1, n_new + 1):
                    target = cum[a] + gap * k / (n_new + 1)
                    window = [i for i in range(a + 1, b) if abs(cum[i] - target) <= max_gap / 2]
                    opts = [(score(cand[(t["city"], st[i]["name"])]), i) for i in window if (t["city"], st[i]["name"]) in cand]
                    opts = [o for o in opts if o[0] > 0]
                    if opts:
                        chosen.add((t["city"], st[max(opts)[1]]["name"]))
    return sorted(chosen)

if __name__ == "__main__":
    R = json.load(open(os.path.join(HERE, "research", "research.json"), encoding="utf8"))
    sel = select(R["stops"], float(sys.argv[1]) if len(sys.argv) > 1 else 1200)
    print(json.dumps(sel, ensure_ascii=False))
    print(f"{len(sel)} hållplatser valda", file=sys.stderr)

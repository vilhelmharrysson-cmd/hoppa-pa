"""Väljer vilka hållplatser som behöver nya berättelser för att fylla luckor längs linjerna.

Mål: på varje tur ska guiden ha något att säga ungefär var MAX_GAP meter. För varje lucka väljs den
hållplats i luckan som har mest underlag (Wikipedia-artiklar) och som flest linjer passerar,
så att en berättelse kommer så många turer som möjligt till nytta.

  python3 tools/select_fill.py [MAX_GAP=1200] > urval.json
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOURS = os.path.join(ROOT, "public", "data", "tours")
MAX_GAP = float(sys.argv[1]) if len(sys.argv) > 1 else 1200
R = json.load(open(os.path.join(HERE, "research", "research.json"), encoding="utf8"))
cand = {(s["city"], s["name"]): s for s in R["stops"]}

def dist(a, b):
    return math.hypot((a["lat"] - b["lat"]) * 111320, (a["lon"] - b["lon"]) * 111320 * math.cos(math.radians(a["lat"])))

def score(s):
    near = [d for _, d in s["near"] if _ in R["articles"]]
    return (len([d for d in near if d <= 400]) * 3 + len(near) + 2 * len(s["area"])) * (1 + 0.3 * s["lines"])

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
            if gap <= MAX_GAP: continue
            n_new = int(gap // MAX_GAP)
            for k in range(1, n_new + 1):
                target = cum[a] + gap * k / (n_new + 1)
                window = [i for i in range(a + 1, b) if abs(cum[i] - target) <= MAX_GAP / 2]
                opts = [(score(cand[(t["city"], st[i]["name"])]), i) for i in window if (t["city"], st[i]["name"]) in cand]
                opts = [o for o in opts if o[0] > 0]
                if opts:
                    chosen.add((t["city"], st[max(opts)[1]]["name"]))
sel = [cand[k] for k in chosen]
sel.sort(key=lambda s: (s["city"], -s["lines"]))
print(json.dumps(sel, ensure_ascii=False), file=sys.stdout)
print(f"{len(sel)} hållplatser valda (Göteborg {sum(s['city']=='Göteborg' for s in sel)}, "
      f"Stockholm {sum(s['city']=='Stockholm' for s in sel)})", file=sys.stderr)

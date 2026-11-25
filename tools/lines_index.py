"""Bygger public/data/lines-<stad>.json: förenklad linjedragning och hållplatser för varje tur.

Används av appens "Vilken linje åker jag?": telefonens GPS-spår jämförs med alla linjer i staden.
Körs efter gtfs_build.py (i den nattliga GitHub Action).

  python3 tools/lines_index.py
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "public", "data")
TOL = 12.0   # meter: hur mycket linjen får förenklas

def xy(p, lat0):
    return (p[1] * 111320 * math.cos(math.radians(lat0)), p[0] * 110540)

def seg_dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)

def simplify(pts, lat0):
    """Ramer–Douglas–Peucker, iterativt."""
    if len(pts) < 3: return pts
    P = [xy(p, lat0) for p in pts]
    keep = [False] * len(pts); keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        best, bi = 0, None
        for k in range(i + 1, j):
            d = seg_dist(P[k], P[i], P[j])
            if d > best: best, bi = d, k
        if bi is not None and best > TOL:
            keep[bi] = True; stack += [(i, bi), (bi, j)]
    return [p for p, k in zip(pts, keep) if k]

def main():
    out = {}
    for f in sorted(os.listdir(os.path.join(DATA, "tours"))):
        t = json.load(open(os.path.join(DATA, "tours", f), encoding="utf8"))
        if t.get("guide"): continue          # inlästa turer har en vanlig motsvarighet
        route = t["route"]; lat0 = route[0][0]
        r = simplify(route, lat0)
        out.setdefault(t["city"], {})[t["id"]] = {
            "r": [[round(a, 5), round(b, 5)] for a, b in r],
            "s": [[round(s["lat"], 5), round(s["lon"], 5)] for s in t["stops"]]}
    for city, lines in out.items():
        slug = "goteborg" if city.startswith("G") else "stockholm"
        path = os.path.join(DATA, f"lines-{slug}.json")
        json.dump(lines, open(path, "w", encoding="utf8"), separators=(",", ":"))
        print(path, len(lines), "turer", os.path.getsize(path) // 1024, "kB")

if __name__ == "__main__":
    main()

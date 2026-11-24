"""Hjälpfunktioner för OSM-relationer."""
import json, math, os
OSM = None

def xy(lat, lon, lat0):
    return (lon * 111320.0 * math.cos(math.radians(lat0)), lat * 111320.0)

def load(rid):
    d = json.load(open(os.path.join(OSM, f"full_{rid}.json")))
    nodes = {e["id"]: e for e in d["elements"] if e["type"] == "node"}
    ways = {e["id"]: e for e in d["elements"] if e["type"] == "way"}
    rel = [e for e in d["elements"] if e["type"] == "relation" and e["id"] == rid][0]
    return nodes, ways, rel

def stitch(nodes, ways, rel):
    seqs = [list(ways[m["ref"]]["nodes"]) for m in rel["members"]
            if m["type"] == "way" and m["role"] == "" and m["ref"] in ways]
    line = []
    for i, w in enumerate(seqs):
        if not line:
            nxt = seqs[i + 1] if i + 1 < len(seqs) else None
            if nxt and w[0] in (nxt[0], nxt[-1]):
                w = w[::-1]
            line = w[:]; continue
        if line[-1] == w[0]: line += w[1:]
        elif line[-1] == w[-1]: line += w[::-1][1:]
        else:
            a = nodes[line[-1]]
            d0 = (nodes[w[0]]["lat"] - a["lat"]) ** 2 + (nodes[w[0]]["lon"] - a["lon"]) ** 2
            d1 = (nodes[w[-1]]["lat"] - a["lat"]) ** 2 + (nodes[w[-1]]["lon"] - a["lon"]) ** 2
            line += w if d0 <= d1 else w[::-1]
    return [(nodes[n]["lat"], nodes[n]["lon"]) for n in line if n in nodes]

def stops_of(nodes, rel):
    out = []
    for m in rel["members"]:
        if m["role"].startswith("stop") and m["type"] == "node" and m["ref"] in nodes:
            n = nodes[m["ref"]]; name = n.get("tags", {}).get("name")
            if name and (not out or out[-1][0] != name):
                out.append((name, n["lat"], n["lon"]))
    return out

def project(pt, P, cum, s_min=-1e18):
    best = (0, 1e18, 0)
    for i in range(len(P) - 1):
        if cum[i + 1] < s_min - 1: continue
        (x1, y1), (x2, y2) = P[i], P[i + 1]
        dx, dy = x2 - x1, y2 - y1; L2 = dx * dx + dy * dy or 1e-9
        t = max(0, min(1, ((pt[0] - x1) * dx + (pt[1] - y1) * dy) / L2))
        d = math.hypot(pt[0] - (x1 + t * dx), pt[1] - (y1 + t * dy))
        s = cum[i] + t * math.sqrt(L2)
        if s < s_min - 1: continue
        if d < best[1]: best = (s, d, i)
    return best

def rdp(pts, eps):
    if len(pts) < 3: return pts
    (x1, y1), (x2, y2) = pts[0][2:], pts[-1][2:]
    dx, dy = x2 - x1, y2 - y1; L = math.hypot(dx, dy) or 1e-9
    dmax, idx = 0, 0
    for i in range(1, len(pts) - 1):
        x, y = pts[i][2:]
        d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / L
        if d > dmax: dmax, idx = d, i
    if dmax > eps: return rdp(pts[: idx + 1], eps)[:-1] + rdp(pts[idx:], eps)
    return [pts[0], pts[-1]]


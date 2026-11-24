"""Bygger site/tours.json från OpenStreetMap-relationer + content.py.

Kör:  python3 -I build.py <scratchpad>
Steg: 1) geometri och hållplatser från OSM  2) planera ljud (återanvänd/spela in)
      3) spela in saknade klipp via ElevenLabs  4) mät längd på klippen  5) skriv tours.json
"""
import json, math, os, re, shutil, subprocess, sys, unicodedata

ROOT = sys.argv[1]
B = os.path.join(ROOT, "build"); SITE = os.path.join(ROOT, "site"); OSM = os.path.join(ROOT, "osm")
sys.path.insert(0, B)
from content import TOURS  # noqa: E402

OLD = json.load(open(os.path.join(B, "old_tours.json")))
DRY = "--dry" in sys.argv

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def xy(lat, lon, lat0):
    k = 111320.0
    return (lon * k * math.cos(math.radians(lat0)), lat * k)

def load_rel(rid):
    p = os.path.join(OSM, f"full_{rid}.json")
    if not os.path.exists(p):
        subprocess.run(["curl", "-sS", "-m", "120", "-o", p,
                        f"https://api.openstreetmap.org/api/0.6/relation/{rid}/full.json"], check=True)
    d = json.load(open(p))
    nodes = {e["id"]: e for e in d["elements"] if e["type"] == "node"}
    ways = {e["id"]: e for e in d["elements"] if e["type"] == "way"}
    rel = [e for e in d["elements"] if e["type"] == "relation" and e["id"] == rid][0]
    return nodes, ways, rel

def stitch(nodes, ways, rel):
    seqs = []
    for m in rel["members"]:
        if m["type"] == "way" and m["role"] == "" and m["ref"] in ways:
            seqs.append(list(ways[m["ref"]]["nodes"]))
    line = []
    for i, w in enumerate(seqs):
        if not line:
            nxt = seqs[i + 1] if i + 1 < len(seqs) else None
            if nxt and w[0] in (nxt[0], nxt[-1]):
                w = w[::-1]
            line = w[:]
            continue
        if line[-1] == w[0]:
            line += w[1:]
        elif line[-1] == w[-1]:
            line += w[::-1][1:]
        else:  # glapp i datan: ta närmaste orientering
            a = nodes[line[-1]]
            d0 = (nodes[w[0]]["lat"] - a["lat"]) ** 2 + (nodes[w[0]]["lon"] - a["lon"]) ** 2
            d1 = (nodes[w[-1]]["lat"] - a["lat"]) ** 2 + (nodes[w[-1]]["lon"] - a["lon"]) ** 2
            line += w if d0 <= d1 else w[::-1]
    return [(nodes[n]["lat"], nodes[n]["lon"]) for n in line if n in nodes]

def rel_stops(nodes, ways, rel):
    out = []
    for m in rel["members"]:
        if not m["role"].startswith("stop"):
            continue
        if m["type"] == "node" and m["ref"] in nodes:
            n = nodes[m["ref"]]
            name = n.get("tags", {}).get("name")
            if name and (not out or out[-1][0] != name):
                out.append((name, n["lat"], n["lon"]))
    return out

def project(pt, P, cum, start_s=0.0):
    """Närmaste punkt på linjen (efter start_s). Returnerar (s, avstånd)."""
    best = (None, 1e18)
    for i in range(len(P) - 1):
        if cum[i + 1] < start_s - 1:
            continue
        (x1, y1), (x2, y2) = P[i], P[i + 1]
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy or 1e-9
        t = max(0, min(1, ((pt[0] - x1) * dx + (pt[1] - y1) * dy) / L2))
        px, py = x1 + t * dx, y1 + t * dy
        d = math.hypot(pt[0] - px, pt[1] - py)
        s = cum[i] + t * math.sqrt(L2)
        if s < start_s - 1:
            continue
        if d < best[1]:
            best = (s, d)
    return best

def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0][2:], pts[-1][2:]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1e-9
    dmax, idx = 0, 0
    for i in range(1, len(pts) - 1):
        x, y = pts[i][2:]
        d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / L
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        return rdp(pts[: idx + 1], eps)[:-1] + rdp(pts[idx:], eps)
    return [pts[0], pts[-1]]

def old_stop(tid, name):
    for s in OLD[tid]["stops"]:
        if s["name"] == name:
            return s
    raise KeyError((tid, name))

def dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    return round(float(r.stdout.strip()), 1)

def record(text, voice, out):
    body = json.dumps({"text": text, "model_id": "eleven_multilingual_v2", "language_code": "sv",
                       "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}})
    r = subprocess.run(["curl", "-sS", "-o", out, "-w", "%{http_code}", "-H", "Content-Type: application/json",
                        "-d", body, f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128"],
                       capture_output=True, text=True)
    if r.stdout != "200":
        raise RuntimeError(f"ElevenLabs {r.stdout}: {open(out, 'rb').read(300)}")

result = {"order": [], "tours": {}}
to_record = []
for T in TOURS:
    tid = T["id"]
    nodes, ways, rel = load_rel(T["relation"])
    geo = stitch(nodes, ways, rel)
    lat0 = geo[0][0]
    P = [xy(a, b, lat0) for a, b in geo]
    cum = [0.0]
    for i in range(1, len(P)):
        cum.append(cum[-1] + math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]))
    stops_all = rel_stops(nodes, ways, rel)
    s_prev, proj = 0.0, []
    for name, la, lo in stops_all:
        s, d = project(xy(la, lo, lat0), P, cum, s_prev)
        proj.append({"name": name, "lat": round(la, 6), "lon": round(lo, 6), "s": s, "off": d})
        s_prev = s
    names = [p["name"] for p in proj]
    i0, i1 = names.index(T["from"]), names.index(T["to"])
    sec = proj[i0:i1 + 1]
    s0, s1 = sec[0]["s"] - 30, sec[-1]["s"] + 30
    # geometri för sträckan, förenklad
    pts = [(geo[i][0], geo[i][1], P[i][0], P[i][1]) for i in range(len(geo)) if s0 <= cum[i] <= s1]
    pts = rdp(pts, 6)
    route = [[round(p[0], 6), round(p[1], 6)] for p in pts]

    missing = [g for g in T["guided"] if g not in [p["name"] for p in sec]]
    if missing:
        raise SystemExit(f"{tid}: hittar inte guidade hållplatser i OSM: {missing}")

    adir = f"audio/{tid}/"
    os.makedirs(os.path.join(SITE, adir), exist_ok=True)
    stops_out = []
    for p in sec:
        st = {"name": p["name"], "lat": p["lat"], "lon": p["lon"]}
        g = T["guided"].get(p["name"])
        if g:
            old = old_stop(*g["old"]) if "old" in g else {}
            story = g.get("story") or old["story"]
            tips = g.get("tips") or old["tips"]
            sp = adir + "stop-" + slug(p["name"]) + ".mp3"
            hp = adir + "hop-" + slug(p["name"]) + ".mp3"
            hop_text = (f"Du har klivit av vid {p['name']}. Nästa {T['vehicle']} på linje {T['line']} kommer om "
                        f"några minuter. Tryck på Hoppa på igen när du vill fortsätta.")
            if tid == "goteborg-11":
                hop_text = hop_text.replace("linje 11", "linje elva")
            for path, text, reuse in [(sp, story, g.get("reuseStory") if "story" not in g else None),
                                      (hp, hop_text, g.get("reuseHop"))]:
                if reuse:
                    if not DRY:
                        shutil.copyfile(os.path.join(SITE, reuse), os.path.join(SITE, path))
                else:
                    to_record.append((T["voice"], text, path))
            st.update({"story": story, "tips": tips, "audio": sp, "hopAudio": hp})
        stops_out.append(st)
        if p["off"] > 60:
            print(f"  varning: {tid} {p['name']} ligger {p['off']:.0f} m från linjen")

    looks_out = []
    for L in T["looks"]:
        s, d = project(xy(L["lat"], L["lon"], lat0), P, cum, 0)
        lp = adir + "look-" + L["id"] + ".mp3"
        if L.get("reuse"):
            if not DRY:
                shutil.copyfile(os.path.join(SITE, L["reuse"]), os.path.join(SITE, lp))
        else:
            to_record.append((T["voice"], "Titta ut. " + L["text"], lp))
        print(f"  {tid} titta ut {L['id']}: {d:.0f} m från linjen (radie {L['r']})")
        looks_out.append({"id": L["id"], "lat": L["lat"], "lon": L["lon"], "r": L["r"], "text": L["text"], "audio": lp})

    length = sec[-1]["s"] - sec[0]["s"]
    mins = length / (T["speedKmh"] / 3.6) / 60
    print(f"{tid}: {len(sec)} hållplatser, {len(T['guided'])} guidade, {length/1000:.1f} km, ca {mins:.0f} min, {len(route)} punkter")
    result["order"].append(tid)
    result["tours"][tid] = {k: T[k] for k in ("city", "line", "vehicle", "vehicleLong", "operator", "tab", "guide",
                                              "speedKmh", "dwellSec")}
    result["tours"][tid].update({"route": route, "stops": stops_out, "looks": looks_out,
                                 "from": T["from"], "to": T["to"],
                                 "source": f"OpenStreetMap relation {T['relation']}"})

print("Att spela in:", len(to_record), "klipp,", sum(len(t) for _, t, _ in to_record), "tecken")
for v, t, p in to_record:
    print("  ", p, len(t))
if DRY:
    sys.exit()
for v, t, p in to_record:
    record(t, v, os.path.join(SITE, p))
# längder
for tid, T in result["tours"].items():
    for st in T["stops"]:
        if "audio" in st:
            st["dur"] = dur(os.path.join(SITE, st["audio"]))
    for L in T["looks"]:
        L["dur"] = dur(os.path.join(SITE, L["audio"]))
json.dump(result, open(os.path.join(SITE, "tours.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print("tours.json", os.path.getsize(os.path.join(SITE, "tours.json")), "bytes")

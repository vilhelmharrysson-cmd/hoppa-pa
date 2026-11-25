"""Bygger alla turer från SL:s och Västtrafiks officiella tidtabellsdata (GTFS Regional, Trafiklab).

Körs varje natt av .github/workflows/data.yml. Kräver miljövariabeln TRAFIKLAB_KEY
(nyckel för "GTFS Regional Static" på trafiklab.se).

Utdata:
  public/data/index.json          lista över alla turer (för linjeväljaren)
  public/data/tours/<id>.json     en fil per tur: linjeform, hållplatser, berättelser, "titta ut"

För varje linje och riktning väljs det vanligaste körmönstret (flest turer). Berättelser och
"titta ut" kommer från platsbiblioteken i content_gbg.py och content_sthlm.py.

Lokalt:  TRAFIKLAB_KEY=... python3 tools/gtfs_build.py [--cache katalog]
"""
import collections, csv, io, json, math, os, re, sys, unicodedata, urllib.request, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "public", "data")
sys.path.insert(0, HERE)
from content_sthlm import PLACES as _STH, LOOKS as STH_LOOKS, LINE_NAMES as STH_LINE_NAMES  # noqa: E402

_G = json.load(open(os.path.join(HERE, "places_gbg.json"), encoding="utf8"))
GBG_LOOKS = _G["looks"]

def _normlib(lib):
    return {norm(k): v for k, v in lib.items()}

FEEDS = {
  "vt": {"city": "Göteborg", "operator": "Västtrafik", "bbox": (57.58, 11.60, 57.86, 12.20), "api": "vt"},
  "sl": {"city": "Stockholm", "operator": "SL", "bbox": (59.22, 17.78, 59.44, 18.22), "api": "sl"},
}
# GTFS route_type -> färdmedel. Tunnelbana och tåg är inte med (inte sightseeing från fönstret).
MODES = {0: "tram", 900: "tram", 901: "tram", 902: "tram", 3: "bus", 700: "bus", 701: "bus", 702: "bus",
         704: "bus", 705: "bus", 711: "bus", 712: "bus", 715: "bus", 717: "bus", 4: "boat", 1000: "boat",
         1200: "boat"}
MODE_SV = {"tram": ("spårvagn", "vagn"), "bus": ("buss", "buss"), "boat": ("båt", "båt")}
SPEED = {"tram": 22, "bus": 18, "boat": 20}   # km/h i rörelse
DWELL = {"tram": 15, "bus": 15, "boat": 60}   # sekunder per hållplats
# Västtrafiks linjefärger (spårvagnar och stombussar, linjekartan juni 2026). [bakgrund, text]
VT_COLORS = {"1": ["#ffffff", "#231f20"], "2": ["#fddd04", "#0f3549"], "3": ["#1476c6", "#ffffff"],
             "4": ["#00a363", "#ffffff"], "5": ["#ee293d", "#ffffff"], "6": ["#f68b1a", "#0f3549"],
             "7": ["#994b0b", "#ffffff"], "8": ["#a32b9b", "#ffffff"], "9": ["#bfe8fa", "#0f3549"],
             "10": ["#c2e577", "#0f3549"], "11": ["#231f20", "#ffffff"], "12": ["#61c9b1", "#0f3549"]}
VT_BUS_COLORS = {"16": ["#0f3549", "#ffffff"], "17": ["#1d2a6b", "#fddd04"], "18": ["#231f20", "#fddd04"],
                 "19": ["#e4007d", "#ffffff"], "21": ["#a32b9b", "#ffffff"], "25": ["#1476c6", "#ffffff"]}
DEFAULT_COLORS = {("vt", "bus"): ["#0071b9", "#ffffff"], ("vt", "boat"): ["#61c9b1", "#0f3549"],
                  ("vt", "tram"): ["#0f3549", "#ffffff"], ("sl", "bus"): ["#d71d24", "#ffffff"],
                  ("sl", "boat"): ["#0089ca", "#ffffff"], ("sl", "tram"): ["#7b8086", "#ffffff"]}
SL_BLUE = ["#0089ca", "#ffffff"]   # SL:s blåbussar (stomlinjer)
SL_TRAM_COLORS = {"7": ["#7b8086", "#ffffff"], "12": ["#7b8086", "#ffffff"], "21": ["#7b8086", "#ffffff"],
                  "30": ["#d77d00", "#ffffff"], "31": ["#d77d00", "#ffffff"]}

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "", s)

def slug(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def fetch(op, cache):
    path = os.path.join(cache, f"{op}.zip") if cache else None
    if path and os.path.exists(path):
        return open(path, "rb").read()
    key = os.environ.get("TRAFIKLAB_KEY")
    if not key:
        sys.exit("TRAFIKLAB_KEY saknas")
    url = f"https://opendata.samtrafiken.se/gtfs/{op}/{op}.zip?key={key}"
    req = urllib.request.Request(url, headers={"Accept-Encoding": "gzip", "User-Agent": "hoppa-pa-databygge"})
    data = urllib.request.urlopen(req, timeout=600).read()
    if path:
        os.makedirs(cache, exist_ok=True); open(path, "wb").write(data)
    return data

def rows(z, name):
    with z.open(name) as f:
        yield from csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))

def xy(lat, lon, lat0):
    return (lon * 111320.0 * math.cos(math.radians(lat0)), lat * 111320.0)

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

def inside(b, lat, lon):
    return b[0] <= lat <= b[2] and b[1] <= lon <= b[3]

def color_for(op, mode, line, group):
    if op == "vt":
        if mode == "tram" and line in VT_COLORS: return VT_COLORS[line]
        if mode == "bus" and line in VT_BUS_COLORS: return VT_BUS_COLORS[line]
    if op == "sl":
        if mode == "tram" and line in SL_TRAM_COLORS: return SL_TRAM_COLORS[line]
        if mode == "bus" and (group or "").lower().startswith("blåbuss"): return SL_BLUE
    return DEFAULT_COLORS.get((op, mode), ["#0f3549", "#ffffff"])

def place_story(lib, name, nxt, first):
    p = lib.get(norm(name))
    if not p: return None
    imgs = p.get("images", [])
    if first and p.get("asFirst"): return {"story": p["asFirst"], "tips": p.get("tips", []), "images": imgs}
    for v in p.get("variants", []):
        if nxt in v["ifNext"]:
            return {"story": v["story"], "tips": p.get("tips", []), "images": imgs}
    if "story" not in p: return None
    return {"story": p["story"], "tips": p.get("tips", []), "images": imgs}

def sl_line_groups():
    """SL:s linjelista (öppet API, ingen nyckel): linjegrupp per linjenummer, t.ex. Blåbuss."""
    try:
        d = json.load(urllib.request.urlopen("https://transport.integration.sl.se/v1/lines?transport_authority_id=1", timeout=60))
        return {(m, l["designation"]): (l.get("group_of_lines") or l.get("name") or "")
                for m, ls in d.items() if isinstance(ls, list) for l in ls}
    except Exception as e:
        print("SL:s linjelista gick inte att hämta:", e); return {}

def build_feed(op, z):
    F = FEEDS[op]
    routes = {}
    for r in rows(z, "routes.txt"):
        mode = MODES.get(int(r.get("route_type") or -1))
        if mode: routes[r["route_id"]] = {"line": (r.get("route_short_name") or "").strip(), "long": r.get("route_long_name") or "",
                                          "mode": mode, "desc": r.get("route_desc") or ""}
    # vanligaste körmönster per linje och riktning
    pat = collections.Counter(); heads = collections.defaultdict(collections.Counter); rep = {}
    for t in rows(z, "trips.txt"):
        if t["route_id"] not in routes: continue
        k = (t["route_id"], t.get("direction_id") or "0", t.get("shape_id") or "")
        pat[k] += 1; heads[k][t.get("trip_headsign") or ""] += 1; rep.setdefault(k, t["trip_id"])
    best = {}
    for (rid, d, sh), n in pat.items():
        if (rid, d) not in best or n > pat[best[(rid, d)]]: best[(rid, d)] = (rid, d, sh)
    want_trips = {rep[k]: k for k in best.values()}
    seq = collections.defaultdict(list)
    for st in rows(z, "stop_times.txt"):
        k = want_trips.get(st["trip_id"])
        if k: seq[k].append((int(st["stop_sequence"]), st["stop_id"]))
    stops = {}
    for s in rows(z, "stops.txt"):
        stops[s["stop_id"]] = (s["stop_name"], float(s["stop_lat"]), float(s["stop_lon"]), s.get("parent_station") or "")
    want_shapes = {k[2] for k in best.values() if k[2]}
    shp = collections.defaultdict(list)
    if "shapes.txt" in z.namelist():
        for s in rows(z, "shapes.txt"):
            if s["shape_id"] in want_shapes:
                shp[s["shape_id"]].append((int(s["shape_pt_sequence"]), float(s["shape_pt_lat"]), float(s["shape_pt_lon"])))
    out = []
    for k in best.values():
        rid, d, sh = k
        R = routes[rid]
        if not R["line"] or k not in seq: continue
        if not re.search(r"\d", R["line"]): continue   # t.ex. Västtrafiks extravagnar "X" och "BÅT"
        st = [stops[sid] for _, sid in sorted(seq[k]) if sid in stops]
        names = []
        for nm, la, lo, par in st:
            nm = re.sub(r"\s*\(.*?\)$", "", nm).strip()
            if not names or names[-1][0] != nm: names.append((nm, la, lo))
        if len(names) < 2: continue
        share = sum(inside(F["bbox"], la, lo) for _, la, lo in names) / len(names)
        if share < 0.6: continue
        geo = [(la, lo) for _, la, lo in sorted(shp[sh])] if sh in shp else [(la, lo) for _, la, lo in names]
        out.append({"op": op, "route_id": rid, "dir": d, "line": R["line"], "mode": R["mode"], "desc": R["desc"],
                    "head": heads[k].most_common(1)[0][0], "trips": pat[k], "stops": names, "geo": geo})
    return out

def make_tour(p):
    op, F = p["op"], FEEDS[p["op"]]
    mode, line = p["mode"], p["line"]
    long_, short_ = MODE_SV[mode]
    lib = GBG_PLACES if op == "vt" else STH_PLACES
    looks = GBG_LOOKS if op == "vt" else STH_LOOKS
    geo = p["geo"]; lat0 = geo[0][0]
    P = [xy(a, b, lat0) for a, b in geo]
    cum = [0.0]
    for i in range(1, len(P)): cum.append(cum[-1] + math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]))
    proj, s_prev = [], -1e18
    for nm, la, lo in p["stops"]:
        s, dd, _ = project(xy(la, lo, lat0), P, cum, s_prev); proj.append((nm, la, lo, s)); s_prev = s
    first, last = proj[0][0], proj[-1][0]
    to = p["head"] or last
    length = max(1, proj[-1][3] - proj[0][3])
    mins = round(length / (SPEED[mode] / 3.6) / 60 + len(proj) * DWELL[mode] / 60)
    stops_out = []
    for k, (nm, la, lo, s) in enumerate(proj):
        st = {"name": nm, "lat": round(la, 6), "lon": round(lo, 6)}
        nxt = proj[k + 1][0] if k + 1 < len(proj) else None
        pl = place_story(lib, nm, nxt, k == 0)
        if k == 0:
            intro = f"Välkommen ombord på {long_} {line} mot {to}! Resan tar ungefär {mins} minuter."
            pl = {"story": intro + (" " + pl["story"] if pl else " Luta dig tillbaka och titta ut genom fönstret."),
                  "tips": pl["tips"] if pl else [], "images": pl.get("images", []) if pl else []}
        elif k == len(proj) - 1:
            body = pl["story"] if pl else ""
            story = body if body.startswith(("Ändhållplats", "Snart är vi framme")) else \
                f"Snart är vi framme vid ändhållplatsen {nm}." + (" " + body if body else "")
            if not story.endswith("Tack för att du åkte med!"): story += " Tack för att du åkte med!"
            pl = {"story": story, "tips": pl["tips"] if pl else [], "images": pl.get("images", []) if pl else []}
        if pl:
            st.update({"story": pl["story"], "tips": pl["tips"], "dur": round(len(pl["story"]) / 14, 1)})
            if pl.get("images"): st["images"] = pl["images"][:3]
        stops_out.append(st)
    looks_out = []
    for L in looks:
        if L.get("modes") and mode not in L["modes"]: continue
        s, d, i = project(xy(L["lat"], L["lon"], lat0), P, cum)
        if d > L["r"] or i >= len(P) - 1: continue
        text = L["text"]
        if "{side}" in text:
            (x1, y1), (x2, y2) = P[i], P[i + 1]; sx, sy = xy(L["lat"], L["lon"], lat0)
            fx, fy = x2 - x1, y2 - y1; fl = math.hypot(fx, fy) or 1
            cross = (fx * (sy - y1) - fy * (sx - x1)) / fl
            text = text.replace("{side}", "Rakt fram" if abs(cross) < 35 else ("Till vänster" if cross > 0 else "Till höger"))
        looks_out.append({"id": L["id"], "lat": L["lat"], "lon": L["lon"], "r": L["r"], "text": text, "dur": round(len(text) / 14, 1)})
    pts = [(geo[i][0], geo[i][1], P[i][0], P[i][1]) for i in range(len(geo)) if proj[0][3] - 30 <= cum[i] <= proj[-1][3] + 30]
    route = [[round(a, 6), round(b, 6)] for a, b, _, _ in rdp(pts, 6)] or [[p["stops"][0][1], p["stops"][0][2]]]
    city = F["city"]
    group = f"{slug(city)}-{mode}-{slug(line)}"
    return {
        "id": f"{group}-{slug(to)}", "group": group, "city": city, "mode": mode, "line": line,
        "vehicle": short_, "vehicleLong": long_, "operator": F["operator"], "api": F["api"],
        "tab": STH_LINE_NAMES.get(line, "") if op == "sl" and mode != "bus" else "",
        "guide": None, "speedKmh": SPEED[mode], "dwellSec": DWELL[mode], "route": route, "stops": stops_out,
        "looks": looks_out, "from": first, "to": to, "variant": f"Mot {to}",
        "color": color_for(op, mode, line, p["desc"]), "trips": p["trips"],
        "source": f"{F['operator']} via Trafiklab (GTFS Regional)",
    }

def main():
    cache = sys.argv[sys.argv.index("--cache") + 1] if "--cache" in sys.argv else None
    global GBG_PLACES, STH_PLACES
    # Kunskapsbanken (places_extra.json) fylls på med research; handskrivna texter går före.
    extra_path = os.path.join(HERE, "places_extra.json")
    extra = json.load(open(extra_path, encoding="utf8")) if os.path.exists(extra_path) else {}
    GBG_PLACES = _normlib(extra.get("Göteborg", {})) | _normlib(_G["places"])
    STH_PLACES = _normlib(extra.get("Stockholm", {})) | _normlib(_STH)
    for city, lib in (("Göteborg", GBG_PLACES), ("Stockholm", STH_PLACES)):
        for k, v in extra.get(city, {}).items():   # bilder läggs även på handskrivna platser
            if v.get("images") and not lib[norm(k)].get("images"):
                lib[norm(k)] = dict(lib[norm(k)], images=v["images"])
    groups = sl_line_groups()
    tours = []
    for op in FEEDS:
        z = zipfile.ZipFile(io.BytesIO(fetch(op, cache)))
        pats = build_feed(op, z)
        print(f"{op}: {len(pats)} linje-riktningar", flush=True)
        for p in pats:
            if op == "sl":
                g = groups.get(({"bus": "bus", "tram": "tram", "boat": "ship"}[p["mode"]], p["line"]), "")
                p["desc"] = g or p["desc"]
        tours += [make_tour(p) for p in pats]
    # unika id:n (samma linje kan ha flera riktningar med samma ändhållplats)
    seen = collections.Counter()
    for t in tours:
        seen[t["id"]] += 1
        if seen[t["id"]] > 1: t["id"] += f"-{seen[t['id']]}"
    # inspelade turer (med röst) behålls från voiced.json
    voiced = json.load(open(os.path.join(HERE, "voiced.json"), encoding="utf8"))
    tours += voiced
    os.makedirs(os.path.join(OUT, "tours"), exist_ok=True)
    for f in os.listdir(os.path.join(OUT, "tours")):
        os.remove(os.path.join(OUT, "tours", f))
    index = []
    for t in tours:
        json.dump(t, open(os.path.join(OUT, "tours", t["id"] + ".json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
        index.append({k: t.get(k) for k in ("id", "group", "city", "mode", "line", "vehicleLong", "from", "to", "variant",
                                             "color", "tab", "guide", "operator")} |
                     {"guided": sum(1 for s in t["stops"] if s.get("story"))})
    def sortkey(e):
        m = re.match(r"(\d+)(.*)", e["line"] or "")
        return (e["city"] != "Göteborg", ["tram", "bus", "boat"].index(e["mode"]), int(m.group(1)) if m else 9999,
                m.group(2) if m else e["line"], e["guide"] is not None, e["to"] or "")
    index.sort(key=sortkey)
    json.dump({"generated": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "tours": index},
              open(os.path.join(OUT, "index.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    by = collections.Counter((e["city"], e["mode"]) for e in index)
    print("Klart:", len(index), "turer", dict(by))

if __name__ == "__main__":
    main()

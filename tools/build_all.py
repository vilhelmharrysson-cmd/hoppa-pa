"""Bygger site/tours.json: alla Göteborgs spårvagnslinjer i båda riktningar (text) + Stockholm 54/66
(inspelade turer + motsatt riktning i text). Utgår från build/tours.base.json (de inspelade turerna).
Kör: python3 -I build_all.py <scratchpad>
"""
import json, math, os, sys

ROOT = sys.argv[1]
B = os.path.join(ROOT, "build"); SITE = os.path.join(ROOT, "site")
sys.path.insert(0, B)
import osmlib  # noqa: E402
osmlib.OSM = os.path.join(ROOT, "osm")
from osmlib import xy, load, stitch, stops_of, project, rdp  # noqa: E402
from content_gbg import PLACES, LOOKS  # noqa: E402
from content import TOURS as T0  # noqa: E402

OLDALL = json.load(open(os.path.join(B, "old_tours.json")))
OLD = {s["name"]: s for s in OLDALL["goteborg-11"]["stops"]}
NEW = {t["id"]: t["guided"] for t in T0}

# Västtrafiks linjefärger (linjeförteckningen, spårvagnskarta juni 2026). [bakgrund, text]
VT_COLORS = {"1": ["#ffffff", "#231f20"], "2": ["#fddd04", "#0f3549"], "3": ["#1476c6", "#ffffff"],
             "4": ["#00a363", "#ffffff"], "5": ["#ee293d", "#ffffff"], "6": ["#f68b1a", "#0f3549"],
             "7": ["#994b0b", "#ffffff"], "8": ["#a32b9b", "#ffffff"], "9": ["#bfe8fa", "#0f3549"],
             "10": ["#c2e577", "#0f3549"], "11": ["#231f20", "#ffffff"], "12": ["#61c9b1", "#0f3549"]}
SL_BUS = ["#d71d24", "#ffffff"]

# ref: (relation riktning A, relation riktning B, A från, A till, flik)
GBG = {
  "1": (5455642, 5455643, "Tynnered", "Östra Sjukhuset", "Tvärs genom stan"),
  "2": (53646, 2413519, "Högsbotorp", "Biskopsgården", "Över älven till Biskopsgården"),
  "3": (2413521, 52612, "Marklandsgatan", "Kålltorp", "Majorna och Vasastan"),
  "4": (2413520, 52774, "Mölndal", "Angered", "Mölndal, Liseberg och Angered"),
  "5": (2184933, 2181885, "Länsmansgården", "Östra Sjukhuset", "Hisingen, Korsvägen och Liseberg"),
  "6": (2213139, 2213138, "Länsmansgården", "Kortedala", "Hela stan på en vagn"),
  "7": (2247615, 2243292, "Tynnered", "Bergsjön", "Från Tynnered till rymdgatorna"),
  "8": (2413330, 54313, "Frölunda", "Angered", "Chalmers, Ullevi och Angered"),
  "9": (2418222, 54041, "Kungssten", "Angered", "Majorna, Haga och Angered"),
  "10": (2413329, 55371, "Guldheden", "Lindholmen", "Guldheden och Lindholmen"),
  "11": (2418221, 52448, "Saltholmen", "Bergsjön", "Från havet till Bergsjön"),
  "12": (19977485, 19977486, "Mölndal", "Lindholmen", "Mölndal, Liseberg och Lindholmen"),
}
SPEED, DWELL = 24, 15

# Riktningsberoende texter i platsbiblioteket
VARIANTS = {
  "Frihamnen": [{"ifNext": ["Lilla Bommen", "Nils Ericsonsplatsen", "Brunnsparken"],
                 "story": "Frihamnen var förr en hamn där varor kunde lagras utan tull. Nu växer här en ny stadsdel fram. Strax korsar vi Göta älv på Hisingsbron, en lyftbro som öppnade 2021 och ersatte den gamla Götaälvbron."}],
}
AS_FIRST = {
  "Saltholmen": "Saltholmen är porten till Göteborgs södra skärgård. Härifrån går färjor till bilfria öar som Brännö, Styrsö och Vrångö, och båtarna ingår i samma biljett som spårvagnen.",
  "Östra Sjukhuset": "Vi startar vid Östra sjukhuset. Härifrån är det nära till Delsjöområdet, ett stort naturreservat med sjöar, skog och bad.",
  "Virginsgatan": "Vi startar i Kålltorp, ett lugnt bostadsområde i östra Göteborg. Härifrån är det inte långt till Delsjöområdet, ett stort naturreservat med sjöar och skog.",
}

def gbg_place(name, nxt, first):
    if first and name in AS_FIRST:
        p = PLACES.get(name, {})
        tips = place_tips(name)
        return {"story": AS_FIRST[name], "tips": tips}
    for v in VARIANTS.get(name, []):
        if nxt in v["ifNext"]:
            return {"story": v["story"], "tips": place_tips(name)}
    p = PLACES.get(name)
    if not p: return None
    if "old" in p: o = OLD[p["old"]]; return {"story": o["story"], "tips": o["tips"]}
    if "new11" in p: g = NEW["goteborg-11"][p["new11"]]; return {"story": g["story"], "tips": g["tips"]}
    return {"story": p["story"], "tips": p["tips"]}

def place_tips(name):
    p = PLACES.get(name)
    if not p: return []
    if "old" in p: return OLD[p["old"]]["tips"]
    if "new11" in p: return NEW["goteborg-11"][p["new11"]]["tips"]
    return p["tips"]

def geometry(rid, first=None, last=None):
    nodes, ways, rel = load(rid)
    geo = stitch(nodes, ways, rel)
    lat0 = geo[0][0]
    P = [xy(a, b, lat0) for a, b in geo]
    cum = [0.0]
    for i in range(1, len(P)):
        cum.append(cum[-1] + math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]))
    proj, s_prev = [], -1e18
    for name, la, lo in stops_of(nodes, rel):
        s, d, _ = project(xy(la, lo, lat0), P, cum, s_prev)
        proj.append((name, la, lo, s, d)); s_prev = s
        if d > 60: print(f"  varning: {rel['tags'].get('name')} {name} {d:.0f} m från linjen")
    names = [p[0] for p in proj]
    i0 = names.index(first) if first else 0
    i1 = len(names) - 1 - names[::-1].index(last) if last else len(names) - 1
    proj = proj[i0:i1 + 1]
    pts = [(geo[i][0], geo[i][1], P[i][0], P[i][1]) for i in range(len(geo)) if proj[0][3] - 30 <= cum[i] <= proj[-1][3] + 30]
    route = [[round(p[0], 6), round(p[1], 6)] for p in rdp(pts, 6)]
    return proj, route, P, cum, lat0, rel

def looks_for(P, cum, lat0, looks):
    out = []
    for L in looks:
        s, d, i = project(xy(L["lat"], L["lon"], lat0), P, cum)
        if d > L["r"]: continue
        if "{side}" in L["text"]:
            (x1, y1), (x2, y2) = P[i], P[i + 1]
            sx, sy = xy(L["lat"], L["lon"], lat0)
            fx, fy = x2 - x1, y2 - y1; fl = math.hypot(fx, fy) or 1
            cross = (fx * (sy - y1) - fy * (sx - x1)) / fl
            side = "Rakt fram" if abs(cross) < 35 else ("Till vänster" if cross > 0 else "Till höger")
            text = L["text"].replace("{side}", side)
        else:
            text = L["text"]
        out.append({"id": L["id"], "lat": L["lat"], "lon": L["lon"], "r": L["r"], "text": text, "dur": round(len(text) / 14, 1)})
    return out

def minutes(proj, speed, dwell):
    return round((proj[-1][3] - proj[0][3]) / (speed / 3.6) / 60 + len(proj) * dwell / 60)

base = json.load(open(os.path.join(B, "tours.base.json")))
tours = {}

# --- Göteborg, båda riktningar ----------------------------------------------
for ref, (ra, rb, fa, ta, tab) in GBG.items():
    for suffix, rid, frm, to in (("a", ra, fa, ta), ("b", rb, ta, fa)):
        proj, route, P, cum, lat0, rel = geometry(rid)
        mins = minutes(proj, SPEED, DWELL)
        stops_out = []
        for k, (name, la, lo, s, d) in enumerate(proj):
            st = {"name": name, "lat": round(la, 6), "lon": round(lo, 6)}
            nxt = proj[k + 1][0] if k + 1 < len(proj) else None
            pl = gbg_place(name, nxt, k == 0)
            if k == 0:
                intro = f"Välkommen ombord på spårvagn {ref} mot {to}! Resan tar ungefär {mins} minuter, och jag berättar om platserna vi passerar."
                pl = {"story": intro + (" " + pl["story"] if pl else " Luta dig tillbaka och titta ut genom fönstret."),
                      "tips": pl["tips"] if pl else []}
            elif k == len(proj) - 1:
                body = pl["story"] if pl else ""
                if body.startswith(("Ändhållplatsen", "Snart är vi framme")):
                    story = body
                else:
                    story = f"Snart är vi framme vid ändhållplatsen {name}." + (" " + body if body else "")
                pl = {"story": story + ("" if story.endswith("Tack för att du åkte med!") else " Tack för att du åkte med!"),
                      "tips": pl["tips"] if pl else []}
            if pl:
                st.update({"story": pl["story"], "tips": pl["tips"], "dur": round(len(pl["story"]) / 14, 1)})
            stops_out.append(st)
        tid = f"goteborg-{ref}-{suffix}"
        tours[tid] = {"city": "Göteborg", "line": ref, "vehicle": "vagn", "vehicleLong": "spårvagn",
                      "operator": "Västtrafik", "tab": tab, "guide": None, "speedKmh": SPEED, "dwellSec": DWELL,
                      "route": route, "stops": stops_out, "looks": looks_for(P, cum, lat0, LOOKS),
                      "from": frm, "to": to, "group": f"goteborg-{ref}", "variant": f"Mot {to}",
                      "color": VT_COLORS[ref],
                      "source": f"OpenStreetMap relation {rid}, kontrollerad mot Västtrafiks linjekarta juni 2026"}
        g = sum(1 for x in stops_out if "story" in x)
        print(f"{tid}: {frm} → {to}, {len(stops_out)} hpl, {g} guidade, {len(tours[tid]['looks'])} titta ut, ca {mins} min")

# --- Inspelade turer från tidigare --------------------------------------------
fl = base["tours"]["goteborg-11"]
fl.update({"group": "goteborg-11", "variant": "Med röst: Drottningtorget → Saltholmen", "color": VT_COLORS["11"]})
tours["goteborg-11"] = fl
s54 = base["tours"]["stockholm-54"]; s54.update({"group": "stockholm-54", "variant": "Mot Reimersholme", "color": SL_BUS})
s66 = base["tours"]["stockholm-66"]; s66.update({"group": "stockholm-66", "variant": "Mot Sofia", "color": SL_BUS})
tours["stockholm-54"] = s54; tours["stockholm-66"] = s66

# --- Stockholm, motsatt riktning (text) ----------------------------------------
def sth_old(tid, name):
    for s in OLDALL[tid]["stops"]:
        if s["name"] == name: return s
    raise KeyError(name)

STH_REV = [
  {"id": "stockholm-54-b", "rel": 17927240, "line": "54", "first": "Reimersholme", "last": "Fridhemsplan",
   "from": "Reimersholme", "to": "Fridhemsplan", "group": "stockholm-54", "tab": "Över Västerbron", "speed": 14,
   "guided": {
     "Reimersholme": {"story": "Välkommen ombord på buss 54 mot Fridhemsplan! Den här korta turen tar dig över Västerbron, med en av Stockholms bästa utsikter. Vi startar på Reimersholme, en liten ö som fått sitt namn efter Anders Reimers, som ägde den på 1700-talet. Här låg länge en brännvinsfabrik, och namnet Reimersholms levde vidare på flaskorna.",
                      "tips": sth_old("stockholm-54", "Reimersholme")["tips"]},
     "Bergsunds strand": sth_old("stockholm-54", "Bergsunds strand"),
     "Hornstull": sth_old("stockholm-54", "Hornstull"),
     "Högalidsgatan": {"story": "Kyrkan med de två tornen här bredvid är Högalidskyrkan, invigd 1923. Den syns från långt håll och är ett landmärke för hela västra Söder. Håll utkik nu, för strax kör vi upp på Västerbron.",
                       "tips": [["Högalidskyrkan", "2 min"], ["Promenad upp på Västerbron för utsikten", "6 min"]]},
     "Mariebergsgatan": {"story": "Vi är tillbaka på Kungsholmen, i Marieberg. Det höga tornet i närheten är DN-skrapan, där Dagens Nyheter flyttade in på 1960-talet. Strax intill ligger Rålambshovsparken, en av stadens populäraste sommarparker.",
                         "tips": sth_old("stockholm-54", "Mariebergsgatan")["tips"]},
     "Fridhemsplan": {"story": "Snart är vi framme vid ändhållplatsen Fridhemsplan, en av Kungsholmens stora knutpunkter med tunnelbana, bussar och butiker. Kungsholmen kallades på 1500-talet Munklägret, efter munkarna som hade mark här. Tack för att du åkte med!",
                      "tips": sth_old("stockholm-54", "Fridhemsplan")["tips"]},
   },
   "looks": [
     {"id": "vasterbron", "lat": 59.3233, "lon": 18.0268, "r": 170,
      "text": "Vi kör över Västerbron. Titta åt höger: där ligger Stadshuset, Riddarholmen och Gamla stan. Under oss, till vänster, ligger Långholmen."},
     {"id": "langholmen", "lat": 59.3177, "lon": 18.0280, "r": 120,
      "text": "Till vänster, på andra sidan vattnet, ligger Långholmen."}]},
  {"id": "stockholm-66-b", "rel": 2227911, "line": "66", "first": "Tengdahlsgatan", "last": "Hornstull",
   "from": "Sofia", "to": "Hornstull", "group": "stockholm-66", "tab": "Tvärs över Söder", "speed": 13,
   "guided": {
     "Tengdahlsgatan": {"story": "Välkommen ombord på buss 66! Den här turen tar dig tvärs över Södermalm, från kvarteren kring Sofia i öster till Hornstull i väster. Bussen fortsätter sedan till Reimersholme. Vi börjar i Sofia, den östligaste delen av Södermalm.",
                        "tips": sth_old("stockholm-66", "Tengdahlsgatan")["tips"]},
     "Erstagatan": sth_old("stockholm-66", "Erstagatan"),
     "Klippgatan": sth_old("stockholm-66", "Klippgatan"),
     "Södermannagatan": sth_old("stockholm-66", "Södermannagatan"),
     "Skanstull": sth_old("stockholm-66", "Skanstull"),
     "Eriksdal": sth_old("stockholm-66", "Eriksdal"),
     "Södra station": NEW["stockholm-66"]["Södra station"],
     "Skinnarviken": {"story": "Uppe till höger ligger Skinnarviksberget, den högsta naturliga punkten i Stockholms innerstad. Klättra upp så får du en vid utsikt över Riddarfjärden, Stadshuset och Kungsholmen. Namnet kommer från skinnarna, hantverkarna som beredde skinn och läder vid viken här förr i tiden.",
                      "tips": NEW["stockholm-66"]["Skinnarviken"]["tips"]},
     "Hornstull": {"story": "Snart är vi framme vid Hornstull, uppkallat efter tullen som en gång låg här vid stadsgränsen. Här slutar turen, men bussen fortsätter till Reimersholme om du vill åka vidare. Tack för att du åkte med!",
                   "tips": sth_old("stockholm-66", "Hornstull")["tips"]},
   },
   "looks": [
     {"id": "arstaviken", "lat": 59.3080, "lon": 18.0680, "r": 160, "text": "Söderut glittrar Årstaviken."},
     {"id": "sofiakyrka", "lat": 59.3122, "lon": 18.0858, "r": 160, "text": "Uppe på berget syns Sofia kyrka."}]},
]
for R in STH_REV:
    proj, route, P, cum, lat0, rel = geometry(R["rel"], R["first"], R["last"])
    stops_out = []
    for name, la, lo, s, d in proj:
        st = {"name": name, "lat": round(la, 6), "lon": round(lo, 6)}
        g = R["guided"].get(name)
        if g: st.update({"story": g["story"], "tips": g["tips"], "dur": round(len(g["story"]) / 14, 1)})
        stops_out.append(st)
    missing = [n for n in R["guided"] if n not in [p[0] for p in proj]]
    assert not missing, missing
    tours[R["id"]] = {"city": "Stockholm", "line": R["line"], "vehicle": "buss", "vehicleLong": "buss", "operator": "SL",
                      "tab": R["tab"], "guide": None, "speedKmh": R["speed"], "dwellSec": 20, "route": route,
                      "stops": stops_out, "looks": looks_for(P, cum, lat0, R["looks"]), "from": R["from"], "to": R["to"],
                      "group": R["group"], "variant": f"Mot {R['to']}", "color": SL_BUS,
                      "source": f"OpenStreetMap relation {R['rel']}"}
    print(f"{R['id']}: {R['from']} → {R['to']}, {len(stops_out)} hpl, {len(R['guided'])} guidade, ca {minutes(proj, R['speed'], 20)} min")

order = []
for ref in GBG:
    order += [f"goteborg-{ref}-a", f"goteborg-{ref}-b"] + (["goteborg-11"] if ref == "11" else [])
order += ["stockholm-54", "stockholm-54-b", "stockholm-66", "stockholm-66-b"]
assert set(order) == set(tours), set(tours) ^ set(order)
json.dump({"order": order, "tours": tours}, open(os.path.join(SITE, "tours.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(len(order), "turer, tours.json", os.path.getsize(os.path.join(SITE, "tours.json")), "bytes")

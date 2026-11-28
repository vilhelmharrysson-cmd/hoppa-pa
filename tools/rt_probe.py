"""Undersöker GTFS Sweden 3 Realtime: vilka operatörer som har fordonspositioner och vilka fält som finns.
  TRAFIKLAB_SWEDEN3_RT_KEY=... python3 tools/rt_probe.py
"""
import collections, json, os, urllib.request
from google.transit import gtfs_realtime_pb2

KEY = os.environ["TRAFIKLAB_SWEDEN3_RT_KEY"]
OPS = ["sl"] or ["sl", "vt", "ul", "otraf", "klt", "skane", "dt", "varm", "xt", "orebro", "vastmanland", "jlt", "krono", "halland", "sormland", "gotland", "blekinge", "norrbotten", "vasterbotten", "jamtland", "vasternorrland", "kalmar"]
out = {}
for op in OPS:
    for kind in ("VehiclePositions", "TripUpdates"):
        url = f"https://opendata.samtrafiken.se/gtfs-rt-sweden/{op}/{kind}Sweden.pb?key={KEY}"
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers={"Accept-Encoding": "gzip"}), timeout=60).read()
        except Exception as e:
            out[f"{op}/{kind}"] = str(e)[:80]; continue
        if data[:2] == b"\x1f\x8b":
            import gzip; data = gzip.decompress(data)
        f = gtfs_realtime_pb2.FeedMessage()
        try: f.ParseFromString(data)
        except Exception as e:
            out[f"{op}/{kind}"] = "ej protobuf: " + repr(data[:120]); print(op, kind, out[f"{op}/{kind}"], flush=True); continue
        ents = list(f.entity)
        info = {"bytes": len(data), "entities": len(ents)}
        if kind == "VehiclePositions" and ents:
            v = [e.vehicle for e in ents if e.HasField("vehicle")]
            info["with_trip"] = sum(1 for x in v if x.trip.trip_id)
            info["with_route"] = sum(1 for x in v if x.trip.route_id)
            info["with_bearing"] = sum(1 for x in v if x.position.HasField("bearing"))
            info["with_speed"] = sum(1 for x in v if x.position.HasField("speed"))
            info["sample"] = str(v[0])[:600]
        if kind == "TripUpdates" and ents:
            tu = [e.trip_update for e in ents if e.HasField("trip_update")]
            info["with_route"] = sum(1 for x in tu if x.trip.route_id)
            info["with_dir"] = sum(1 for x in tu if x.trip.HasField("direction_id"))
            info["sample"] = str(tu[0])[:900]
        out[f"{op}/{kind}"] = info
        print(op, kind, json.dumps(info, ensure_ascii=False)[:700], flush=True)

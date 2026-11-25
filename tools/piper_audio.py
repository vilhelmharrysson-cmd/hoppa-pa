"""Spelar in berättelser som saknar ljud med Piper (lokal, gratis talsyntes).

Körs i den nattliga GitHub Action efter gtfs_build.py. Turer med inläst röst (ElevenLabs) rörs inte.
Varje klipp namnges efter en hash av röst + text, så samma platsberättelse delas av alla linjer
och bara nya eller ändrade texter spelas in. Klipp som inte längre används tas bort.

  python3 tools/piper_audio.py <röstmodell.onnx> [--workers 4]
"""
import hashlib, json, multiprocessing as mp, os, subprocess, sys, tempfile, wave

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOURS = os.path.join(ROOT, "public", "data", "tours")
ADIR = os.path.join(ROOT, "public", "audio", "piper")
MODEL = sys.argv[1]
VOICE_ID = os.path.basename(MODEL).replace(".onnx", "")
WORKERS = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else max(1, mp.cpu_count())

def key(text):
    return hashlib.sha1(f"{VOICE_ID}|{text}".encode()).hexdigest()[:16]

_voice = None
def synth(item):
    global _voice
    k, text = item
    out = os.path.join(ADIR, k + ".mp3")
    if os.path.exists(out):
        return k, None
    from piper import PiperVoice
    from piper.config import SynthesisConfig
    if _voice is None:
        _voice = PiperVoice.load(MODEL, config_path=MODEL + ".json")
    cfg = SynthesisConfig(length_scale=1.05, noise_scale=0.6, noise_w_scale=0.8)
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        with wave.open(tmp.name, "wb") as w:
            _voice.synthesize_wav(text, w, syn_config=cfg)
        with wave.open(tmp.name, "rb") as w:
            dur = w.getnframes() / float(w.getframerate())
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp.name, "-ac", "1", "-ar", "22050",
                        "-b:a", "32k", out], check=True)
    return k, round(dur, 1)

def main():
    os.makedirs(ADIR, exist_ok=True)
    tours = {}
    for f in sorted(os.listdir(TOURS)):
        t = json.load(open(os.path.join(TOURS, f), encoding="utf8"))
        if t.get("guide"):      # ElevenLabs-turer behålls som de är
            continue
        tours[f] = t
    jobs = {}
    for t in tours.values():
        for st in t["stops"]:
            if st.get("story"): jobs.setdefault(key(st["story"]), st["story"])
        for L in t.get("looks", []):
            jobs.setdefault(key("Titta ut. " + L["text"]), "Titta ut. " + L["text"])
    missing = [(k, v) for k, v in jobs.items() if not os.path.exists(os.path.join(ADIR, k + ".mp3"))]
    print(f"{len(jobs)} unika texter, {len(missing)} att spela in med {WORKERS} processer", flush=True)
    durs = {}
    with mp.Pool(WORKERS) as pool:
        for n, (k, dur) in enumerate(pool.imap_unordered(synth, missing, chunksize=4)):
            if dur: durs[k] = dur
            if n % 200 == 0: print(" ", n, flush=True)
    # längder för klipp som fanns sedan tidigare sparas i en liten katalog
    cat_path = os.path.join(ADIR, "index.json")
    cat = json.load(open(cat_path)) if os.path.exists(cat_path) else {}
    cat.update(durs)
    for f, t in tours.items():
        for st in t["stops"]:
            if st.get("story"):
                k = key(st["story"]); st["audio"] = f"audio/piper/{k}.mp3"
                if k in cat: st["dur"] = cat[k]
        for L in t.get("looks", []):
            k = key("Titta ut. " + L["text"]); L["audio"] = f"audio/piper/{k}.mp3"
            if k in cat: L["dur"] = cat[k]
        t["tts"] = "Piper"
        json.dump(t, open(os.path.join(TOURS, f), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    # städa bort klipp som inte används längre
    used = set(jobs)
    removed = 0
    for f in os.listdir(ADIR):
        if f.endswith(".mp3") and f[:-4] not in used:
            os.remove(os.path.join(ADIR, f)); removed += 1
    cat = {k: v for k, v in cat.items() if k in used}
    json.dump(cat, open(cat_path, "w"), separators=(",", ":"))
    size = sum(os.path.getsize(os.path.join(ADIR, f)) for f in os.listdir(ADIR)) // (1024 * 1024)
    print(f"Klart: {len(durs)} nya klipp, {removed} borttagna, {size} MB ljud totalt")

if __name__ == "__main__":
    main()

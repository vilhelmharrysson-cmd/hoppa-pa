// Resenärernas bidrag och enkel statistik, lagrat i Cloudflare D1 (binding DB).
//
//   POST /api/feedback   {kind, city, tour, stop, text, contact?}  → hamnar i granskningskön
//   GET  /api/ugc?city=Göteborg                                     → godkända tips per hållplats
//   POST /api/hit        {ev, tour?}                                → räknare per dag (inga personuppgifter)
//   GET/POST /api/admin  (kräver hemligheten ADMIN_KEY)             → granska bidrag, se statistik
//
// Tabellerna skapas automatiskt första gången. Utan DB svarar API:t 503 och appen döljer funktionerna.

const KINDS = ["fel", "tips", "berattelse", "bild", "annat"];
const EVENTS = ["open", "start", "gps", "finish", "offline", "share", "more", "alight", "lang_en", "kids", "theme"];
let ready = null;

const json = (data, status = 200, extra = {}) =>
  new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...extra } });

async function init(db) {
  if (!ready) ready = db.batch([
    db.prepare(`CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, created TEXT NOT NULL,
      kind TEXT NOT NULL, city TEXT, tour TEXT, stop TEXT, text TEXT NOT NULL, contact TEXT, status TEXT NOT NULL DEFAULT 'ny',
      reply TEXT, who TEXT)`),
    db.prepare(`CREATE INDEX IF NOT EXISTS feedback_status ON feedback(status, kind, city)`),
    db.prepare(`CREATE TABLE IF NOT EXISTS hits (day TEXT NOT NULL, ev TEXT NOT NULL, tour TEXT NOT NULL DEFAULT '', n INTEGER NOT NULL DEFAULT 0,
      PRIMARY KEY (day, ev, tour))`),
  ]).catch((e) => { ready = null; throw e; });
  return ready;
}

// grov spamspärr: högst 20 bidrag per avsändare och dygn (avsändaren lagras bara som en hash med dygnets datum)
async function who(req) {
  const ip = req.headers.get("cf-connecting-ip") || "";
  const day = new Date().toISOString().slice(0, 10);
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(day + "|" + ip));
  return [...new Uint8Array(buf)].slice(0, 8).map((b) => b.toString(16).padStart(2, "0")).join("");
}
const clip = (s, n) => String(s ?? "").replace(/[\u0000-\u0008\u000b-\u001f]/g, "").trim().slice(0, n);

export async function handle(req, env = {}) {
  const url = new URL(req.url);
  const db = env.DB;
  if (!db) return json({ error: "ingen databas" }, 503);
  await init(db);
  const path = url.pathname;

  if (path === "/api/feedback" && req.method === "POST") {
    let b; try { b = await req.json(); } catch { return json({ error: "ogiltig data" }, 400); }
    const kind = KINDS.includes(b.kind) ? b.kind : "annat";
    const text = clip(b.text, 2000);
    if (text.length < 3) return json({ error: "skriv lite mer" }, 400);
    const w = await who(req);
    const day = new Date().toISOString().slice(0, 10);
    const { n } = await db.prepare(`SELECT COUNT(*) n FROM feedback WHERE who=? AND created>=?`).bind(w, day).first();
    if (n >= 20) return json({ error: "för många bidrag i dag" }, 429);
    await db.prepare(`INSERT INTO feedback (created, kind, city, tour, stop, text, contact, who) VALUES (?,?,?,?,?,?,?,?)`)
      .bind(new Date().toISOString(), kind, clip(b.city, 40), clip(b.tour, 80), clip(b.stop, 80), text, clip(b.contact, 120), w).run();
    return json({ ok: true });
  }

  if (path === "/api/ugc" && req.method === "GET") {
    const city = clip(url.searchParams.get("city"), 40);
    const { results } = await db.prepare(`SELECT stop, text, reply FROM feedback WHERE status='ok' AND kind='tips' AND city=? ORDER BY id DESC LIMIT 2000`).bind(city).all();
    const out = {};
    for (const r of results) (out[r.stop] = out[r.stop] || []).push(r.reply || r.text);
    return json(out, 200, { "cache-control": "public, max-age=300" });
  }

  if (path === "/api/hit" && req.method === "POST") {
    let b; try { b = await req.json(); } catch { return json({ ok: false }, 400); }
    if (!EVENTS.includes(b.ev)) return json({ ok: false }, 400);
    const tour = clip(b.tour, 80).replace(/[^a-z0-9-]/g, "");
    await db.prepare(`INSERT INTO hits (day, ev, tour, n) VALUES (?,?,?,1) ON CONFLICT(day, ev, tour) DO UPDATE SET n=n+1`)
      .bind(new Date().toISOString().slice(0, 10), b.ev, tour).run();
    return json({ ok: true });
  }

  if (path === "/api/admin") {
    const key = req.headers.get("x-admin-key") || "";
    if (!env.ADMIN_KEY || key !== env.ADMIN_KEY) return json({ error: "fel nyckel" }, 401);
    if (req.method === "GET") {
      const status = clip(url.searchParams.get("status") || "ny", 10);
      const { results: items } = await db.prepare(`SELECT id, created, kind, city, tour, stop, text, contact, status, reply FROM feedback WHERE status=? ORDER BY id DESC LIMIT 300`).bind(status).all();
      const days = Math.min(90, Number(url.searchParams.get("days")) || 30);
      const since = new Date(Date.now() - days * 864e5).toISOString().slice(0, 10);
      const { results: byEv } = await db.prepare(`SELECT ev, SUM(n) n FROM hits WHERE day>=? GROUP BY ev ORDER BY n DESC`).bind(since).all();
      const { results: byDay } = await db.prepare(`SELECT day, SUM(n) n FROM hits WHERE day>=? AND ev='open' GROUP BY day ORDER BY day`).bind(since).all();
      const { results: topTours } = await db.prepare(`SELECT tour, SUM(n) n FROM hits WHERE day>=? AND ev='open' AND tour<>'' GROUP BY tour ORDER BY n DESC LIMIT 25`).bind(since).all();
      const { results: counts } = await db.prepare(`SELECT status, COUNT(*) n FROM feedback GROUP BY status`).all();
      return json({ items, stats: { byEv, byDay, topTours }, counts });
    }
    if (req.method === "POST") {
      let b; try { b = await req.json(); } catch { return json({ error: "ogiltig data" }, 400); }
      const status = ["ok", "nej", "klar", "ny"].includes(b.status) ? b.status : null;
      if (!status || !Number.isInteger(b.id)) return json({ error: "ogiltig data" }, 400);
      await db.prepare(`UPDATE feedback SET status=?, reply=COALESCE(?, reply) WHERE id=?`).bind(status, b.reply ? clip(b.reply, 400) : null, b.id).run();
      return json({ ok: true });
    }
  }
  return json({ error: "saknas" }, 404);
}

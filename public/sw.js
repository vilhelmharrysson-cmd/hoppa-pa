// Offline-stöd: sidan och turdatan hämtas från nätet i första hand (så att ändringar syns),
// ljudfiler och ikoner sparas i telefonen när de spelats en gång. Realtid (/api) cachas aldrig.
const CACHE = "hoppa-pa-v3";
const OFFLINE = "hoppa-pa-offline";   // turer som sparats med "Spara offline" (rensas inte vid uppdatering)
const CORE = ["./", "index.html", "data/index.json", "manifest.webmanifest", "icons/icon-192.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(CORE)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE && k !== OFFLINE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.pathname.startsWith("/api/")) return;
  if (url.origin !== location.origin) {
    // bilder från Wikimedia m.fl.: från telefonen om turen är sparad offline, annars nätet
    if (e.request.destination === "image" || /\.(jpe?g|png|webp)$/i.test(url.pathname))
      e.respondWith(caches.match(e.request.url).then((hit) => hit || fetch(e.request)));
    return;
  }
  if (/\.(mp3|png)$/.test(url.pathname)) {
    // ljud och ikoner: från telefonen om de finns, annars nätet (och spara)
    e.respondWith(caches.open(CACHE).then(async (c) => {
      const hit = await caches.match(e.request.url);
      if (hit) return hit;
      const res = await fetch(e.request);
      if (res.ok && res.status === 200) c.put(e.request, res.clone());
      return res;
    }));
    return;
  }
  // sidan och turdata: nätet först, telefonens kopia om du är offline (eller nätet är segt, t.ex. i en tunnel)
  e.respondWith((async () => {
    const net = fetch(e.request).then((res) => {
      if (res.ok) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(e.request, copy)); }
      return res;
    });
    const cached = await caches.match(e.request, { ignoreSearch: true });
    if (!cached) return net;
    return Promise.race([net, new Promise((r) => setTimeout(() => r(cached), 5000))]).catch(() => cached);
  })());
});

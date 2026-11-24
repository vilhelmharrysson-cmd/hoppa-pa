// Offline-stöd: sidan och turdatan hämtas från nätet i första hand (så att ändringar syns),
// ljudfiler och ikoner sparas i telefonen när de spelats en gång. Realtid (/api) cachas aldrig.
const CACHE = "hoppa-pa-v1";
const CORE = ["./", "index.html", "tours.json", "manifest.webmanifest", "icons/icon-192.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(CORE)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin || url.pathname.startsWith("/api/")) return;
  if (/\.(mp3|png)$/.test(url.pathname)) {
    // ljud och ikoner: från telefonen om de finns, annars nätet (och spara)
    e.respondWith(caches.open(CACHE).then(async (c) => {
      const hit = await c.match(e.request);
      if (hit) return hit;
      const res = await fetch(e.request);
      if (res.ok && res.status === 200) c.put(e.request, res.clone());
      return res;
    }));
    return;
  }
  // sidan och turdata: nätet först, telefonens kopia om du är offline
  e.respondWith(fetch(e.request).then((res) => {
    if (res.ok) caches.open(CACHE).then((c) => c.put(e.request, res.clone()));
    return res;
  }).catch(() => caches.match(e.request)));
});

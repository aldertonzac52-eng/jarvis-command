// JARVIS service worker — network-first so the app always shows the latest version online,
// with a cached fallback when offline.
const CACHE = "jarvis-cache-v7";
self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.add("./")).then(() => self.skipWaiting()).catch(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())
  );
});
self.addEventListener("fetch", (e) => {
  // Only manage page navigations (the HTML). Always try the network first; fall back to cache offline.
  if (e.request.mode === "navigate") {
    e.respondWith(
      fetch(e.request)
        .then((r) => { const cp = r.clone(); caches.open(CACHE).then((c) => c.put("./", cp)); return r; })
        .catch(() => caches.match("./"))
    );
  }
});
// ---- push notifications ----
self.addEventListener("push", (e) => {
  let data = { title: "JARVIS", body: "", url: "./" };
  try { data = Object.assign(data, e.data.json()); } catch (_e) { try { if (e.data) data.body = e.data.text(); } catch (_e2) {} }
  e.waitUntil(self.registration.showNotification(data.title, { body: data.body, data: { url: data.url || "./" }, tag: data.tag || undefined, renotify: false }));
});
self.addEventListener("notificationclick", (e) => {
  e.notification.close();
  const url = (e.notification.data && e.notification.data.url) || "./";
  e.waitUntil(clients.matchAll({ type: "window", includeUncontrolled: true }).then((cl) => {
    for (const c of cl) { if ("focus" in c) { try { c.navigate(url); } catch (_e) {} return c.focus(); } }
    if (clients.openWindow) return clients.openWindow(url);
  }));
});

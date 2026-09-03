const CACHE_NAME = "deng-pharma-v1";
const urlsToCache = [
  "/",
  "/manifest.json",
  "/icons/icon-192x192.png",
  "/icons/icon-512x512.png"
];

// Installation
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(urlsToCache))
  );
});

// Activation
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) =>
      Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      )
    )
  );
});

// 🔥 Fetch : ignorer les requêtes API et les images externes
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Ignorer les requêtes API (backend)
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(fetch(event.request));
    return;
  }

  // Ignorer les images externes (Cloudinary, etc.)
  if (url.hostname.includes("cloudinary") || url.hostname.includes("imgur")) {
    event.respondWith(fetch(event.request));
    return;
  }

  // Pour les autres ressources, servir du cache ou du réseau
  event.respondWith(
    caches.match(event.request).then((response) => response || fetch(event.request))
  );
});

// Notifications push
self.addEventListener("push", (event) => {
  const data = event.data ? event.data.json() : {};
  const options = {
    body: data.body,
    icon: "/icons/icon-192x192.png",
    badge: "/icons/icon-192x192.png",
  };
  event.waitUntil(
    self.registration.showNotification(data.title || "DENG PHARMA", options)
  );
});

// Clic sur notification
self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  event.waitUntil(clients.openWindow("/"));
});
const CACHE_NAME = "deng-pharma-v2";
const STATIC_ASSETS = [
  "/manifest.json",
  "/icons/icon-192x192.png",
  "/icons/icon-512x512.png"
];

// Installation
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      // addAll échoue si UN SEUL fichier est introuvable → on ajoute individuellement
      return Promise.all(
        STATIC_ASSETS.map((url) =>
          cache.add(url).catch((err) => console.warn(`⚠️ Cache skip: ${url}`, err))
        )
      );
    })
  );
  self.skipWaiting();
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
  self.clients.claim();
});

// 🔥 Fetch : STRATÉGIE "network-first" pour éviter les blocages
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // ✅ 1. IGNORER complètement les chunks Next.js (Turbopack, dev et prod)
  if (url.pathname.startsWith("/_next/")) {
    return;  // Laisser le navigateur gérer normalement
  }

  // ✅ 2. IGNORER les requêtes API
  if (url.pathname.startsWith("/api/")) {
    return;
  }

  // ✅ 3. IGNORER les websockets et HMR (Hot Module Replacement)
  if (url.protocol === "ws:" || url.protocol === "wss:") {
    return;
  }

  // ✅ 4. IGNORER les images externes
  if (
    url.hostname.includes("cloudinary") ||
    url.hostname.includes("imgur") ||
    url.hostname !== self.location.hostname
  ) {
    return;
  }

  // ✅ 5. IGNORER les requêtes non-GET (POST, PUT, DELETE...)
  if (event.request.method !== "GET") {
    return;
  }

  // ✅ 6. Pour les autres ressources : network-first avec fallback cache
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Mettre en cache uniquement les réponses valides
        if (response && response.status === 200 && response.type === "basic") {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone).catch(() => {});
          });
        }
        return response;
      })
      .catch(() => {
        // Fallback : chercher dans le cache
        return caches.match(event.request).then((cached) => {
          if (cached) return cached;
          // Dernier recours : réponse vide plutôt que rejet
          return new Response("", { status: 503, statusText: "Offline" });
        });
      })
  );
});

// Notifications push
self.addEventListener("push", (event) => {
  const data = event.data ? event.data.json() : {};
  const options = {
    body: data.body || "Nouvelle notification",
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
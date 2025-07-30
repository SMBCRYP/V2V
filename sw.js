const CACHE_NAME = 'v2v-cache-v3'; // Cache version updated
const urlsToCache = [
  '.',
  'index.html',
  'configs.json',
  'manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', event => {
  // For configs.json, always fetch from network to get the latest version.
  if (event.request.url.includes('configs.json')) {
    event.respondWith(fetch(event.request));
    return;
  }

  // For other files, use cache-first strategy.
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        return response || fetch(event.request);
      })
  );
});

// Clean up old caches on activation
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

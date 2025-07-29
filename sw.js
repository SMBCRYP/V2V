const CACHE_NAME = 'v2v-cache-v1';
const urlsToCache = [
  '.',
  'index.html',
  'configs.txt',
  'manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          // Return from cache
          return response;
        }
        // Not in cache, fetch from network
        return fetch(event.request).then(
          networkResponse => {
            // Optional: Clone and cache the new response for next time
            if(networkResponse && networkResponse.status === 200) {
              const responseToCache = networkResponse.clone();
              caches.open(CACHE_NAME).then(cache => {
                cache.put(event.request, responseToCache);
              });
            }
            return networkResponse;
          }
        );
      })
  );
});

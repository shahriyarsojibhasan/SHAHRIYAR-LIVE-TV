self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open('shahriyar-tv-cache').then((cache) => cache.addAll([
      './index.html',
      './manifest.json'
    ])),
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((response) => response || fetch(e.request)),
  );
});
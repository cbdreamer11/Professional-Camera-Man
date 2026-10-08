// Minimal service worker: only there so the browser offers "Install app". It caches nothing — live view and the camera API
// must always go straight to the local server.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', () => {});

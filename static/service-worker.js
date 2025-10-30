const CACHE_NAME = 'gasgo-cache-v1';
const urlsToCache = [
  '/',  // homepage
  '/static/css/home.css',
  '/static/css/responsive.css',
  '/static/css/auth.css',
  '/static/css/bot.css',
  '/static/css/contact.css',
  '/static/css/content.css',
  '/static/css/dashboard.css',
  '/static/css/emer.css',
  '/static/css/history.css',
  '/static/css/orders.css',
  '/static/css/profile.css',
  '/static/css/testimonials.css',
  '/static/css/track.css',
  '/static/css/vendor.css',
  '/static/images/logo.png',
  '/static/images/testimonial1.jpg',
  '/static/images/testimonial2.jpg',
  '/static/images/testimonial3.jpg',
  '/static/js/forgot_password.js'
];


self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => response || fetch(event.request))
  );
});

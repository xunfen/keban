const C='keban-student-v1';const U=['/','/setup','/index.html']
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(U)));self.skipWaiting()})
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==C).map(k=>caches.delete(k)))))})
self.addEventListener('fetch',e=>{e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request).catch(()=>new Response('离线中',{status:503}))))})

// Service Worker for PWA
const CACHE_NAME = 'handwrite-v1.0.0';
const urlsToCache = [
  '/',
  '/static/css/app.css',
  '/static/js/app.js',
  '/static/js/chunk-vendors.js',
  '/icon.svg',
  '/favicon.ico',
  '/manifest.json',
  // 添加其他重要资源
  '/default.png',
  '/default1.png',
  '/writing.png'
];

// 安装事件
self.addEventListener('install', (event) => {
  console.log('Service Worker: Install');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Service Worker: Caching files');
        return cache.addAll(urlsToCache);
      })
      .catch((error) => {
        console.log('Service Worker: Cache failed', error);
      })
  );
});

// 激活事件
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activate');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Service Worker: Deleting old cache', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// 拦截请求
self.addEventListener('fetch', (event) => {
  // 过滤掉不支持的请求协议
  if (!event.request.url.startsWith("http")) {
    return;
  }

  // 过滤掉 Chrome 扩展请求
  if (event.request.url.startsWith("chrome-extension://")) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((response) => {
      // 如果缓存中有，返回缓存
      if (response) {
        return response;
      }

      // 否则发起网络请求
      return fetch(event.request)
        .then((response) => {
          // 检查是否是有效响应
          if (
            !response ||
            response.status !== 200 ||
            response.type !== "basic"
          ) {
            return response;
          }

          // 克隆响应
          const responseToCache = response.clone();

          // 添加到缓存（使用 try-catch 避免不支持的请求）
          caches
            .open(CACHE_NAME)
            .then((cache) => {
              try {
                cache.put(event.request, responseToCache);
              } catch (error) {
                console.warn(
                  "Failed to cache request:",
                  event.request.url,
                  error
                );
              }
            })
            .catch((error) => {
              console.warn("Failed to open cache:", error);
            });

          return response;
        })
        .catch(() => {
          // 网络失败时的后备方案
          if (event.request.destination === "document") {
            return caches.match("/");
          }
        });
    })
  );
});

// 推送通知（可选）
self.addEventListener('push', (event) => {
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body,
      icon: '/icon.svg',
      badge: '/icon.svg',
      vibrate: [100, 50, 100],
      data: {
        dateOfArrival: Date.now(),
        primaryKey: 1
      }
    };
    
    event.waitUntil(
      self.registration.showNotification(data.title, options)
    );
  }
});

// 通知点击事件
self.addEventListener('notificationclick', (event) => {
  console.log('Notification click received.');
  event.notification.close();
  
  event.waitUntil(
    clients.openWindow('/')
  );
});

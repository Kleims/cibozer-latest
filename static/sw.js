/**
 * Cibozer Service Worker
 * Provides offline functionality, caching, and background sync
 */

const CACHE_NAME = 'cibozer-v1.0.0';
const STATIC_CACHE = 'cibozer-static-v1.0.0';
const DYNAMIC_CACHE = 'cibozer-dynamic-v1.0.0';
const OFFLINE_PAGE = '/offline.html';

// Files to cache immediately
const STATIC_FILES = [
    '/',
    '/static/css/style.css',
    '/static/css/touch-targets.css',
    '/static/js/cibozer-clean.js',
    '/static/js/error-handling.js',
    '/static/js/keyboard-navigation.js',
    '/static/js/touch-gestures.js',
    '/static/js/performance.js',
    '/static/js/ux-enhancements.js',
    '/auth/login',
    '/offline.html',
    // Bootstrap and Font Awesome will be cached dynamically
];

// API endpoints to cache
const CACHEABLE_APIS = [
    '/api/user/profile',
    '/api/meal-plans',
    '/api/health'
];

// Files that should always be fetched from network
const NETWORK_ONLY = [
    '/api/generate-meal-plan',
    '/api/payment',
    '/admin',
    '/auth/logout'
];

// Install event - cache static files
self.addEventListener('install', (event) => {
    event.waitUntil(
        Promise.all([
            // Cache static files
            caches.open(STATIC_CACHE).then((cache) => {
                return cache.addAll(STATIC_FILES);
            }),
            // Skip waiting to activate immediately
            self.skipWaiting()
        ])
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        Promise.all([
            // Clean up old caches
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== STATIC_CACHE && 
                            cacheName !== DYNAMIC_CACHE && 
                            cacheName !== CACHE_NAME) {
                            return caches.delete(cacheName);
                        }
                    })
                );
            }),
            // Claim all clients
            self.clients.claim()
        ])
    );
});

// Fetch event - handle all network requests
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests and chrome-extension requests
    if (request.method !== 'GET' || url.protocol.startsWith('chrome-extension')) {
        return;
    }
    
    // Handle different types of requests
    if (isStaticAsset(url)) {
        event.respondWith(handleStaticAsset(request));
    } else if (isAPIRequest(url)) {
        event.respondWith(handleAPIRequest(request));
    } else if (isPageRequest(url)) {
        event.respondWith(handlePageRequest(request));
    } else {
        event.respondWith(handleOtherRequest(request));
    }
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync') {
        event.waitUntil(handleBackgroundSync());
    }
});

// Push notifications
self.addEventListener('push', (event) => {
    if (event.data) {
        const data = event.data.json();
        event.waitUntil(
            self.registration.showNotification(data.title, {
                body: data.body,
                icon: '/static/img/icon-192.png',
                badge: '/static/img/badge-72.png',
                data: data.data || {}
            })
        );
    }
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    const urlToOpen = event.notification.data?.url || '/';
    
    event.waitUntil(
        clients.matchAll({ includeUncontrolled: true, type: 'window' })
            .then((clientList) => {
                // Check if app is already open
                for (const client of clientList) {
                    if (client.url === urlToOpen && 'focus' in client) {
                        return client.focus();
                    }
                }
                
                // Open new window if app is not already open
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
    );
});

// Helper functions
function isStaticAsset(url) {
    return url.pathname.startsWith('/static/') ||
           url.pathname.endsWith('.css') ||
           url.pathname.endsWith('.js') ||
           url.pathname.endsWith('.png') ||
           url.pathname.endsWith('.jpg') ||
           url.pathname.endsWith('.svg') ||
           url.pathname.endsWith('.woff') ||
           url.pathname.endsWith('.woff2');
}

function isAPIRequest(url) {
    return url.pathname.startsWith('/api/');
}

function isPageRequest(url) {
    return url.origin === self.location.origin && 
           !url.pathname.startsWith('/static/') &&
           !url.pathname.startsWith('/api/');
}

function isNetworkOnly(url) {
    return NETWORK_ONLY.some(path => url.pathname.startsWith(path));
}

function isCacheableAPI(url) {
    return CACHEABLE_APIs.some(path => url.pathname.startsWith(path));
}

// Static asset handler - cache first with fallback
async function handleStaticAsset(request) {
    try {
        const cache = await caches.open(STATIC_CACHE);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            // Serve from cache and update in background
            updateCacheInBackground(request, cache);
            return cachedResponse;
        }
        
        // Not in cache, fetch and cache
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
        
    } catch (error) {
        // Return fallback for critical assets
        if (request.url.includes('.css')) {
            return new Response('/* Offline fallback styles */', {
                headers: { 'Content-Type': 'text/css' }
            });
        }
        if (request.url.includes('.js')) {
            return new Response('// Offline fallback script', {
                headers: { 'Content-Type': 'application/javascript' }
            });
        }
        
        throw error;
    }
}

// API request handler
async function handleAPIRequest(request) {
    const url = new URL(request.url);
    
    // Network-only endpoints
    if (isNetworkOnly(url)) {
        return fetch(request);
    }
    
    // Cacheable APIs - network first with cache fallback
    if (isCacheableAPI(url)) {
        try {
            const networkResponse = await fetch(request);
            
            if (networkResponse.ok) {
                const cache = await caches.open(DYNAMIC_CACHE);
                cache.put(request, networkResponse.clone());
            }
            
            return networkResponse;
            
        } catch (error) {
            // Fallback to cache
            const cache = await caches.open(DYNAMIC_CACHE);
            const cachedResponse = await cache.match(request);
            
            if (cachedResponse) {
                // Add offline indicator to response
                const response = cachedResponse.clone();
                const data = await response.json();
                data._offline = true;
                data._cached_at = new Date().toISOString();
                
                return new Response(JSON.stringify(data), {
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Offline': 'true'
                    }
                });
            }
            
            // Return offline response
            return new Response(JSON.stringify({
                error: 'Offline',
                message: 'This feature requires an internet connection',
                offline: true
            }), {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
            });
        }
    }
    
    // Other APIs - network only with offline fallback
    try {
        return await fetch(request);
    } catch (error) {
        return new Response(JSON.stringify({
            error: 'Network Error',
            message: 'Unable to connect to server',
            offline: true
        }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// Page request handler
async function handlePageRequest(request) {
    try {
        // Try network first
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            // Cache successful page responses
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
        
    } catch (error) {
        // Try cache
        const cache = await caches.open(DYNAMIC_CACHE);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Fallback to offline page
        const offlineResponse = await cache.match(OFFLINE_PAGE);
        if (offlineResponse) {
            return offlineResponse;
        }
        
        // Ultimate fallback
        return new Response(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Offline - Cibozer</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { 
                        font-family: system-ui, sans-serif; 
                        text-align: center; 
                        padding: 50px 20px;
                        background: #f8f9fa;
                    }
                    .offline-container {
                        max-width: 400px;
                        margin: 0 auto;
                        background: white;
                        padding: 40px 20px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }
                    .offline-icon { font-size: 48px; margin-bottom: 20px; }
                    h1 { color: #2c3e50; margin-bottom: 20px; }
                    p { color: #7f8c8d; margin-bottom: 30px; }
                    .retry-btn {
                        background: #2ecc71;
                        color: white;
                        border: none;
                        padding: 12px 24px;
                        border-radius: 6px;
                        cursor: pointer;
                        font-size: 16px;
                    }
                    .retry-btn:hover { background: #27ae60; }
                </style>
            </head>
            <body>
                <div class="offline-container">
                    <div class="offline-icon">📡</div>
                    <h1>You're Offline</h1>
                    <p>Check your internet connection and try again.</p>
                    <button class="retry-btn" onclick="window.location.reload()">
                        Try Again
                    </button>
                </div>
            </body>
            </html>
        `, {
            status: 503,
            headers: { 'Content-Type': 'text/html' }
        });
    }
}

// Other request handler
async function handleOtherRequest(request) {
    try {
        return await fetch(request);
    } catch (error) {
        // Try cache as fallback
        const cache = await caches.open(DYNAMIC_CACHE);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        throw error;
    }
}

// Background cache update
async function updateCacheInBackground(request, cache) {
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
    } catch (error) {
        // Ignore background update errors
    }
}

// Background sync handler
async function handleBackgroundSync() {
    try {
        // Get pending actions from IndexedDB
        const pendingActions = await getPendingActions();
        
        for (const action of pendingActions) {
            try {
                await executeAction(action);
                await removePendingAction(action.id);
            } catch (error) {
                // Keep action for next sync attempt
                console.error('Background sync failed for action:', action.id);
            }
        }
    } catch (error) {
        console.error('Background sync failed:', error);
    }
}

// IndexedDB helpers for background sync
async function getPendingActions() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('CibozerOffline', 1);
        
        request.onerror = () => reject(request.error);
        
        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction(['pendingActions'], 'readonly');
            const store = transaction.objectStore('pendingActions');
            const getAll = store.getAll();
            
            getAll.onsuccess = () => resolve(getAll.result || []);
            getAll.onerror = () => reject(getAll.error);
        };
        
        request.onupgradeneeded = () => {
            const db = request.result;
            if (!db.objectStoreNames.contains('pendingActions')) {
                const store = db.createObjectStore('pendingActions', { keyPath: 'id' });
                store.createIndex('timestamp', 'timestamp');
            }
        };
    });
}

async function executeAction(action) {
    switch (action.type) {
        case 'like_meal_plan':
            return fetch('/api/meal-plans/like', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ meal_plan_id: action.data.meal_plan_id })
            });
            
        case 'save_preferences':
            return fetch('/api/user/preferences', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(action.data)
            });
            
        default:
            throw new Error(`Unknown action type: ${action.type}`);
    }
}

async function removePendingAction(actionId) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('CibozerOffline', 1);
        
        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction(['pendingActions'], 'readwrite');
            const store = transaction.objectStore('pendingActions');
            const deleteRequest = store.delete(actionId);
            
            deleteRequest.onsuccess = () => resolve();
            deleteRequest.onerror = () => reject(deleteRequest.error);
        };
    });
}

// Cache management
self.addEventListener('message', (event) => {
    if (event.data.action === 'clearCache') {
        event.waitUntil(
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => caches.delete(cacheName))
                );
            })
        );
    }
    
    if (event.data.action === 'getCacheSize') {
        event.waitUntil(
            getCacheSize().then((size) => {
                event.ports[0].postMessage({ cacheSize: size });
            })
        );
    }
});

async function getCacheSize() {
    const cacheNames = await caches.keys();
    let totalSize = 0;
    
    for (const cacheName of cacheNames) {
        const cache = await caches.open(cacheName);
        const requests = await cache.keys();
        
        for (const request of requests) {
            const response = await cache.match(request);
            if (response) {
                const blob = await response.blob();
                totalSize += blob.size;
            }
        }
    }
    
    return totalSize;
}
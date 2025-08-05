/**
 * Performance optimizations for Cibozer
 */

// Lazy loading for images
document.addEventListener('DOMContentLoaded', function() {
    // Intersection Observer for lazy loading
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                observer.unobserve(img);
            }
        });
    });

    // Observe all lazy images
    const lazyImages = document.querySelectorAll('img.lazy');
    lazyImages.forEach(img => imageObserver.observe(img));
});

// Debounce function for scroll/resize events
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Request idle callback polyfill
window.requestIdleCallback = window.requestIdleCallback || function(cb) {
    const start = Date.now();
    return setTimeout(() => {
        cb({
            didTimeout: false,
            timeRemaining: () => Math.max(0, 50 - (Date.now() - start))
        });
    }, 1);
};

// Defer non-critical tasks
function deferTask(task) {
    if ('requestIdleCallback' in window) {
        requestIdleCallback(task, { timeout: 2000 });
    } else {
        setTimeout(task, 0);
    }
}

// Performance monitoring
class PerformanceMonitor {
    constructor() {
        this.metrics = {};
        this.init();
    }

    init() {
        // Monitor page load performance
        window.addEventListener('load', () => {
            if ('performance' in window) {
                const perfData = window.performance.timing;
                const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
                const domReadyTime = perfData.domContentLoadedEventEnd - perfData.navigationStart;
                const resourceLoadTime = perfData.loadEventEnd - perfData.responseEnd;

                this.metrics = {
                    pageLoadTime,
                    domReadyTime,
                    resourceLoadTime
                };

                // Log to console in development
                if (window.location.hostname === 'localhost') {
                    // Performance metrics (debug mode only)
                }

                // Send to analytics in production
                this.sendMetrics();
            }
        });

        // Monitor Core Web Vitals
        this.observeWebVitals();
    }

    observeWebVitals() {
        // Largest Contentful Paint
        new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const lastEntry = entries[entries.length - 1];
            this.metrics.lcp = lastEntry.renderTime || lastEntry.loadTime;
        }).observe({ entryTypes: ['largest-contentful-paint'] });

        // First Input Delay
        new PerformanceObserver((list) => {
            const entries = list.getEntries();
            entries.forEach((entry) => {
                this.metrics.fid = entry.processingStart - entry.startTime;
            });
        }).observe({ entryTypes: ['first-input'] });

        // Cumulative Layout Shift
        let clsValue = 0;
        new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
                if (!entry.hadRecentInput) {
                    clsValue += entry.value;
                }
            }
            this.metrics.cls = clsValue;
        }).observe({ entryTypes: ['layout-shift'] });
    }

    sendMetrics() {
        // Send metrics to analytics endpoint
        if (this.metrics.pageLoadTime > 3000) {
            console.warn('Page load time exceeds 3 seconds:', this.metrics.pageLoadTime);
        }
    }
}

// Initialize performance monitor
const perfMonitor = new PerformanceMonitor();

// Resource hints
function addResourceHints() {
    const head = document.head;
    
    // Preconnect to external domains
    const preconnectDomains = [
        'https://cdn.jsdelivr.net',
        'https://fonts.googleapis.com',
        'https://js.stripe.com'
    ];
    
    preconnectDomains.forEach(domain => {
        const link = document.createElement('link');
        link.rel = 'preconnect';
        link.href = domain;
        head.appendChild(link);
    });
    
    // DNS prefetch
    const dnsPrefetchDomains = [
        'https://www.google-analytics.com',
        'https://api.stripe.com'
    ];
    
    dnsPrefetchDomains.forEach(domain => {
        const link = document.createElement('link');
        link.rel = 'dns-prefetch';
        link.href = domain;
        head.appendChild(link);
    });
}

// Add resource hints
deferTask(addResourceHints);

// Service Worker registration
if ('serviceWorker' in navigator && window.location.protocol === 'https:') {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
            .then(registration => {
                // ServiceWorker registered
            })
            .catch(err => {
                // ServiceWorker registration failed
            });
    });
}

// Memory leak prevention
class MemoryManager {
    constructor() {
        this.listeners = new WeakMap();
        this.timers = new Set();
    }

    addEventListener(element, event, handler) {
        element.addEventListener(event, handler);
        
        if (!this.listeners.has(element)) {
            this.listeners.set(element, []);
        }
        
        this.listeners.get(element).push({ event, handler });
    }

    removeEventListeners(element) {
        const listeners = this.listeners.get(element);
        if (listeners) {
            listeners.forEach(({ event, handler }) => {
                element.removeEventListener(event, handler);
            });
            this.listeners.delete(element);
        }
    }

    setTimeout(callback, delay) {
        const timerId = setTimeout(() => {
            callback();
            this.timers.delete(timerId);
        }, delay);
        
        this.timers.add(timerId);
        return timerId;
    }

    clearAllTimers() {
        this.timers.forEach(timerId => clearTimeout(timerId));
        this.timers.clear();
    }

    cleanup() {
        this.clearAllTimers();
        // Clean up any other resources
    }
}

// Global memory manager
window.memoryManager = new MemoryManager();

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.memoryManager) {
        window.memoryManager.cleanup();
    }
});

// Export for use in other modules
window.CibozerPerformance = {
    debounce,
    deferTask,
    perfMonitor,
    memoryManager
};
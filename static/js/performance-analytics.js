/**
 * Advanced Performance Analytics and Monitoring for Cibozer
 * Tracks real-world performance metrics and user experience
 */

class PerformanceAnalytics {
    constructor() {
        this.metrics = {
            pageLoadTime: 0,
            domContentLoaded: 0,
            firstPaint: 0,
            firstContentfulPaint: 0,
            largestContentfulPaint: 0,
            cumulativeLayoutShift: 0,
            firstInputDelay: 0,
            totalBlockingTime: 0,
            timeToInteractive: 0
        };
        
        this.resources = [];
        this.userTiming = [];
        this.errors = [];
        this.interactions = [];
        
        this.initialized = false;
        this.startTime = performance.now();
        
        this.init();
    }
    
    init() {
        if (this.initialized) return;
        
        // Wait for page to be loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.startTracking());
        } else {
            this.startTracking();
        }
        
        this.initialized = true;
    }
    
    startTracking() {
        // Core Web Vitals tracking
        this.trackCoreWebVitals();
        
        // Navigation timing
        this.trackNavigationTiming();
        
        // Resource timing
        this.trackResourceTiming();
        
        // User interactions
        this.trackUserInteractions();
        
        // Error tracking
        this.trackErrors();
        
        // Custom performance marks
        this.trackCustomMarks();
        
        // Send metrics after page is fully loaded
        window.addEventListener('load', () => {
            setTimeout(() => this.sendMetrics(), 3000); // Wait 3s for everything to settle
        });
    }
    
    trackCoreWebVitals() {
        // First Contentful Paint (FCP)
        if (window.PerformanceObserver && window.PerformancePaintTiming) {
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (entry.name === 'first-paint') {
                        this.metrics.firstPaint = entry.startTime;
                    } else if (entry.name === 'first-contentful-paint') {
                        this.metrics.firstContentfulPaint = entry.startTime;
                        this.markMilestone('FCP', entry.startTime);
                    }
                }
            });
            observer.observe({ entryTypes: ['paint'] });
        }
        
        // Largest Contentful Paint (LCP)
        if (window.PerformanceObserver && window.LargestContentfulPaint) {
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const lastEntry = entries[entries.length - 1];
                this.metrics.largestContentfulPaint = lastEntry.startTime;
                this.markMilestone('LCP', lastEntry.startTime);
            });
            observer.observe({ entryTypes: ['largest-contentful-paint'] });
        }
        
        // Cumulative Layout Shift (CLS)
        if (window.PerformanceLongTaskTiming) {
            let clsValue = 0;
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (!entry.hadRecentInput) {
                        clsValue += entry.value;
                    }
                }
                this.metrics.cumulativeLayoutShift = clsValue;
            });
            observer.observe({ entryTypes: ['layout-shift'] });
        }
        
        // First Input Delay (FID)
        if (window.PerformanceEventTiming) {
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (entry.processingStart && entry.startTime) {
                        this.metrics.firstInputDelay = entry.processingStart - entry.startTime;
                        this.markMilestone('FID', this.metrics.firstInputDelay);
                        observer.disconnect();
                        break;
                    }
                }
            });
            observer.observe({ entryTypes: ['first-input'] });
        }
        
        // Total Blocking Time (TBT)
        if (window.PerformanceLongTaskTiming) {
            let totalBlockingTime = 0;
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (entry.duration > 50) {
                        totalBlockingTime += entry.duration - 50;
                    }
                }
                this.metrics.totalBlockingTime = totalBlockingTime;
            });
            observer.observe({ entryTypes: ['longtask'] });
        }
    }
    
    trackNavigationTiming() {
        window.addEventListener('load', () => {
            const navigation = performance.getEntriesByType('navigation')[0];
            
            if (navigation) {
                this.metrics.pageLoadTime = navigation.loadEventEnd - navigation.fetchStart;
                this.metrics.domContentLoaded = navigation.domContentLoadedEventEnd - navigation.fetchStart;
                this.metrics.timeToInteractive = this.estimateTimeToInteractive(navigation);
                
                // Detailed timing breakdown
                this.navigationDetails = {
                    dnsLookup: navigation.domainLookupEnd - navigation.domainLookupStart,
                    tcpConnect: navigation.connectEnd - navigation.connectStart,
                    tlsHandshake: navigation.secureConnectionStart > 0 ? 
                        navigation.connectEnd - navigation.secureConnectionStart : 0,
                    request: navigation.responseStart - navigation.requestStart,
                    response: navigation.responseEnd - navigation.responseStart,
                    domProcessing: navigation.domContentLoadedEventStart - navigation.responseEnd,
                    domComplete: navigation.domComplete - navigation.domContentLoadedEventStart
                };
            }
        });
    }
    
    estimateTimeToInteractive(navigation) {
        // Simplified TTI estimation
        const domInteractive = navigation.domInteractive - navigation.fetchStart;
        const loadEvent = navigation.loadEventStart - navigation.fetchStart;
        
        // TTI is typically after DOM interactive but before load
        return domInteractive + ((loadEvent - domInteractive) * 0.7);
    }
    
    trackResourceTiming() {
        window.addEventListener('load', () => {
            const resources = performance.getEntriesByType('resource');
            
            this.resources = resources.map(resource => ({
                name: resource.name,
                type: this.getResourceType(resource.name),
                size: resource.transferSize || 0,
                duration: resource.duration,
                startTime: resource.startTime,
                cached: resource.transferSize === 0 && resource.decodedBodySize > 0
            }));
            
            // Analyze resource loading
            this.analyzeResourcePerformance();
        });
    }
    
    getResourceType(url) {
        if (url.includes('.js')) return 'script';
        if (url.includes('.css')) return 'stylesheet';
        if (url.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i)) return 'image';
        if (url.includes('fonts.') || url.match(/\.(woff|woff2|ttf|eot)$/i)) return 'font';
        return 'other';
    }
    
    analyzeResourcePerformance() {
        const analysis = {
            totalSize: 0,
            totalRequests: this.resources.length,
            byType: {},
            slowResources: [],
            largeResources: []
        };
        
        for (const resource of this.resources) {
            analysis.totalSize += resource.size;
            
            if (!analysis.byType[resource.type]) {
                analysis.byType[resource.type] = { count: 0, size: 0 };
            }
            analysis.byType[resource.type].count++;
            analysis.byType[resource.type].size += resource.size;
            
            // Flag slow resources (>2s)
            if (resource.duration > 2000) {
                analysis.slowResources.push({
                    name: resource.name,
                    duration: resource.duration
                });
            }
            
            // Flag large resources (>500KB)
            if (resource.size > 500 * 1024) {
                analysis.largeResources.push({
                    name: resource.name,
                    size: resource.size
                });
            }
        }
        
        this.resourceAnalysis = analysis;
    }
    
    trackUserInteractions() {
        // Track clicks with timing
        document.addEventListener('click', (event) => {
            this.trackInteraction('click', event.target, performance.now());
        });
        
        // Track form submissions
        document.addEventListener('submit', (event) => {
            this.trackInteraction('submit', event.target, performance.now());
        });
        
        // Track keyboard interactions
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
                this.trackInteraction('keyboard', event.target, performance.now());
            }
        });
    }
    
    trackInteraction(type, element, timestamp) {
        const interaction = {
            type,
            element: element.tagName.toLowerCase(),
            className: element.className,
            id: element.id,
            timestamp: timestamp - this.startTime,
            url: window.location.pathname
        };
        
        this.interactions.push(interaction);
        
        // Keep only last 50 interactions
        if (this.interactions.length > 50) {
            this.interactions = this.interactions.slice(-50);
        }
    }
    
    trackErrors() {
        // JavaScript errors
        window.addEventListener('error', (event) => {
            this.errors.push({
                type: 'javascript',
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                timestamp: performance.now() - this.startTime
            });
        });
        
        // Promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.errors.push({
                type: 'promise',
                message: event.reason?.toString() || 'Unhandled promise rejection',
                timestamp: performance.now() - this.startTime
            });
        });
        
        // Resource loading errors
        document.addEventListener('error', (event) => {
            if (event.target !== window) {
                this.errors.push({
                    type: 'resource',
                    element: event.target.tagName,
                    source: event.target.src || event.target.href,
                    timestamp: performance.now() - this.startTime
                });
            }
        }, true);
    }
    
    trackCustomMarks() {
        // Track custom performance marks
        if (window.performance && window.performance.getEntriesByType) {
            window.addEventListener('load', () => {
                setTimeout(() => {
                    const marks = performance.getEntriesByType('mark');
                    const measures = performance.getEntriesByType('measure');
                    
                    this.userTiming = [...marks, ...measures].map(entry => ({
                        name: entry.name,
                        type: entry.entryType,
                        startTime: entry.startTime,
                        duration: entry.duration || 0
                    }));
                }, 1000);
            });
        }
    }
    
    markMilestone(name, value) {
        // Custom milestone tracking
        if (window.performance && window.performance.mark) {
            performance.mark(`milestone-${name}`);
        }
        
        // Log milestone for debugging
        if (window.location.hostname === 'localhost') {
            console.log(`🎯 Performance Milestone: ${name} = ${value.toFixed(2)}ms`);
        }
    }
    
    measureUserEngagement() {
        const engagement = {
            timeOnPage: performance.now() - this.startTime,
            interactions: this.interactions.length,
            scrollDepth: this.getScrollDepth(),
            visibilityChanges: this.visibilityChanges || 0
        };
        
        // Track visibility changes
        if (!this.visibilityTracking) {
            this.visibilityChanges = 0;
            document.addEventListener('visibilitychange', () => {
                this.visibilityChanges++;
            });
            this.visibilityTracking = true;
        }
        
        return engagement;
    }
    
    getScrollDepth() {
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight;
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        return Math.round(((scrollTop + windowHeight) / documentHeight) * 100);
    }
    
    getPerformanceScore() {
        // Calculate a simplified performance score
        let score = 100;
        
        // Deduct points for slow metrics
        if (this.metrics.firstContentfulPaint > 2500) score -= 10;
        if (this.metrics.largestContentfulPaint > 4000) score -= 15;
        if (this.metrics.firstInputDelay > 300) score -= 10;
        if (this.metrics.cumulativeLayoutShift > 0.25) score -= 10;
        if (this.metrics.pageLoadTime > 5000) score -= 15;
        
        // Deduct points for errors
        score -= this.errors.length * 5;
        
        // Deduct points for large resources
        if (this.resourceAnalysis?.totalSize > 2 * 1024 * 1024) score -= 10; // 2MB
        
        return Math.max(0, score);
    }
    
    async sendMetrics() {
        const performanceData = {
            url: window.location.href,
            userAgent: navigator.userAgent,
            timestamp: new Date().toISOString(),
            metrics: this.metrics,
            navigationDetails: this.navigationDetails,
            resources: this.resourceAnalysis,
            userTiming: this.userTiming,
            errors: this.errors,
            interactions: this.interactions.slice(-10), // Last 10 interactions
            engagement: this.measureUserEngagement(),
            performanceScore: this.getPerformanceScore(),
            connection: this.getConnectionInfo(),
            deviceInfo: this.getDeviceInfo()
        };
        
        try {
            // Send to performance monitoring endpoint
            if (window.apiClient) {
                await window.apiClient.post('/api/performance/metrics', performanceData);
            } else {
                // Fallback to fetch
                await fetch('/api/performance/metrics', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(performanceData)
                });
            }
            
            if (window.location.hostname === 'localhost') {
                console.log('📊 Performance metrics sent:', {
                    score: performanceData.performanceScore,
                    fcp: this.metrics.firstContentfulPaint.toFixed(0) + 'ms',
                    lcp: this.metrics.largestContentfulPaint.toFixed(0) + 'ms',
                    cls: this.metrics.cumulativeLayoutShift.toFixed(3),
                    fid: this.metrics.firstInputDelay.toFixed(0) + 'ms'
                });
            }
            
        } catch (error) {
            // Silently fail - don't interrupt user experience
            if (window.location.hostname === 'localhost') {
                console.warn('Failed to send performance metrics:', error);
            }
        }
    }
    
    getConnectionInfo() {
        if (navigator.connection) {
            return {
                effectiveType: navigator.connection.effectiveType,
                downlink: navigator.connection.downlink,
                rtt: navigator.connection.rtt,
                saveData: navigator.connection.saveData
            };
        }
        return null;
    }
    
    getDeviceInfo() {
        return {
            screenWidth: screen.width,
            screenHeight: screen.height,
            viewportWidth: window.innerWidth,
            viewportHeight: window.innerHeight,
            devicePixelRatio: window.devicePixelRatio,
            hardwareConcurrency: navigator.hardwareConcurrency,
            memory: navigator.deviceMemory
        };
    }
    
    // Public API for manual tracking
    mark(name) {
        if (window.performance && window.performance.mark) {
            performance.mark(name);
        }
    }
    
    measure(name, startMark, endMark) {
        if (window.performance && window.performance.measure) {
            performance.measure(name, startMark, endMark);
        }
    }
    
    // Get current metrics for debugging
    getMetrics() {
        return {
            ...this.metrics,
            performanceScore: this.getPerformanceScore(),
            resourceAnalysis: this.resourceAnalysis,
            errors: this.errors.length
        };
    }
}

// Initialize performance analytics
const performanceAnalytics = new PerformanceAnalytics();

// Export for use in other scripts
window.PerformanceAnalytics = performanceAnalytics;

// Add to global Cibozer object
if (window.CibozerClean) {
    window.CibozerClean.performance = performanceAnalytics;
}

// Expose methods for manual tracking
window.perfMark = (name) => performanceAnalytics.mark(name);
window.perfMeasure = (name, start, end) => performanceAnalytics.measure(name, start, end);
window.perfMetrics = () => performanceAnalytics.getMetrics();
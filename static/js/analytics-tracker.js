/**
 * User Behavior Analytics Tracker for Cibozer
 * Tracks user interactions and sends analytics data
 */

class AnalyticsTracker {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.userId = this.getUserId();
        this.events = [];
        this.batchSize = 10;
        this.flushInterval = 30000; // 30 seconds
        this.endpoint = '/api/analytics/track';
        
        this.init();
    }
    
    init() {
        // Setup event listeners
        this.setupClickTracking();
        this.setupFormTracking();
        this.setupScrollTracking();
        this.setupTimeTracking();
        this.setupErrorTracking();
        this.setupPerformanceTracking();
        
        // Start session
        this.trackEvent('session_start', {
            user_agent: navigator.userAgent,
            screen_resolution: `${screen.width}x${screen.height}`,
            viewport_size: `${window.innerWidth}x${window.innerHeight}`,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            language: navigator.language
        });
        
        // Setup periodic flushing
        setInterval(() => this.flush(), this.flushInterval);
        
        // Flush on page unload
        window.addEventListener('beforeunload', () => this.flush(true));
        window.addEventListener('pagehide', () => this.flush(true));
    }
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    getUserId() {
        // Try to get user ID from various sources
        const metaTag = document.querySelector('meta[name="user-id"]');
        if (metaTag) return metaTag.content;
        
        // Check if user data is available globally
        if (window.currentUser && window.currentUser.id) {
            return window.currentUser.id;
        }
        
        // Generate anonymous user ID
        let anonymousId = localStorage.getItem('cibozer_anonymous_id');
        if (!anonymousId) {
            anonymousId = 'anon_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('cibozer_anonymous_id', anonymousId);
        }
        return anonymousId;
    }
    
    trackEvent(eventName, properties = {}, immediate = false) {
        const event = {
            event: eventName,
            properties: {
                ...properties,
                timestamp: new Date().toISOString(),
                session_id: this.sessionId,
                user_id: this.userId,
                page_url: window.location.href,
                page_title: document.title,
                referrer: document.referrer
            }
        };
        
        this.events.push(event);
        
        // Flush immediately if requested or batch is full
        if (immediate || this.events.length >= this.batchSize) {
            this.flush();
        }
    }
    
    async flush(synchronous = false) {
        if (this.events.length === 0) return;
        
        const eventsToSend = [...this.events];
        this.events = [];
        
        const payload = {
            events: eventsToSend,
            session_id: this.sessionId,
            user_id: this.userId
        };
        
        try {
            if (synchronous && navigator.sendBeacon) {
                // Use sendBeacon for synchronous requests (page unload)
                navigator.sendBeacon(this.endpoint, JSON.stringify(payload));
            } else {
                // Regular fetch request
                await fetch(this.endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload)
                });
            }
        } catch (error) {
            console.error('Analytics tracking error:', error);
            // Put events back if sending failed
            this.events.unshift(...eventsToSend);
        }
    }
    
    setupClickTracking() {
        document.addEventListener('click', (e) => {
            const element = e.target;
            const properties = {
                element_type: element.tagName.toLowerCase(),
                element_id: element.id || null,
                element_class: element.className || null,
                element_text: element.textContent?.trim().substring(0, 100) || null
            };
            
            // Track specific elements
            if (element.matches('button, .btn')) {
                this.trackEvent('button_click', {
                    ...properties,
                    button_type: element.type || 'button',
                    form_id: element.form?.id || null
                });
            } else if (element.matches('a')) {
                this.trackEvent('link_click', {
                    ...properties,
                    href: element.href,
                    is_external: !element.href.includes(window.location.origin)
                });
            } else if (element.matches('[data-track]')) {
                // Custom tracked elements
                this.trackEvent(element.dataset.track, {
                    ...properties,
                    custom_data: element.dataset.trackData ? JSON.parse(element.dataset.trackData) : null
                });
            }
        });
    }
    
    setupFormTracking() {
        // Track form submissions
        document.addEventListener('submit', (e) => {
            const form = e.target;
            const formData = new FormData(form);
            const fields = {};
            
            // Collect field names (not values for privacy)
            for (let [key] of formData.entries()) {
                fields[key] = 'field_present';
            }
            
            this.trackEvent('form_submit', {
                form_id: form.id || null,
                form_action: form.action || null,
                form_method: form.method || 'get',
                field_count: Object.keys(fields).length,
                fields: fields
            });
        });
        
        // Track form field interactions
        document.addEventListener('focus', (e) => {
            if (e.target.matches('input, textarea, select')) {
                this.trackEvent('form_field_focus', {
                    field_name: e.target.name || null,
                    field_type: e.target.type || 'text',
                    form_id: e.target.form?.id || null
                });
            }
        });
        
        // Track form abandonment
        let formInteractions = new Map();
        
        document.addEventListener('input', (e) => {
            if (e.target.matches('input, textarea, select')) {
                const formId = e.target.form?.id || 'unknown';
                formInteractions.set(formId, Date.now());
            }
        });
        
        window.addEventListener('beforeunload', () => {
            formInteractions.forEach((lastInteraction, formId) => {
                const form = document.getElementById(formId);
                if (form && !form.dataset.submitted) {
                    this.trackEvent('form_abandon', {
                        form_id: formId,
                        interaction_duration: Date.now() - lastInteraction
                    });
                }
            });
        });
    }
    
    setupScrollTracking() {
        let maxScroll = 0;
        let scrollMilestones = [25, 50, 75, 90, 100];
        let trackedMilestones = new Set();
        
        const trackScroll = () => {
            const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
            const scrollTop = window.pageYOffset;
            const scrollPercent = Math.round((scrollTop / scrollHeight) * 100);
            
            maxScroll = Math.max(maxScroll, scrollPercent);
            
            // Track milestone scrolling
            scrollMilestones.forEach(milestone => {
                if (scrollPercent >= milestone && !trackedMilestones.has(milestone)) {
                    trackedMilestones.add(milestone);
                    this.trackEvent('scroll_milestone', {
                        milestone: milestone,
                        scroll_depth: scrollPercent
                    });
                }
            });
        };
        
        let scrollTimeout;
        window.addEventListener('scroll', () => {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(trackScroll, 100);
        });
        
        // Track final scroll depth on page unload
        window.addEventListener('beforeunload', () => {
            this.trackEvent('page_scroll_complete', {
                max_scroll_depth: maxScroll
            });
        });
    }
    
    setupTimeTracking() {
        const startTime = Date.now();
        let lastActiveTime = startTime;
        let totalActiveTime = 0;
        
        // Track user activity
        const updateActiveTime = () => {
            const now = Date.now();
            if (now - lastActiveTime < 30000) { // 30 seconds max gap
                totalActiveTime += now - lastActiveTime;
            }
            lastActiveTime = now;
        };
        
        ['click', 'scroll', 'keypress', 'mousemove'].forEach(event => {
            document.addEventListener(event, updateActiveTime, { passive: true });
        });
        
        // Track page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.trackEvent('page_hidden', {
                    time_on_page: Date.now() - startTime,
                    active_time: totalActiveTime
                });
            } else {
                this.trackEvent('page_visible');
                lastActiveTime = Date.now();
            }
        });
        
        // Track session duration on unload
        window.addEventListener('beforeunload', () => {
            updateActiveTime();
            this.trackEvent('session_end', {
                session_duration: Date.now() - startTime,
                active_time: totalActiveTime
            });
        });
    }
    
    setupErrorTracking() {
        // Track JavaScript errors
        window.addEventListener('error', (e) => {
            this.trackEvent('javascript_error', {
                error_message: e.message,
                error_filename: e.filename,
                error_line: e.lineno,
                error_column: e.colno,
                stack_trace: e.error?.stack?.substring(0, 500) || null
            }, true); // Send immediately
        });
        
        // Track unhandled promise rejections
        window.addEventListener('unhandledrejection', (e) => {
            this.trackEvent('promise_rejection', {
                error_reason: e.reason?.toString()?.substring(0, 500) || 'Unknown'
            }, true);
        });
    }
    
    setupPerformanceTracking() {
        // Track page load performance
        window.addEventListener('load', () => {
            setTimeout(() => {
                const perfData = performance.getEntriesByType('navigation')[0];
                if (perfData) {
                    this.trackEvent('page_performance', {
                        load_time: Math.round(perfData.loadEventEnd - perfData.fetchStart),
                        dom_ready: Math.round(perfData.domContentLoadedEventEnd - perfData.fetchStart),
                        first_byte: Math.round(perfData.responseStart - perfData.fetchStart),
                        dns_lookup: Math.round(perfData.domainLookupEnd - perfData.domainLookupStart),
                        connection_time: Math.round(perfData.connectEnd - perfData.connectStart)
                    });
                }
                
                // Track Core Web Vitals if available
                if ('web-vital' in window) {
                    this.trackWebVitals();
                }
            }, 0);
        });
    }
    
    trackWebVitals() {
        // Track First Contentful Paint
        if (window.PerformanceObserver) {
            new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (entry.name === 'first-contentful-paint') {
                        this.trackEvent('web_vital_fcp', {
                            value: Math.round(entry.startTime)
                        });
                    }
                }
            }).observe({ entryTypes: ['paint'] });
            
            // Track Largest Contentful Paint
            new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const lastEntry = entries[entries.length - 1];
                this.trackEvent('web_vital_lcp', {
                    value: Math.round(lastEntry.startTime)
                });
            }).observe({ entryTypes: ['largest-contentful-paint'] });
            
            // Track First Input Delay
            new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    this.trackEvent('web_vital_fid', {
                        value: Math.round(entry.processingStart - entry.startTime)
                    });
                }
            }).observe({ entryTypes: ['first-input'] });
        }
    }
    
    // Public API methods
    identify(userId, traits = {}) {
        this.userId = userId;
        this.trackEvent('user_identify', {
            user_traits: traits
        });
    }
    
    track(eventName, properties = {}) {
        this.trackEvent(eventName, properties);
    }
    
    page(pageName = null, properties = {}) {
        this.trackEvent('page_view', {
            page_name: pageName || document.title,
            ...properties
        });
    }
    
    // Meal plan specific tracking
    trackMealPlanGeneration(data) {
        this.trackEvent('meal_plan_generate', {
            calories: data.calories,
            diet_type: data.diet_type,
            meal_count: data.meals,
            has_preferences: data.preferences && data.preferences.length > 0,
            preference_count: data.preferences ? data.preferences.length : 0
        });
    }
    
    trackMealPlanSave(planId) {
        this.trackEvent('meal_plan_save', {
            plan_id: planId
        });
    }
    
    trackMealPlanShare(planId, method) {
        this.trackEvent('meal_plan_share', {
            plan_id: planId,
            share_method: method
        });
    }
    
    trackPaymentEvent(eventType, data = {}) {
        this.trackEvent(`payment_${eventType}`, data);
    }
}

// Initialize analytics tracker
window.analytics = new AnalyticsTracker();

// Expose public methods globally
window.trackEvent = (eventName, properties) => window.analytics.track(eventName, properties);
window.identifyUser = (userId, traits) => window.analytics.identify(userId, traits);
window.trackPage = (pageName, properties) => window.analytics.page(pageName, properties);

// Track initial page view
window.analytics.page();

// Add data attributes for easy tracking
document.addEventListener('DOMContentLoaded', () => {
    // Auto-track elements with data-track attributes
    document.querySelectorAll('[data-auto-track]').forEach(element => {
        const eventName = element.dataset.autoTrack;
        const eventData = element.dataset.trackData ? JSON.parse(element.dataset.trackData) : {};
        
        element.addEventListener('click', () => {
            window.analytics.track(eventName, eventData);
        });
    });
});
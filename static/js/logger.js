/**
 * Cibozer Frontend Logger
 * Comprehensive logging system with real-time sync to backend
 */

class CibozerLogger {
    constructor() {
        this.logs = [];
        this.maxLogs = 1000;
        this.syncInterval = 5000; // 5 seconds
        this.syncEndpoint = '/api/logs/sync';
        this.logLevels = {
            DEBUG: 0,
            INFO: 1,
            WARN: 2,
            ERROR: 3
        };
        this.currentLevel = this.logLevels.DEBUG;
        this.sessionId = this.generateSessionId();
        
        // Start sync timer
        this.startSync();
        
        // Override console methods
        this.overrideConsole();
        
        // Log initialization
        this.info('Logger initialized', { sessionId: this.sessionId });
    }
    
    generateSessionId() {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    overrideConsole() {
        const originalConsole = {
            log: console.log,
            info: console.info,
            warn: console.warn,
            error: console.error,
            debug: console.debug
        };
        
        console.log = (...args) => {
            originalConsole.log(...args);
            this.log('INFO', args);
        };
        
        console.info = (...args) => {
            originalConsole.info(...args);
            this.info(...args);
        };
        
        console.warn = (...args) => {
            originalConsole.warn(...args);
            this.warn(...args);
        };
        
        console.error = (...args) => {
            originalConsole.error(...args);
            this.error(...args);
        };
        
        console.debug = (...args) => {
            originalConsole.debug(...args);
            this.debug(...args);
        };
    }
    
    log(level, ...args) {
        const logEntry = {
            level,
            timestamp: new Date().toISOString(),
            sessionId: this.sessionId,
            url: window.location.href,
            userAgent: navigator.userAgent,
            message: args.map(arg => {
                if (typeof arg === 'object') {
                    try {
                        return JSON.stringify(arg, null, 2);
                    } catch (e) {
                        return String(arg);
                    }
                }
                return String(arg);
            }).join(' ')
        };
        
        // Add stack trace for errors
        if (level === 'ERROR') {
            logEntry.stack = new Error().stack;
        }
        
        this.logs.push(logEntry);
        
        // Trim logs if too many
        if (this.logs.length > this.maxLogs) {
            this.logs = this.logs.slice(-this.maxLogs);
        }
        
        // Log to localStorage for persistence
        this.saveToLocalStorage();
    }
    
    debug(...args) {
        if (this.currentLevel <= this.logLevels.DEBUG) {
            this.log('DEBUG', ...args);
        }
    }
    
    info(...args) {
        if (this.currentLevel <= this.logLevels.INFO) {
            this.log('INFO', ...args);
        }
    }
    
    warn(...args) {
        if (this.currentLevel <= this.logLevels.WARN) {
            this.log('WARN', ...args);
        }
    }
    
    error(...args) {
        if (this.currentLevel <= this.logLevels.ERROR) {
            this.log('ERROR', ...args);
        }
    }
    
    saveToLocalStorage() {
        try {
            localStorage.setItem('cibozer_logs', JSON.stringify({
                sessionId: this.sessionId,
                logs: this.logs.slice(-100) // Keep last 100 in localStorage
            }));
        } catch (e) {
            // Ignore localStorage errors
        }
    }
    
    loadFromLocalStorage() {
        try {
            const stored = localStorage.getItem('cibozer_logs');
            if (stored) {
                const data = JSON.parse(stored);
                if (data.sessionId === this.sessionId) {
                    this.logs = [...data.logs, ...this.logs];
                }
            }
        } catch (e) {
            // Ignore localStorage errors
        }
    }
    
    async syncToBackend() {
        if (this.logs.length === 0) return;
        
        const logsToSync = [...this.logs];
        this.logs = []; // Clear after copying
        
        try {
            const response = await fetch(this.syncEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': this.getCSRFToken()
                },
                body: JSON.stringify({
                    sessionId: this.sessionId,
                    logs: logsToSync
                })
            });
            
            if (!response.ok) {
                // Re-add logs if sync failed
                this.logs = [...logsToSync, ...this.logs];
                this.warn('Failed to sync logs to backend', response.status);
            }
        } catch (error) {
            // Re-add logs if sync failed
            this.logs = [...logsToSync, ...this.logs];
            this.warn('Error syncing logs', error);
        }
    }
    
    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.content : '';
    }
    
    startSync() {
        // Initial load from localStorage
        this.loadFromLocalStorage();
        
        // Set up periodic sync
        setInterval(() => {
            this.syncToBackend();
        }, this.syncInterval);
        
        // Sync on page unload
        window.addEventListener('beforeunload', () => {
            this.syncToBackend();
        });
    }
    
    // API Request Logger
    logAPIRequest(url, options = {}) {
        const requestId = Math.random().toString(36).substr(2, 9);
        this.info('API Request', {
            requestId,
            url,
            method: options.method || 'GET',
            headers: options.headers,
            body: options.body
        });
        return requestId;
    }
    
    logAPIResponse(requestId, response, data) {
        this.info('API Response', {
            requestId,
            status: response.status,
            statusText: response.statusText,
            headers: Object.fromEntries(response.headers.entries()),
            data: data
        });
    }
    
    logAPIError(requestId, error) {
        this.error('API Error', {
            requestId,
            error: error.message,
            stack: error.stack
        });
    }
    
    // Enhanced fetch wrapper
    async fetchWithLogging(url, options = {}) {
        const requestId = this.logAPIRequest(url, options);
        
        try {
            const response = await fetch(url, options);
            const contentType = response.headers.get('content-type');
            
            if (contentType && contentType.includes('application/json')) {
                const data = await response.json();
                this.logAPIResponse(requestId, response, data);
                
                // Re-create response with cloned data
                return {
                    ...response,
                    json: async () => data,
                    ok: response.ok,
                    status: response.status,
                    statusText: response.statusText
                };
            } else {
                const text = await response.text();
                this.logAPIResponse(requestId, response, { text });
                
                // Log HTML responses as potential errors
                if (contentType && contentType.includes('text/html')) {
                    this.error('Received HTML instead of JSON', {
                        requestId,
                        url,
                        html: text.substring(0, 500)
                    });
                }
                
                return {
                    ...response,
                    text: async () => text,
                    json: async () => {
                        throw new Error(`Expected JSON but received ${contentType}`);
                    },
                    ok: response.ok,
                    status: response.status,
                    statusText: response.statusText
                };
            }
        } catch (error) {
            this.logAPIError(requestId, error);
            throw error;
        }
    }
    
    // Get logs for display
    getLogs(level = null) {
        if (level) {
            return this.logs.filter(log => log.level === level);
        }
        return this.logs;
    }
    
    // Clear logs
    clearLogs() {
        this.logs = [];
        this.saveToLocalStorage();
        this.info('Logs cleared');
    }
}

// Initialize logger
window.CibozerLogger = new CibozerLogger();

// Replace global fetch with logged version
window.originalFetch = window.fetch;
window.fetch = function(...args) {
    return window.CibozerLogger.fetchWithLogging(...args);
};

// Log page load
window.CibozerLogger.info('Page loaded', {
    title: document.title,
    referrer: document.referrer,
    timestamp: new Date().toISOString()
});

// Log errors
window.addEventListener('error', (event) => {
    window.CibozerLogger.error('Uncaught error', {
        message: event.message,
        filename: event.filename,
        line: event.lineno,
        column: event.colno,
        error: event.error ? event.error.stack : 'No stack trace'
    });
});

// Log unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
    window.CibozerLogger.error('Unhandled promise rejection', {
        reason: event.reason,
        promise: event.promise
    });
});
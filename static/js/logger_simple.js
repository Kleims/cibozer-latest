/**
 * Simplified Cibozer Logger
 * Basic logging without backend sync to prevent freezing
 */

class SimpleCibozerLogger {
    constructor() {
        this.logs = [];
        this.maxLogs = 100;
        
        // Override console methods
        this.overrideConsole();
        
        console.log('Simple logger initialized');
    }
    
    overrideConsole() {
        const originalConsole = {
            log: console.log,
            info: console.info,
            warn: console.warn,
            error: console.error
        };
        
        // Store references to original methods
        window.originalConsole = originalConsole;
    }
    
    log(level, ...args) {
        const logEntry = {
            level,
            timestamp: new Date().toISOString(),
            message: args.map(arg => {
                if (typeof arg === 'object') {
                    try {
                        return JSON.stringify(arg);
                    } catch (e) {
                        return String(arg);
                    }
                }
                return String(arg);
            }).join(' ')
        };
        
        this.logs.push(logEntry);
        
        // Keep only recent logs
        if (this.logs.length > this.maxLogs) {
            this.logs = this.logs.slice(-this.maxLogs);
        }
    }
}

// Initialize simple logger
window.CibozerLogger = new SimpleCibozerLogger();

// Log page load
console.log('Page loaded:', document.title);

// Log errors
window.addEventListener('error', (event) => {
    console.error('JavaScript error:', event.message, 'at', event.filename, ':', event.lineno);
});

// Log unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
});
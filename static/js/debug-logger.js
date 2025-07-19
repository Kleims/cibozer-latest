// Debug Logger - Saves all console logs to server
(function() {
    const logs = [];
    const originalLog = console.log;
    const originalError = console.error;
    const originalWarn = console.warn;
    
    // Override console methods
    console.log = function(...args) {
        logs.push({
            type: 'log',
            timestamp: new Date().toISOString(),
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
        });
        originalLog.apply(console, args);
    };
    
    console.error = function(...args) {
        logs.push({
            type: 'error',
            timestamp: new Date().toISOString(),
            message: args.map(arg => String(arg)).join(' ')
        });
        originalError.apply(console, args);
    };
    
    console.warn = function(...args) {
        logs.push({
            type: 'warn',
            timestamp: new Date().toISOString(),
            message: args.map(arg => String(arg)).join(' ')
        });
        originalWarn.apply(console, args);
    };
    
    // Send logs to server every 2 seconds
    setInterval(() => {
        if (logs.length > 0) {
            const logsToSend = [...logs];
            logs.length = 0; // Clear array
            
            fetch('/api/debug-logs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ logs: logsToSend })
            }).catch(err => {
                originalError('Failed to send debug logs:', err);
            });
        }
    }, 2000);
    
    // Also send on page unload
    window.addEventListener('beforeunload', () => {
        if (logs.length > 0) {
            navigator.sendBeacon('/api/debug-logs', JSON.stringify({ logs }));
        }
    });
    
    console.log('🔍 Debug logger initialized - all console output will be saved to server');
})();
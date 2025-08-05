/**
 * Comprehensive Error Handling Utilities for Cibozer
 * Ensures all async operations have proper error handling
 */

class ErrorHandler {
    constructor() {
        this.setupGlobalErrorHandlers();
        this.setupPromiseRejectionHandlers();
        this.setupAsyncWrappers();
    }
    
    setupGlobalErrorHandlers() {
        // Catch all uncaught JavaScript errors
        window.addEventListener('error', (event) => {
            this.logError('JavaScript Error', {
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                stack: event.error?.stack
            });
            
            // Show user-friendly message for critical errors
            if (this.isCriticalError(event.error)) {
                this.showErrorToUser('Something went wrong. Please refresh the page.');
            }
            
            // Prevent default browser error handling for custom errors
            if (event.error?.name === 'CibozerError') {
                event.preventDefault();
            }
        });
        
        // Catch unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.logError('Unhandled Promise Rejection', {
                reason: event.reason,
                promise: event.promise,
                stack: event.reason?.stack
            });
            
            // Show user-friendly message
            this.showErrorToUser('An unexpected error occurred. Please try again.');
            
            // Prevent default browser handling
            event.preventDefault();
        });
    }
    
    setupPromiseRejectionHandlers() {
        // Catch handled promise rejections that might not have proper error handling
        const originalThen = Promise.prototype.then;
        const originalCatch = Promise.prototype.catch;
        
        Promise.prototype.then = function(onFulfilled, onRejected) {
            // Ensure all promises have error handling
            const wrappedOnRejected = onRejected || ((error) => {
                window.errorHandler?.logError('Promise Rejection in then()', { error });
                throw error;
            });
            
            return originalThen.call(this, onFulfilled, wrappedOnRejected);
        };
        
        Promise.prototype.catch = function(onRejected) {
            const wrappedOnRejected = (error) => {
                window.errorHandler?.logError('Promise Rejection in catch()', { error });
                if (onRejected) {
                    return onRejected(error);
                }
                throw error;
            };
            
            return originalCatch.call(this, wrappedOnRejected);
        };
    }
    
    setupAsyncWrappers() {
        // Wrap common async operations with error handling
        
        // Fetch wrapper
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            try {
                const response = await originalFetch(...args);
                
                // Log failed requests
                if (!response.ok) {
                    this.logError('HTTP Request Failed', {
                        url: args[0],
                        status: response.status,
                        statusText: response.statusText
                    });
                }
                
                return response;
            } catch (error) {
                this.logError('Fetch Error', {
                    url: args[0],
                    error: error.message,
                    stack: error.stack
                });
                throw error;
            }
        };
        
        // Wrap setTimeout for async error handling
        const originalSetTimeout = window.setTimeout;
        window.setTimeout = (callback, delay, ...args) => {
            const wrappedCallback = (...callbackArgs) => {
                try {
                    return callback(...callbackArgs);
                } catch (error) {
                    this.logError('SetTimeout Callback Error', { error });
                    throw error;
                }
            };
            
            return originalSetTimeout(wrappedCallback, delay, ...args);
        };
        
        // Wrap event listeners for async operations
        const originalAddEventListener = EventTarget.prototype.addEventListener;
        EventTarget.prototype.addEventListener = function(type, listener, options) {
            const wrappedListener = async (event) => {
                try {
                    if (listener.constructor.name === 'AsyncFunction') {
                        await listener.call(this, event);
                    } else {
                        listener.call(this, event);
                    }
                } catch (error) {
                    window.errorHandler?.logError('Event Listener Error', {
                        type,
                        target: this.tagName || this.constructor.name,
                        error: error.message,
                        stack: error.stack
                    });
                    
                    // Don't let event errors break the UI
                    event.preventDefault?.();
                }
            };
            
            return originalAddEventListener.call(this, type, wrappedListener, options);
        };
    }
    
    // Safe async wrapper utility
    safeAsync(asyncFn, fallbackValue = null, context = 'Unknown') {
        return async (...args) => {
            try {
                return await asyncFn(...args);
            } catch (error) {
                this.logError(`Safe Async Error (${context})`, {
                    error: error.message,
                    stack: error.stack,
                    args: args.length
                });
                
                // Return fallback value instead of throwing
                if (typeof fallbackValue === 'function') {
                    return fallbackValue(error);
                }
                return fallbackValue;
            }
        };
    }
    
    // Retry wrapper for important operations
    async withRetry(asyncFn, maxRetries = 3, delay = 1000, context = 'Unknown') {
        let lastError;
        
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                return await asyncFn();
            } catch (error) {
                lastError = error;
                
                this.logError(`Retry Attempt ${attempt}/${maxRetries} Failed (${context})`, {
                    error: error.message,
                    attempt,
                    maxRetries
                });
                
                if (attempt < maxRetries) {
                    await this.sleep(delay * attempt); // Exponential backoff
                }
            }
        }
        
        // All retries failed
        this.logError(`All Retry Attempts Failed (${context})`, {
            error: lastError.message,
            maxRetries
        });
        
        throw lastError;
    }
    
    // Circuit breaker pattern
    createCircuitBreaker(asyncFn, failureThreshold = 5, resetTimeout = 60000) {
        let failures = 0;
        let lastFailureTime = 0;
        let state = 'CLOSED'; // CLOSED, OPEN, HALF_OPEN
        
        return async (...args) => {
            const currentTime = Date.now();
            
            // Reset circuit if timeout has passed
            if (state === 'OPEN' && currentTime - lastFailureTime >= resetTimeout) {
                state = 'HALF_OPEN';
                failures = 0;
            }
            
            // Fail fast if circuit is open
            if (state === 'OPEN') {
                throw new Error('Circuit breaker is OPEN');
            }
            
            try {
                const result = await asyncFn(...args);
                
                // Success - reset circuit
                if (state === 'HALF_OPEN') {
                    state = 'CLOSED';
                }
                failures = 0;
                
                return result;
            } catch (error) {
                failures++;
                lastFailureTime = currentTime;
                
                this.logError('Circuit Breaker Failure', {
                    failures,
                    threshold: failureThreshold,
                    state
                });
                
                // Open circuit if threshold reached
                if (failures >= failureThreshold) {
                    state = 'OPEN';
                    this.logError('Circuit Breaker OPENED', {
                        failures,
                        resetTimeout
                    });
                }
                
                throw error;
            }
        };
    }
    
    // Timeout wrapper
    withTimeout(asyncFn, timeoutMs = 30000, context = 'Unknown') {
        return async (...args) => {
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => {
                    reject(new Error(`Operation timed out after ${timeoutMs}ms`));
                }, timeoutMs);
            });
            
            try {
                return await Promise.race([
                    asyncFn(...args),
                    timeoutPromise
                ]);
            } catch (error) {
                this.logError(`Timeout Error (${context})`, {
                    timeout: timeoutMs,
                    error: error.message
                });
                throw error;
            }
        };
    }
    
    // Helper methods
    isCriticalError(error) {
        const criticalErrors = [
            'ChunkLoadError',
            'NetworkError',
            'SecurityError',
            'TypeError'
        ];
        
        return criticalErrors.some(type => 
            error?.name === type || error?.message?.includes(type)
        );
    }
    
    logError(context, details) {
        const errorEntry = {
            timestamp: new Date().toISOString(),
            context,
            details,
            userAgent: navigator.userAgent,
            url: window.location.href,
            sessionId: this.getSessionId()
        };
        
        // Log to console in development
        if (window.location.hostname === 'localhost') {
            // Development logging (removed console.log for production)
        }
        
        // Log to backend logging service
        if (window.CibozerLogger) {
            window.CibozerLogger.error(context, details);
        }
        
        // Store locally for analysis
        this.storeErrorLocally(errorEntry);
    }
    
    showErrorToUser(message, type = 'error') {
        // Use existing notification system if available
        if (window.CibozerApp?.showNotification) {
            window.CibozerApp.showNotification(message, type);
        } else if (window.showNotification) {
            window.showNotification(message, type);
        } else {
            // Fallback to alert
            alert(message);
        }
    }
    
    storeErrorLocally(errorEntry) {
        try {
            const errors = JSON.parse(localStorage.getItem('cibozer_errors') || '[]');
            errors.push(errorEntry);
            
            // Keep only last 50 errors
            if (errors.length > 50) {
                errors.splice(0, errors.length - 50);
            }
            
            localStorage.setItem('cibozer_errors', JSON.stringify(errors));
        } catch (e) {
            // Ignore localStorage errors
        }
    }
    
    getSessionId() {
        let sessionId = sessionStorage.getItem('cibozer_session_id');
        if (!sessionId) {
            sessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            sessionStorage.setItem('cibozer_session_id', sessionId);
        }
        return sessionId;
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    // Get error summary for debugging
    getErrorSummary() {
        try {
            const errors = JSON.parse(localStorage.getItem('cibozer_errors') || '[]');
            return {
                total: errors.length,
                recent: errors.slice(-10),
                byContext: errors.reduce((acc, error) => {
                    acc[error.context] = (acc[error.context] || 0) + 1;
                    return acc;
                }, {})
            };
        } catch (e) {
            return { total: 0, recent: [], byContext: {} };
        }
    }
    
    // Clear stored errors
    clearErrors() {
        try {
            localStorage.removeItem('cibozer_errors');
        } catch (e) {
            // Ignore
        }
    }
}

// Create global error handler
window.errorHandler = new ErrorHandler();

// Export utilities for use in other scripts
window.ErrorHandling = {
    safeAsync: (...args) => window.errorHandler.safeAsync(...args),
    withRetry: (...args) => window.errorHandler.withRetry(...args),
    withTimeout: (...args) => window.errorHandler.withTimeout(...args),
    createCircuitBreaker: (...args) => window.errorHandler.createCircuitBreaker(...args),
    logError: (...args) => window.errorHandler.logError(...args),
    getErrorSummary: () => window.errorHandler.getErrorSummary(),
    clearErrors: () => window.errorHandler.clearErrors()
};
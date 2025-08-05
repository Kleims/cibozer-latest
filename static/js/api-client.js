/**
 * Robust API Client with Timeout, Retry, and Circuit Breaker
 * Provides bulletproof API communication for Cibozer
 */

class ApiClient {
    constructor() {
        this.baseURL = '';
        this.defaultTimeout = 30000; // 30 seconds
        this.maxRetries = 3;
        this.retryDelay = 1000; // 1 second
        this.circuitBreaker = new Map(); // Track failed endpoints
        this.requestInterceptors = [];
        this.responseInterceptors = [];
    }

    /**
     * Make a request with timeout, retry, and circuit breaker
     */
    async request(url, options = {}) {
        const requestOptions = {
            timeout: this.defaultTimeout,
            retries: this.maxRetries,
            ...options
        };

        // Check circuit breaker
        if (this.isCircuitOpen(url)) {
            throw new Error(`Circuit breaker open for ${url}. Service temporarily unavailable.`);
        }

        let lastError = null;
        
        for (let attempt = 0; attempt <= requestOptions.retries; attempt++) {
            try {
                const response = await this.makeRequest(url, requestOptions);
                
                // Reset circuit breaker on success
                this.resetCircuitBreaker(url);
                
                return response;
            } catch (error) {
                lastError = error;
                
                // Record failure for circuit breaker
                this.recordFailure(url);
                
                // Don't retry on client errors (4xx)
                if (error.status >= 400 && error.status < 500) {
                    break;
                }
                
                // Don't retry on last attempt
                if (attempt === requestOptions.retries) {
                    break;
                }
                
                // Wait before retry with exponential backoff
                await this.sleep(requestOptions.retryDelay * Math.pow(2, attempt));
            }
        }
        
        throw lastError;
    }

    /**
     * Make the actual HTTP request with timeout
     */
    async makeRequest(url, options) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), options.timeout);
        
        try {
            // Apply request interceptors
            const finalOptions = this.applyRequestInterceptors({
                ...options,
                signal: controller.signal
            });
            
            const response = await fetch(url, finalOptions);
            clearTimeout(timeoutId);
            
            // Check if response is ok
            if (!response.ok) {
                const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
                error.status = response.status;
                error.response = response;
                throw error;
            }
            
            // Apply response interceptors
            return this.applyResponseInterceptors(response);
            
        } catch (error) {
            clearTimeout(timeoutId);
            
            // Handle timeout
            if (error.name === 'AbortError') {
                const timeoutError = new Error(`Request timeout after ${options.timeout}ms`);
                timeoutError.code = 'TIMEOUT';
                throw timeoutError;
            }
            
            // Handle network errors
            if (error instanceof TypeError && error.message.includes('fetch')) {
                const networkError = new Error('Network error. Please check your connection.');
                networkError.code = 'NETWORK_ERROR';
                throw networkError;
            }
            
            throw error;
        }
    }

    /**
     * GET request wrapper
     */
    async get(url, options = {}) {
        return this.request(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
    }

    /**
     * POST request wrapper
     */
    async post(url, data = null, options = {}) {
        const requestOptions = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        if (data) {
            requestOptions.body = JSON.stringify(data);
        }

        return this.request(url, requestOptions);
    }

    /**
     * Add CSRF token to requests
     */
    addCSRFToken(options = {}) {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (csrfToken) {
            options.headers = {
                'X-CSRF-Token': csrfToken,
                ...options.headers
            };
        }
        return options;
    }

    /**
     * Circuit breaker implementation
     */
    isCircuitOpen(url) {
        const failures = this.circuitBreaker.get(url);
        if (!failures) return false;
        
        // Open circuit if too many failures in short time
        const now = Date.now();
        const recentFailures = failures.filter(time => now - time < 60000); // 1 minute window
        
        // Open circuit after 5 failures in 1 minute
        return recentFailures.length >= 5;
    }

    recordFailure(url) {
        const failures = this.circuitBreaker.get(url) || [];
        failures.push(Date.now());
        this.circuitBreaker.set(url, failures);
    }

    resetCircuitBreaker(url) {
        this.circuitBreaker.delete(url);
    }

    /**
     * Apply request interceptors
     */
    applyRequestInterceptors(options) {
        return this.requestInterceptors.reduce((opts, interceptor) => {
            return interceptor(opts) || opts;
        }, options);
    }

    /**
     * Apply response interceptors
     */
    applyResponseInterceptors(response) {
        return this.responseInterceptors.reduce((resp, interceptor) => {
            return interceptor(resp) || resp;
        }, response);
    }

    /**
     * Add request interceptor
     */
    addRequestInterceptor(interceptor) {
        this.requestInterceptors.push(interceptor);
    }

    /**
     * Add response interceptor
     */
    addResponseInterceptor(interceptor) {
        this.responseInterceptors.push(interceptor);
    }

    /**
     * Utility: Sleep for given milliseconds
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Parse JSON response safely
     */
    async parseJSON(response) {
        try {
            return await response.json();
        } catch (error) {
            throw new Error('Invalid JSON response from server');
        }
    }

    /**
     * Handle API errors gracefully
     */
    handleError(error) {
        // Log error for debugging
        console.error('API Error:', error);
        
        // Provide user-friendly error messages
        if (error.code === 'TIMEOUT') {
            return 'The request is taking longer than expected. Please try again.';
        }
        
        if (error.code === 'NETWORK_ERROR') {
            return 'Please check your internet connection and try again.';
        }
        
        if (error.status === 429) {
            return 'Too many requests. Please wait a moment and try again.';
        }
        
        if (error.status >= 500) {
            return 'Server error. Our team has been notified. Please try again later.';
        }
        
        if (error.status === 401) {
            return 'Please log in to continue.';
        }
        
        if (error.status === 403) {
            return 'You do not have permission to perform this action.';
        }
        
        // Default error message
        return 'An unexpected error occurred. Please try again.';
    }
}

// Create global API client instance
const apiClient = new ApiClient();

// Add CSRF token interceptor
apiClient.addRequestInterceptor((options) => {
    return apiClient.addCSRFToken(options);
});

// Add JSON parsing interceptor
apiClient.addResponseInterceptor(async (response) => {
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
        const jsonData = await apiClient.parseJSON(response);
        response.data = jsonData;
    }
    return response;
});

// Export for use in other scripts
window.apiClient = apiClient;
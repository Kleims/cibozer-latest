/**
 * Cibozer Web Application JavaScript
 * Main application logic for the web interface
 */

// Global variables
let currentMealPlan = null;
let currentUser = null;

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check for reduced motion preference
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        document.documentElement.style.setProperty('--animation-duration', '0s');
        // Reduced motion mode enabled
    }
    
    initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize navigation
    initializeNavigation();
    
    // Initialize notifications
    initializeNotifications();
    
    // Initialize modals
    initializeModals();
    
    // Cibozer app initialized successfully
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                showNotification('Please check your form inputs', 'warning');
            }
            
            form.classList.add('was-validated');
        });
    });
    
    // Add real-time validation feedback
    const inputs = document.querySelectorAll('input[required], select[required], textarea[required]');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.checkValidity()) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else {
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
            }
        });
    });
}

/**
 * Initialize navigation
 */
function initializeNavigation() {
    // Highlight active navigation item
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || (currentPath === '/' && href === '/')) {
            link.classList.add('active');
        }
    });
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/**
 * Initialize notifications system
 */
function initializeNotifications() {
    // Auto-hide flash messages after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

/**
 * Initialize modals
 */
function initializeModals() {
    // Handle modal backdrop clicks
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            const modal = bootstrap.Modal.getInstance(e.target);
            if (modal) {
                modal.hide();
            }
        }
    });
}

/**
 * Show notification to user
 * @param {string} message - Message to display
 * @param {string} type - Type of notification (success, error, warning, info)
 * @param {number} duration - Duration in milliseconds (default: 5000)
 */
function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type} show`;
    
    const iconMap = {
        success: 'check-circle',
        error: 'exclamation-triangle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    
    const titleMap = {
        success: 'Success',
        error: 'Error',
        warning: 'Warning',
        info: 'Info'
    };
    
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-${iconMap[type]} me-3"></i>
            <div>
                <div class="fw-bold">${titleMap[type]}</div>
                <div>${message}</div>
            </div>
            <button type="button" class="btn-close ms-auto" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-hide after duration
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }, duration);
}

/**
 * Format number with proper decimal places
 * @param {number} num - Number to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted number
 */
function formatNumber(num, decimals = 1) {
    if (typeof num !== 'number') return '0';
    return num.toFixed(decimals);
}

/**
 * Capitalize first letter of string
 * @param {string} str - String to capitalize
 * @returns {string} Capitalized string
 */
function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Format ingredient name for display
 * @param {string} ingredient - Ingredient name
 * @returns {string} Formatted ingredient name
 */
function formatIngredientName(ingredient) {
    if (!ingredient) return '';
    return ingredient.replace(/_/g, ' ').split(' ').map(capitalize).join(' ');
}

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean} Whether email is valid
 */
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Debounce function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
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

/**
 * Make API request with robust error handling, retry, and circuit breaker
 * @param {string} url - API endpoint
 * @param {Object} options - Request options
 * @returns {Promise} API response
 */
async function apiRequest(url, options = {}) {
    try {
        // Use the robust API client if available
        if (window.apiClient) {
            if (options.method === 'POST' || options.method === 'PUT' || options.method === 'PATCH') {
                const data = options.body ? JSON.parse(options.body) : null;
                const response = await window.apiClient.post(url, data, {
                    headers: options.headers,
                    timeout: options.timeout,
                    retries: options.retries
                });
                return response.data || response;
            } else {
                const response = await window.apiClient.get(url, {
                    headers: options.headers,
                    timeout: options.timeout,
                    retries: options.retries
                });
                return response.data || response;
            }
        } else {
            // Fallback to basic fetch if API client not available
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                },
            };
            
            const response = await fetch(url, { ...defaultOptions, ...options });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        }
    } catch (error) {
        // Use error handling if available
        if (window.ErrorHandling) {
            window.ErrorHandling.logError('API Request Failed', { 
                url, 
                method: options.method || 'GET',
                error: error.message 
            });
        }
        
        // Show user-friendly error message
        if (window.apiClient && typeof window.apiClient.handleError === 'function') {
            const userMessage = window.apiClient.handleError(error);
            if (window.showNotification) {
                window.showNotification(userMessage, 'error');
            }
        }
        
        throw error;
    }
}

/**
 * Save data to localStorage
 * @param {string} key - Storage key
 * @param {*} data - Data to store
 */
function saveToStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
    } catch (error) {
        console.error('Failed to save to localStorage:', error);
    }
}

/**
 * Load data from localStorage
 * @param {string} key - Storage key
 * @returns {*} Loaded data or null
 */
function loadFromStorage(key) {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : null;
    } catch (error) {
        console.error('Failed to load from localStorage:', error);
        return null;
    }
}

/**
 * Clear data from localStorage
 * @param {string} key - Storage key
 */
function clearFromStorage(key) {
    try {
        localStorage.removeItem(key);
    } catch (error) {
        console.error('Failed to clear from localStorage:', error);
    }
}

/**
 * Format date for display
 * @param {Date|string} date - Date to format
 * @returns {string} Formatted date
 */
function formatDate(date) {
    if (!date) return '';
    const d = new Date(date);
    return d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Format time for display
 * @param {Date|string} date - Date to format
 * @returns {string} Formatted time
 */
function formatTime(date) {
    if (!date) return '';
    const d = new Date(date);
    return d.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showNotification('Copied to clipboard!', 'success', 2000);
    } catch (error) {
        console.error('Failed to copy to clipboard:', error);
        showNotification('Failed to copy to clipboard', 'error');
    }
}

/**
 * Download data as file
 * @param {string} data - Data to download
 * @param {string} filename - Name of file
 * @param {string} mimeType - MIME type of file
 */
function downloadFile(data, filename, mimeType = 'text/plain') {
    const blob = new Blob([data], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

/**
 * Animate element into view
 * @param {HTMLElement} element - Element to animate
 * @param {string} animation - Animation class name
 */
function animateElement(element, animation = 'fade-in') {
    if (!element) return;
    
    element.classList.add(animation);
    
    element.addEventListener('animationend', function() {
        element.classList.remove(animation);
    }, { once: true });
}

/**
 * Scroll to element smoothly
 * @param {HTMLElement|string} element - Element or selector
 * @param {Object} options - Scroll options
 */
function scrollToElement(element, options = {}) {
    const target = typeof element === 'string' ? document.querySelector(element) : element;
    if (!target) return;
    
    const defaultOptions = {
        behavior: 'smooth',
        block: 'start',
        inline: 'nearest'
    };
    
    target.scrollIntoView({ ...defaultOptions, ...options });
}

/**
 * Check if element is in viewport
 * @param {HTMLElement} element - Element to check
 * @returns {boolean} Whether element is in viewport
 */
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

/**
 * Throttle function calls
 * @param {Function} func - Function to throttle
 * @param {number} limit - Time limit in milliseconds
 * @returns {Function} Throttled function
 */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Export functions for use in other scripts
window.CibozerApp = {
    showNotification,
    formatNumber,
    capitalize,
    formatIngredientName,
    validateEmail,
    debounce,
    apiRequest,
    saveToStorage,
    loadFromStorage,
    clearFromStorage,
    formatDate,
    formatTime,
    copyToClipboard,
    downloadFile,
    animateElement,
    scrollToElement,
    isInViewport,
    throttle
};

// Cibozer app.js loaded successfully
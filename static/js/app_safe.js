/**
 * Cibozer Web Application JavaScript - Safe Version
 * Main application logic with proper error handling
 */

// Global variables
let currentMealPlan = null;
let currentUser = null;

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // DOM loaded, initializing Cibozer app
    
    try {
        // Check for reduced motion preference
        if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            document.documentElement.style.setProperty('--animation-duration', '0s');
            // Reduced motion mode enabled
        }
        
        initializeApp();
    } catch (error) {
        console.error('Error initializing app:', error);
    }
});

/**
 * Initialize the application
 */
function initializeApp() {
    // Initialize components with error handling
    const initializers = [
        { name: 'tooltips', fn: initializeTooltips },
        { name: 'form validation', fn: initializeFormValidation },
        { name: 'navigation', fn: initializeNavigation }
    ];
    
    initializers.forEach(init => {
        try {
            init.fn();
            // Initialized component
        } catch (error) {
            console.error(`Error initializing ${init.name}:`, error);
        }
    });
    
    // Cibozer app initialization complete
}

/**
 * Initialize Bootstrap tooltips safely
 */
function initializeTooltips() {
    if (typeof bootstrap === 'undefined') {
        console.warn('Bootstrap not loaded, skipping tooltip initialization');
        return;
    }
    
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (tooltipTriggerList.length > 0) {
        tooltipTriggerList.forEach(function (tooltipTriggerEl) {
            try {
                new bootstrap.Tooltip(tooltipTriggerEl);
            } catch (e) {
                console.error('Error initializing tooltip:', e);
            }
        });
    }
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
            }
            
            form.classList.add('was-validated');
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
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}

/**
 * Show notification message
 */
function showNotification(message, type = 'info') {
    // Log message (removed for production)
    
    // Check if we have a notification container
    const container = document.getElementById('notification-container');
    if (!container) {
        // Create one if it doesn't exist
        const newContainer = document.createElement('div');
        newContainer.id = 'notification-container';
        newContainer.style.position = 'fixed';
        newContainer.style.top = '20px';
        newContainer.style.right = '20px';
        newContainer.style.zIndex = '9999';
        document.body.appendChild(newContainer);
    }
    
    // Create alert
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.setAttribute('role', 'alert');
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const notificationContainer = document.getElementById('notification-container');
    notificationContainer.appendChild(alert);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

/**
 * Make API request with CSRF token
 */
async function apiRequest(url, options = {}) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]');
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken ? csrfToken.content : ''
        }
    };
    
    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...(options.headers || {})
        }
    };
    
    try {
        const response = await fetch(url, mergedOptions);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
            throw new Error(errorData.error || `Request failed with status ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        // Log error for debugging (without console.log)
        if (window.CibozerLogger) {
            window.CibozerLogger.error('API request failed', { url, error: error.message });
        }
        
        // Show user-friendly notification
        showNotification(error.message || 'Request failed', 'danger');
        
        // Re-throw for caller to handle
        throw error;
    }
}

// Export functions for use in other scripts
window.CibozerApp = {
    showNotification,
    apiRequest
};
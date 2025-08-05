/**
 * Enhanced Error Messages and User Guidance
 * Provides intuitive, helpful error messages and recovery options
 */

class ErrorMessagesUX {
    constructor() {
        this.errorMappings = this.getErrorMappings();
        this.init();
    }
    
    init() {
        // Override default error handlers
        this.enhanceFormValidation();
        
        // Intercept API errors
        this.interceptAPIErrors();
        
        // Setup global error boundary
        this.setupErrorBoundary();
        
        // Monitor for common issues
        this.monitorCommonIssues();
    }
    
    getErrorMappings() {
        return {
            // Authentication errors
            'Invalid email or password': {
                title: 'Login Failed',
                message: 'The email or password you entered is incorrect.',
                suggestions: [
                    'Double-check your email address for typos',
                    'Make sure Caps Lock is turned off',
                    'Try resetting your password if you\'ve forgotten it'
                ],
                actions: [
                    { text: 'Reset Password', href: '/auth/forgot-password', class: 'btn-primary' },
                    { text: 'Try Again', action: 'retry', class: 'btn-secondary' }
                ]
            },
            
            'Email already registered': {
                title: 'Account Already Exists',
                message: 'An account with this email already exists.',
                suggestions: [
                    'Try logging in instead',
                    'Use a different email address',
                    'Reset your password if you\'ve forgotten it'
                ],
                actions: [
                    { text: 'Log In', href: '/auth/login', class: 'btn-primary' },
                    { text: 'Reset Password', href: '/auth/forgot-password', class: 'btn-secondary' }
                ]
            },
            
            // Payment errors
            'Payment required': {
                title: 'Upgrade Required',
                message: 'You\'ve used all your free meal plans this month.',
                suggestions: [
                    'Upgrade to Premium for unlimited meal plans',
                    'Premium includes PDF exports and shopping lists',
                    'Cancel anytime with no hidden fees'
                ],
                actions: [
                    { text: 'View Plans', href: '/pricing', class: 'btn-success' },
                    { text: 'Maybe Later', action: 'dismiss', class: 'btn-secondary' }
                ]
            },
            
            'card_declined': {
                title: 'Payment Declined',
                message: 'Your card was declined by your bank.',
                suggestions: [
                    'Check your card details are correct',
                    'Ensure you have sufficient funds',
                    'Contact your bank if the problem persists',
                    'Try a different payment method'
                ],
                actions: [
                    { text: 'Update Card', action: 'updateCard', class: 'btn-primary' },
                    { text: 'Contact Support', href: '/support', class: 'btn-secondary' }
                ]
            },
            
            // API errors
            'Network error': {
                title: 'Connection Problem',
                message: 'We\'re having trouble connecting to our servers.',
                suggestions: [
                    'Check your internet connection',
                    'Try refreshing the page',
                    'The issue might be temporary'
                ],
                actions: [
                    { text: 'Retry', action: 'retry', class: 'btn-primary' },
                    { text: 'Refresh Page', action: 'refresh', class: 'btn-secondary' }
                ]
            },
            
            'Server error': {
                title: 'Something Went Wrong',
                message: 'We encountered an unexpected error on our end.',
                suggestions: [
                    'We\'ve been notified and are working on it',
                    'Please try again in a few moments',
                    'Your data has been saved'
                ],
                actions: [
                    { text: 'Try Again', action: 'retry', class: 'btn-primary' },
                    { text: 'Go to Dashboard', href: '/dashboard', class: 'btn-secondary' }
                ]
            },
            
            // Validation errors
            'Invalid calorie amount': {
                title: 'Invalid Calorie Amount',
                message: 'Please enter a calorie amount between 1200 and 5000.',
                suggestions: [
                    'Most adults need 1500-2500 calories per day',
                    'Consider your activity level and goals',
                    'Consult a nutritionist for personalized advice'
                ],
                actions: [
                    { text: 'Use Recommended (2000)', action: 'setValue:2000', class: 'btn-primary' },
                    { text: 'Calculate My Needs', href: '/calorie-calculator', class: 'btn-secondary' }
                ]
            },
            
            // Timeout errors
            'Request timeout': {
                title: 'Taking Too Long',
                message: 'The request is taking longer than expected.',
                suggestions: [
                    'This might be due to high demand',
                    'Complex meal plans take a bit longer to generate',
                    'Your request is still being processed'
                ],
                actions: [
                    { text: 'Keep Waiting', action: 'wait', class: 'btn-primary' },
                    { text: 'Cancel & Retry', action: 'cancel', class: 'btn-secondary' }
                ]
            }
        };
    }
    
    // Enhanced form validation
    enhanceFormValidation() {
        document.addEventListener('invalid', (e) => {
            e.preventDefault();
            const field = e.target;
            
            // Remove default browser validation message
            field.setCustomValidity('');
            
            // Add custom error handling
            this.showFieldError(field);
        }, true);
        
        // Real-time validation
        document.addEventListener('blur', (e) => {
            if (e.target.matches('input, select, textarea')) {
                this.validateField(e.target);
            }
        }, true);
        
        // Clear errors on input
        document.addEventListener('input', (e) => {
            if (e.target.matches('.is-invalid')) {
                this.clearFieldError(e.target);
            }
        });
    }
    
    showFieldError(field) {
        const errorMessage = this.getFieldErrorMessage(field);
        
        field.classList.add('is-invalid');
        
        // Remove existing error
        const existingError = field.parentElement.querySelector('.invalid-feedback');
        if (existingError) existingError.remove();
        
        // Add new error with animation
        const error = document.createElement('div');
        error.className = 'invalid-feedback fade-in';
        error.innerHTML = `
            <i class="fas fa-exclamation-circle me-1"></i>
            ${errorMessage}
        `;
        
        field.parentElement.appendChild(error);
        
        // Add shake animation
        field.classList.add('shake');
        setTimeout(() => field.classList.remove('shake'), 500);
        
        // Focus the field
        field.focus();
    }
    
    getFieldErrorMessage(field) {
        const fieldName = field.name || field.id;
        const fieldLabel = field.labels?.[0]?.textContent || fieldName;
        
        // Custom messages based on validation type
        if (field.validity.valueMissing) {
            return `Please enter your ${fieldLabel.toLowerCase()}`;
        }
        
        if (field.validity.typeMismatch) {
            if (field.type === 'email') {
                return 'Please enter a valid email address (e.g., name@example.com)';
            }
            if (field.type === 'url') {
                return 'Please enter a valid URL (e.g., https://example.com)';
            }
        }
        
        if (field.validity.tooShort) {
            return `${fieldLabel} must be at least ${field.minLength} characters`;
        }
        
        if (field.validity.tooLong) {
            return `${fieldLabel} must be no more than ${field.maxLength} characters`;
        }
        
        if (field.validity.rangeUnderflow) {
            return `Please enter a value of at least ${field.min}`;
        }
        
        if (field.validity.rangeOverflow) {
            return `Please enter a value no more than ${field.max}`;
        }
        
        if (field.validity.patternMismatch) {
            return field.dataset.patternError || `Please match the required format`;
        }
        
        // Field-specific messages
        if (fieldName === 'password') {
            return 'Password must be at least 8 characters with a mix of letters and numbers';
        }
        
        if (fieldName === 'calories') {
            return 'Please enter a calorie amount between 1200 and 5000';
        }
        
        return 'Please check this field';
    }
    
    validateField(field) {
        if (!field.value && !field.required) return;
        
        const isValid = field.checkValidity();
        
        if (!isValid) {
            this.showFieldError(field);
        } else {
            this.clearFieldError(field);
            
            // Show success state for important fields
            if (field.required || field.type === 'email' || field.type === 'password') {
                field.classList.add('is-valid');
            }
        }
    }
    
    clearFieldError(field) {
        field.classList.remove('is-invalid');
        const error = field.parentElement.querySelector('.invalid-feedback');
        if (error) {
            error.classList.add('fade-out');
            setTimeout(() => error.remove(), 300);
        }
    }
    
    // Intercept API errors
    interceptAPIErrors() {
        // Override fetch to intercept responses
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            try {
                const response = await originalFetch(...args);
                
                if (!response.ok) {
                    const data = await response.clone().json().catch(() => ({}));
                    this.handleAPIError(response.status, data);
                }
                
                return response;
            } catch (error) {
                this.handleNetworkError(error);
                throw error;
            }
        };
    }
    
    handleAPIError(status, data) {
        const errorKey = data.error || data.message || 'Server error';
        const mapping = this.errorMappings[errorKey];
        
        if (mapping) {
            this.showErrorModal(mapping);
        } else {
            // Generic error handling
            this.showErrorToast(errorKey, status);
        }
    }
    
    handleNetworkError(error) {
        if (error.name === 'NetworkError' || !navigator.onLine) {
            this.showErrorModal(this.errorMappings['Network error']);
        }
    }
    
    // Error display methods
    showErrorModal(errorConfig) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header border-0">
                        <h5 class="modal-title">
                            <i class="fas fa-exclamation-triangle text-warning me-2"></i>
                            ${errorConfig.title}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p class="mb-3">${errorConfig.message}</p>
                        
                        ${errorConfig.suggestions ? `
                            <div class="alert alert-light">
                                <h6 class="alert-heading">What you can do:</h6>
                                <ul class="mb-0">
                                    ${errorConfig.suggestions.map(s => `<li>${s}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                    <div class="modal-footer border-0">
                        ${errorConfig.actions.map(action => this.createActionButton(action)).join('')}
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Cleanup on hide
        modal.addEventListener('hidden.bs.modal', () => modal.remove());
    }
    
    createActionButton(action) {
        if (action.href) {
            return `<a href="${action.href}" class="btn ${action.class}">${action.text}</a>`;
        }
        
        return `<button type="button" class="btn ${action.class}" data-action="${action.action}">${action.text}</button>`;
    }
    
    showErrorToast(message, status) {
        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-white bg-danger border-0';
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <strong>Error ${status}:</strong> ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(container);
        }
        
        container.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }
    
    // Error boundary for JavaScript errors
    setupErrorBoundary() {
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            
            // Don't show error modal for minor issues
            if (this.isMinorError(event.error)) return;
            
            this.showErrorModal({
                title: 'Unexpected Error',
                message: 'Something went wrong while processing your request.',
                suggestions: [
                    'Try refreshing the page',
                    'Clear your browser cache',
                    'Try using a different browser'
                ],
                actions: [
                    { text: 'Refresh Page', action: 'refresh', class: 'btn-primary' },
                    { text: 'Report Issue', href: '/support', class: 'btn-secondary' }
                ]
            });
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
        });
    }
    
    isMinorError(error) {
        const minorErrors = [
            'ResizeObserver loop limit exceeded',
            'Non-Error promise rejection captured'
        ];
        
        return minorErrors.some(msg => error?.message?.includes(msg));
    }
    
    // Monitor common issues
    monitorCommonIssues() {
        // Monitor for slow connections
        if ('connection' in navigator) {
            const connection = navigator.connection;
            
            if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') {
                this.showSlowConnectionWarning();
            }
        }
        
        // Monitor for offline status
        window.addEventListener('offline', () => {
            this.showOfflineWarning();
        });
        
        window.addEventListener('online', () => {
            this.hideOfflineWarning();
        });
    }
    
    showSlowConnectionWarning() {
        const warning = document.createElement('div');
        warning.className = 'alert alert-warning alert-dismissible fade show position-fixed';
        warning.style.cssText = 'bottom: 20px; left: 20px; right: 20px; z-index: 1050;';
        warning.innerHTML = `
            <i class="fas fa-wifi me-2"></i>
            <strong>Slow Connection Detected</strong>
            <p class="mb-0 mt-1">Some features may take longer to load. We're optimizing your experience.</p>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(warning);
    }
    
    showOfflineWarning() {
        const warning = document.createElement('div');
        warning.id = 'offline-warning';
        warning.className = 'alert alert-danger position-fixed';
        warning.style.cssText = 'top: 0; left: 0; right: 0; z-index: 9999; margin: 0; border-radius: 0;';
        warning.innerHTML = `
            <div class="container">
                <i class="fas fa-wifi-slash me-2"></i>
                <strong>You're Offline</strong> - Some features may not work until you're back online.
            </div>
        `;
        
        document.body.prepend(warning);
    }
    
    hideOfflineWarning() {
        const warning = document.getElementById('offline-warning');
        if (warning) {
            warning.remove();
            
            // Show reconnection success
            this.showSuccessToast('Back online! Everything should work normally now.');
        }
    }
    
    showSuccessToast(message) {
        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-white bg-success border-0';
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-check-circle me-2"></i>${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(container);
        }
        
        container.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.errorMessagesUX = new ErrorMessagesUX();
});

// CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
    
    .shake {
        animation: shake 0.5s ease-in-out;
    }
    
    .fade-in {
        animation: fadeIn 0.3s ease-in;
    }
    
    .fade-out {
        animation: fadeOut 0.3s ease-out forwards;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes fadeOut {
        from { opacity: 1; transform: translateY(0); }
        to { opacity: 0; transform: translateY(-10px); }
    }
`;
document.head.appendChild(style);
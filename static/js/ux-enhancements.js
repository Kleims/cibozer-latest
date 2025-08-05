/**
 * User Experience Enhancements for Cibozer
 * Implements loading states, success confirmations, tooltips, and more
 */

class UXEnhancer {
    constructor() {
        this.init();
    }

    init() {
        this.initLoadingStates();
        this.initTooltips();
        this.initSuccessConfirmations();
        this.initFormValidation();
        this.initEmptyStates();
        this.initProgressIndicators();
        this.initKeyboardShortcuts();
        this.initAutoSave();
        this.initSmartDefaults();
        this.initFocusManagement();
        this.initAccessibility();
    }

    // Loading States for all async operations
    initLoadingStates() {
        // Override fetch to add loading states
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            const loadingId = this.showLoading();
            try {
                const response = await originalFetch(...args);
                this.hideLoading(loadingId);
                return response;
            } catch (error) {
                this.hideLoading(loadingId);
                throw error;
            }
        };

        // Add loading states to all buttons
        document.addEventListener('click', (e) => {
            const button = e.target.closest('button[type="submit"], button[data-loading]');
            if (button && !button.disabled) {
                this.setButtonLoading(button);
            }
        });
    }

    showLoading(message = 'Loading...') {
        const loadingId = `loading-${Date.now()}`;
        const loadingEl = document.createElement('div');
        loadingEl.id = loadingId;
        loadingEl.className = 'loading-overlay';
        loadingEl.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">${message}</span>
                </div>
                <p class="mt-2">${message}</p>
            </div>
        `;
        document.body.appendChild(loadingEl);
        return loadingId;
    }

    hideLoading(loadingId) {
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) {
            loadingEl.classList.add('fade-out');
            setTimeout(() => loadingEl.remove(), 300);
        }
    }

    setButtonLoading(button, loading = true) {
        if (loading) {
            button.disabled = true;
            button.dataset.originalText = button.innerHTML;
            button.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                Loading...
            `;
        } else {
            button.disabled = false;
            if (button.dataset.originalText) {
                button.innerHTML = button.dataset.originalText;
                delete button.dataset.originalText;
            }
        }
    }

    // Tooltips for complex features
    initTooltips() {
        // Add helpful tooltips
        const tooltipData = {
            '#calories': 'Daily calorie target. Recommended: 2000 for adults',
            '[name="diet"]': 'Choose your dietary preference',
            '#generateBtn': 'Generate a personalized meal plan based on your preferences',
            '.save-plan': 'Save this meal plan to your account',
            '.export-pdf': 'Export as PDF (Premium feature)',
            '.share-plan': 'Share this meal plan with others'
        };

        Object.entries(tooltipData).forEach(([selector, text]) => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                el.setAttribute('data-bs-toggle', 'tooltip');
                el.setAttribute('data-bs-placement', 'top');
                el.setAttribute('title', text);
            });
        });

        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }

    // Success confirmations for all actions
    initSuccessConfirmations() {
        this.successQueue = [];
    }

    showSuccess(message, duration = 3000) {
        const successId = `success-${Date.now()}`;
        const successEl = document.createElement('div');
        successEl.id = successId;
        successEl.className = 'success-notification';
        successEl.innerHTML = `
            <div class="alert alert-success d-flex align-items-center" role="alert">
                <svg class="bi flex-shrink-0 me-2" width="24" height="24" role="img" aria-label="Success:">
                    <use xlink:href="#check-circle-fill"/>
                </svg>
                <div>${message}</div>
            </div>
        `;
        
        // Add to notification container
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(successEl);
        
        // Auto-remove after duration
        setTimeout(() => {
            successEl.classList.add('fade-out');
            setTimeout(() => successEl.remove(), 300);
        }, duration);
    }

    // Enhanced form validation
    initFormValidation() {
        const forms = document.querySelectorAll('form[data-validate]');
        
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!form.checkValidity()) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                form.classList.add('was-validated');
            });

            // Real-time validation
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                input.addEventListener('blur', () => {
                    this.validateField(input);
                });

                input.addEventListener('input', () => {
                    if (input.classList.contains('is-invalid')) {
                        this.validateField(input);
                    }
                });
            });
        });
    }

    validateField(field) {
        const isValid = field.checkValidity();
        
        if (isValid) {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        } else {
            field.classList.remove('is-valid');
            field.classList.add('is-invalid');
            
            // Custom error messages
            const customMessages = {
                'email': 'Please enter a valid email address',
                'password': 'Password must be at least 8 characters with uppercase, lowercase, number, and special character',
                'calories': 'Please enter calories between 1200 and 5000'
            };
            
            if (customMessages[field.name]) {
                field.setCustomValidity(customMessages[field.name]);
            }
        }
    }

    // Empty states
    initEmptyStates() {
        const emptyContainers = document.querySelectorAll('[data-empty-state]');
        
        emptyContainers.forEach(container => {
            if (container.children.length === 0) {
                const emptyState = this.createEmptyState(container.dataset.emptyState);
                container.appendChild(emptyState);
            }
        });
    }

    createEmptyState(type) {
        const emptyStates = {
            'meal-plans': {
                icon: '🍽️',
                title: 'No meal plans yet',
                message: 'Generate your first meal plan to get started',
                action: 'Generate Meal Plan',
                actionUrl: '/dashboard'
            },
            'saved-plans': {
                icon: '📋',
                title: 'No saved plans',
                message: 'Save a meal plan to access it later',
                action: 'Browse Plans',
                actionUrl: '/dashboard'
            }
        };

        const state = emptyStates[type] || emptyStates['meal-plans'];
        
        const div = document.createElement('div');
        div.className = 'empty-state text-center py-5';
        div.innerHTML = `
            <div class="empty-state-icon">${state.icon}</div>
            <h3>${state.title}</h3>
            <p class="text-muted">${state.message}</p>
            <a href="${state.actionUrl}" class="btn btn-primary">${state.action}</a>
        `;
        
        return div;
    }

    // Progress indicators
    initProgressIndicators() {
        // Multi-step form progress
        const multiStepForms = document.querySelectorAll('[data-multi-step]');
        
        multiStepForms.forEach(form => {
            const steps = form.querySelectorAll('[data-step]');
            const progressBar = form.querySelector('.progress-bar');
            let currentStep = 0;
            
            const updateProgress = () => {
                const progress = ((currentStep + 1) / steps.length) * 100;
                if (progressBar) {
                    progressBar.style.width = `${progress}%`;
                    progressBar.setAttribute('aria-valuenow', progress);
                }
            };
            
            // Navigation
            form.querySelectorAll('[data-next-step]').forEach(btn => {
                btn.addEventListener('click', () => {
                    if (currentStep < steps.length - 1) {
                        steps[currentStep].classList.add('d-none');
                        currentStep++;
                        steps[currentStep].classList.remove('d-none');
                        updateProgress();
                    }
                });
            });
            
            form.querySelectorAll('[data-prev-step]').forEach(btn => {
                btn.addEventListener('click', () => {
                    if (currentStep > 0) {
                        steps[currentStep].classList.add('d-none');
                        currentStep--;
                        steps[currentStep].classList.remove('d-none');
                        updateProgress();
                    }
                });
            });
            
            updateProgress();
        });
    }

    // Keyboard shortcuts
    initKeyboardShortcuts() {
        const shortcuts = {
            'g h': () => window.location.href = '/',
            'g d': () => window.location.href = '/dashboard',
            'g p': () => window.location.href = '/profile',
            'n': () => document.getElementById('generateBtn')?.click(),
            's': () => document.getElementById('savePlanBtn')?.click(),
            '?': () => this.showKeyboardShortcuts()
        };

        let keys = [];
        
        document.addEventListener('keydown', (e) => {
            // Ignore if typing in input
            if (e.target.matches('input, textarea, select')) return;
            
            keys.push(e.key);
            keys = keys.slice(-10); // Keep last 10 keys
            
            const keysStr = keys.join(' ');
            
            Object.entries(shortcuts).forEach(([shortcut, action]) => {
                if (keysStr.includes(shortcut)) {
                    e.preventDefault();
                    action();
                    keys = [];
                }
            });
        });
    }

    showKeyboardShortcuts() {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Keyboard Shortcuts</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <dl class="row">
                            <dt class="col-sm-3">g h</dt>
                            <dd class="col-sm-9">Go to Home</dd>
                            <dt class="col-sm-3">g d</dt>
                            <dd class="col-sm-9">Go to Dashboard</dd>
                            <dt class="col-sm-3">n</dt>
                            <dd class="col-sm-9">New meal plan</dd>
                            <dt class="col-sm-3">s</dt>
                            <dd class="col-sm-9">Save plan</dd>
                            <dt class="col-sm-3">?</dt>
                            <dd class="col-sm-9">Show shortcuts</dd>
                        </dl>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        modal.addEventListener('hidden.bs.modal', () => modal.remove());
    }

    // Auto-save functionality
    initAutoSave() {
        const autoSaveForms = document.querySelectorAll('[data-auto-save]');
        
        autoSaveForms.forEach(form => {
            let saveTimeout;
            const saveIndicator = document.createElement('span');
            saveIndicator.className = 'auto-save-indicator text-muted ms-2';
            form.appendChild(saveIndicator);
            
            const autoSave = () => {
                saveIndicator.textContent = 'Saving...';
                
                // Save to localStorage
                const formData = new FormData(form);
                const data = Object.fromEntries(formData);
                localStorage.setItem(`autosave-${form.id}`, JSON.stringify(data));
                
                setTimeout(() => {
                    saveIndicator.textContent = 'Saved';
                    setTimeout(() => {
                        saveIndicator.textContent = '';
                    }, 2000);
                }, 500);
            };
            
            // Restore saved data
            const savedData = localStorage.getItem(`autosave-${form.id}`);
            if (savedData) {
                const data = JSON.parse(savedData);
                Object.entries(data).forEach(([name, value]) => {
                    const field = form.elements[name];
                    if (field) field.value = value;
                });
            }
            
            // Auto-save on input
            form.addEventListener('input', () => {
                clearTimeout(saveTimeout);
                saveIndicator.textContent = 'Typing...';
                saveTimeout = setTimeout(autoSave, 1000);
            });
        });
    }

    // Smart defaults
    initSmartDefaults() {
        // Set smart defaults based on user history or preferences
        const defaults = {
            calories: this.getSmartDefault('calories', 2000),
            diet: this.getSmartDefault('diet', 'standard'),
            days: this.getSmartDefault('days', 1)
        };
        
        Object.entries(defaults).forEach(([field, value]) => {
            const element = document.getElementById(field) || document.querySelector(`[name="${field}"]`);
            if (element && !element.value) {
                element.value = value;
            }
        });
    }

    getSmartDefault(field, fallback) {
        // Get from user preferences or last used
        const lastUsed = localStorage.getItem(`last-${field}`);
        return lastUsed || fallback;
    }

    // Focus management
    initFocusManagement() {
        // Trap focus in modals
        document.addEventListener('shown.bs.modal', (e) => {
            const modal = e.target;
            const focusableElements = modal.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            
            const firstFocusable = focusableElements[0];
            const lastFocusable = focusableElements[focusableElements.length - 1];
            
            firstFocusable?.focus();
            
            modal.addEventListener('keydown', (e) => {
                if (e.key === 'Tab') {
                    if (e.shiftKey) {
                        if (document.activeElement === firstFocusable) {
                            lastFocusable.focus();
                            e.preventDefault();
                        }
                    } else {
                        if (document.activeElement === lastFocusable) {
                            firstFocusable.focus();
                            e.preventDefault();
                        }
                    }
                }
            });
        });
    }

    // Accessibility enhancements
    initAccessibility() {
        // Announce dynamic content changes
        this.liveRegion = document.createElement('div');
        this.liveRegion.setAttribute('aria-live', 'polite');
        this.liveRegion.setAttribute('aria-atomic', 'true');
        this.liveRegion.className = 'visually-hidden';
        document.body.appendChild(this.liveRegion);
        
        // Skip to main content link
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.className = 'skip-to-main';
        skipLink.textContent = 'Skip to main content';
        document.body.insertBefore(skipLink, document.body.firstChild);
        
        // Ensure all images have alt text
        document.querySelectorAll('img:not([alt])').forEach(img => {
            img.alt = 'Decorative image';
        });
        
        // Add ARIA labels to icon buttons
        document.querySelectorAll('button:has(svg):not([aria-label])').forEach(btn => {
            btn.setAttribute('aria-label', 'Action button');
        });
    }

    announce(message) {
        this.liveRegion.textContent = message;
    }
}

// Initialize UX enhancements
document.addEventListener('DOMContentLoaded', () => {
    window.uxEnhancer = new UXEnhancer();
});

// Add CSS for UX enhancements
const style = document.createElement('style');
style.textContent = `
.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
}

.loading-spinner {
    text-align: center;
}

.notification-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 9998;
    max-width: 400px;
}

.success-notification {
    animation: slideIn 0.3s ease-out;
    margin-bottom: 10px;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

.fade-out {
    animation: fadeOut 0.3s ease-out forwards;
}

@keyframes fadeOut {
    to {
        opacity: 0;
        transform: translateY(-10px);
    }
}

.empty-state {
    color: #6c757d;
}

.empty-state-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
}

.auto-save-indicator {
    font-size: 0.875rem;
}

.skip-to-main {
    position: absolute;
    left: -9999px;
    z-index: 999;
    padding: 1em;
    background: #000;
    color: #fff;
    text-decoration: none;
}

.skip-to-main:focus {
    left: 50%;
    transform: translateX(-50%);
    top: 0;
}

/* Focus indicators */
*:focus {
    outline: 2px solid #0d6efd;
    outline-offset: 2px;
}

button:focus,
a:focus {
    outline: 3px solid #0d6efd;
    outline-offset: 3px;
}

/* Touch targets */
button,
a,
input,
select,
textarea {
    min-height: 44px;
    min-width: 44px;
}

/* High contrast mode support */
@media (prefers-contrast: high) {
    .btn-primary {
        border: 2px solid;
    }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
`;
document.head.appendChild(style);
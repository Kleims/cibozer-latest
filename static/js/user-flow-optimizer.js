/**
 * User Flow Optimizer for Cibozer
 * Reduces friction and improves user journey
 */

class UserFlowOptimizer {
    constructor() {
        this.currentStep = 0;
        this.userPreferences = this.loadUserPreferences();
        this.analytics = {
            startTime: Date.now(),
            interactions: [],
            abandonmentPoints: []
        };
        
        this.init();
    }
    
    init() {
        // Auto-save form progress
        this.enableAutoSave();
        
        // Smart defaults
        this.setSmartDefaults();
        
        // Progress indicators
        this.setupProgressIndicators();
        
        // Quick actions
        this.setupQuickActions();
        
        // Contextual help
        this.setupContextualHelp();
        
        // Smooth transitions
        this.enableSmoothTransitions();
        
        // Track user behavior
        this.trackUserBehavior();
    }
    
    // Auto-save form data to prevent loss
    enableAutoSave() {
        const forms = document.querySelectorAll('form[data-autosave="true"]');
        
        forms.forEach(form => {
            const formId = form.id || form.dataset.formName;
            let saveTimeout;
            
            form.addEventListener('input', (e) => {
                clearTimeout(saveTimeout);
                saveTimeout = setTimeout(() => {
                    this.saveFormData(formId, form);
                    this.showAutoSaveIndicator(form);
                }, 1000);
            });
            
            // Restore saved data on load
            this.restoreFormData(formId, form);
        });
    }
    
    saveFormData(formId, form) {
        const formData = new FormData(form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        
        localStorage.setItem(`cibozer_form_${formId}`, JSON.stringify({
            data: data,
            timestamp: Date.now()
        }));
    }
    
    restoreFormData(formId, form) {
        const saved = localStorage.getItem(`cibozer_form_${formId}`);
        if (!saved) return;
        
        const { data, timestamp } = JSON.parse(saved);
        
        // Only restore if less than 24 hours old
        if (Date.now() - timestamp > 24 * 60 * 60 * 1000) {
            localStorage.removeItem(`cibozer_form_${formId}`);
            return;
        }
        
        // Show restoration option
        this.showRestoreOption(form, data, formId);
    }
    
    showRestoreOption(form, data, formId) {
        const notice = document.createElement('div');
        notice.className = 'alert alert-info alert-dismissible fade show';
        notice.innerHTML = `
            <strong>Unsaved data found!</strong> Would you like to restore your previous progress?
            <button type="button" class="btn btn-sm btn-primary ms-2" id="restore-data">Restore</button>
            <button type="button" class="btn btn-sm btn-secondary ms-1" id="discard-data">Discard</button>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        form.parentElement.insertBefore(notice, form);
        
        document.getElementById('restore-data')?.addEventListener('click', () => {
            Object.entries(data).forEach(([key, value]) => {
                const field = form.elements[key];
                if (field) {
                    field.value = value;
                    field.dispatchEvent(new Event('change'));
                }
            });
            notice.remove();
        });
        
        document.getElementById('discard-data')?.addEventListener('click', () => {
            localStorage.removeItem(`cibozer_form_${formId}`);
            notice.remove();
        });
    }
    
    showAutoSaveIndicator(form) {
        let indicator = form.querySelector('.autosave-indicator');
        
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'autosave-indicator';
            indicator.style.cssText = `
                position: absolute;
                top: 10px;
                right: 10px;
                background: #28a745;
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
                opacity: 0;
                transition: opacity 0.3s;
            `;
            form.style.position = 'relative';
            form.appendChild(indicator);
        }
        
        indicator.textContent = 'Saved';
        indicator.style.opacity = '1';
        
        setTimeout(() => {
            indicator.style.opacity = '0';
        }, 2000);
    }
    
    // Set smart defaults based on user history
    setSmartDefaults() {
        const dietTypeSelect = document.querySelector('select[name="diet_type"]');
        const caloriesInput = document.querySelector('input[name="calories"]');
        
        if (dietTypeSelect && this.userPreferences.lastDietType) {
            dietTypeSelect.value = this.userPreferences.lastDietType;
        }
        
        if (caloriesInput && this.userPreferences.lastCalories) {
            caloriesInput.value = this.userPreferences.lastCalories;
        }
        
        // Set meal count based on time of day
        const mealsSelect = document.querySelector('select[name="meals"]');
        if (mealsSelect) {
            const hour = new Date().getHours();
            if (hour < 10) {
                mealsSelect.value = '3'; // Full day ahead
            } else if (hour < 14) {
                mealsSelect.value = '2'; // Lunch and dinner
            } else {
                mealsSelect.value = '1'; // Just dinner
            }
        }
    }
    
    // Setup progress indicators
    setupProgressIndicators() {
        const multiStepForms = document.querySelectorAll('[data-multi-step="true"]');
        
        multiStepForms.forEach(form => {
            const steps = form.querySelectorAll('.form-step');
            if (steps.length <= 1) return;
            
            // Create progress bar
            const progressBar = document.createElement('div');
            progressBar.className = 'progress mb-4';
            progressBar.innerHTML = `
                <div class="progress-bar" role="progressbar" style="width: 0%"></div>
            `;
            
            // Create step indicators
            const stepIndicators = document.createElement('div');
            stepIndicators.className = 'd-flex justify-content-between mb-3';
            
            steps.forEach((step, index) => {
                const indicator = document.createElement('div');
                indicator.className = 'step-indicator';
                indicator.innerHTML = `
                    <div class="step-number ${index === 0 ? 'active' : ''}">${index + 1}</div>
                    <div class="step-label">${step.dataset.stepLabel || `Step ${index + 1}`}</div>
                `;
                stepIndicators.appendChild(indicator);
            });
            
            form.insertBefore(progressBar, form.firstChild);
            form.insertBefore(stepIndicators, progressBar.nextSibling);
            
            // Handle step navigation
            this.setupStepNavigation(form, steps, progressBar);
        });
    }
    
    setupStepNavigation(form, steps, progressBar) {
        let currentStep = 0;
        const totalSteps = steps.length;
        
        // Show only first step initially
        steps.forEach((step, index) => {
            step.style.display = index === 0 ? 'block' : 'none';
        });
        
        // Add navigation buttons
        steps.forEach((step, index) => {
            const nav = document.createElement('div');
            nav.className = 'd-flex justify-content-between mt-3';
            
            if (index > 0) {
                nav.innerHTML += `
                    <button type="button" class="btn btn-secondary previous-step">
                        <i class="fas fa-arrow-left me-2"></i>Previous
                    </button>
                `;
            } else {
                nav.innerHTML += '<div></div>';
            }
            
            if (index < totalSteps - 1) {
                nav.innerHTML += `
                    <button type="button" class="btn btn-primary next-step">
                        Next<i class="fas fa-arrow-right ms-2"></i>
                    </button>
                `;
            } else {
                nav.innerHTML += `
                    <button type="submit" class="btn btn-success">
                        <i class="fas fa-check me-2"></i>Complete
                    </button>
                `;
            }
            
            step.appendChild(nav);
        });
        
        // Handle navigation
        form.addEventListener('click', (e) => {
            if (e.target.closest('.next-step')) {
                e.preventDefault();
                if (this.validateStep(steps[currentStep])) {
                    this.goToStep(currentStep + 1, steps, progressBar);
                    currentStep++;
                }
            } else if (e.target.closest('.previous-step')) {
                e.preventDefault();
                this.goToStep(currentStep - 1, steps, progressBar);
                currentStep--;
            }
        });
    }
    
    validateStep(step) {
        const requiredFields = step.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                isValid = false;
                
                // Add error message if not exists
                if (!field.nextElementSibling?.classList.contains('invalid-feedback')) {
                    const error = document.createElement('div');
                    error.className = 'invalid-feedback';
                    error.textContent = 'This field is required';
                    field.parentElement.appendChild(error);
                }
            } else {
                field.classList.remove('is-invalid');
            }
        });
        
        if (!isValid) {
            // Scroll to first error
            const firstError = step.querySelector('.is-invalid');
            firstError?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        
        return isValid;
    }
    
    goToStep(stepIndex, steps, progressBar) {
        // Hide all steps
        steps.forEach(step => step.style.display = 'none');
        
        // Show target step
        steps[stepIndex].style.display = 'block';
        
        // Update progress
        const progress = ((stepIndex + 1) / steps.length) * 100;
        progressBar.querySelector('.progress-bar').style.width = `${progress}%`;
        
        // Update step indicators
        document.querySelectorAll('.step-number').forEach((indicator, index) => {
            indicator.classList.toggle('active', index <= stepIndex);
            indicator.classList.toggle('completed', index < stepIndex);
        });
        
        // Smooth scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    // Setup quick actions
    setupQuickActions() {
        // Quick calorie presets
        const caloriePresets = document.querySelector('.calorie-presets');
        if (caloriePresets) {
            const presets = [1200, 1500, 1800, 2000, 2500, 3000];
            
            presets.forEach(value => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'btn btn-outline-secondary btn-sm me-2 mb-2';
                btn.textContent = `${value} cal`;
                btn.addEventListener('click', () => {
                    const input = document.querySelector('input[name="calories"]');
                    if (input) {
                        input.value = value;
                        input.dispatchEvent(new Event('change'));
                    }
                });
                caloriePresets.appendChild(btn);
            });
        }
        
        // Quick diet templates
        this.setupDietTemplates();
    }
    
    setupDietTemplates() {
        const templates = {
            'weight-loss': {
                calories: 1500,
                meals: 3,
                preferences: ['low-carb', 'high-protein']
            },
            'muscle-gain': {
                calories: 2800,
                meals: 5,
                preferences: ['high-protein', 'balanced']
            },
            'maintenance': {
                calories: 2000,
                meals: 3,
                preferences: ['balanced']
            }
        };
        
        const templateContainer = document.querySelector('.diet-templates');
        if (!templateContainer) return;
        
        Object.entries(templates).forEach(([key, config]) => {
            const card = document.createElement('div');
            card.className = 'template-card';
            card.innerHTML = `
                <h6>${key.replace('-', ' ').toUpperCase()}</h6>
                <p class="text-muted small">${config.calories} cal, ${config.meals} meals</p>
                <button type="button" class="btn btn-sm btn-primary use-template" data-template="${key}">
                    Use Template
                </button>
            `;
            
            card.querySelector('.use-template').addEventListener('click', () => {
                this.applyTemplate(config);
            });
            
            templateContainer.appendChild(card);
        });
    }
    
    applyTemplate(config) {
        Object.entries(config).forEach(([key, value]) => {
            const field = document.querySelector(`[name="${key}"]`);
            if (field) {
                field.value = value;
                field.dispatchEvent(new Event('change'));
            }
        });
        
        // Show success message
        this.showNotification('Template applied successfully!', 'success');
    }
    
    // Contextual help
    setupContextualHelp() {
        const helpTriggers = document.querySelectorAll('[data-help]');
        
        helpTriggers.forEach(trigger => {
            const helpText = trigger.dataset.help;
            
            // Add help icon
            const icon = document.createElement('i');
            icon.className = 'fas fa-question-circle text-muted ms-1';
            icon.style.cursor = 'help';
            trigger.appendChild(icon);
            
            // Create tooltip
            icon.addEventListener('mouseenter', (e) => {
                this.showTooltip(e.target, helpText);
            });
            
            icon.addEventListener('mouseleave', () => {
                this.hideTooltip();
            });
        });
    }
    
    showTooltip(target, text) {
        const tooltip = document.createElement('div');
        tooltip.className = 'custom-tooltip';
        tooltip.textContent = text;
        tooltip.style.cssText = `
            position: absolute;
            background: #333;
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 14px;
            max-width: 250px;
            z-index: 1000;
            pointer-events: none;
        `;
        
        document.body.appendChild(tooltip);
        
        const rect = target.getBoundingClientRect();
        tooltip.style.top = `${rect.top - tooltip.offsetHeight - 5}px`;
        tooltip.style.left = `${rect.left + rect.width/2 - tooltip.offsetWidth/2}px`;
        
        this.currentTooltip = tooltip;
    }
    
    hideTooltip() {
        if (this.currentTooltip) {
            this.currentTooltip.remove();
            this.currentTooltip = null;
        }
    }
    
    // Smooth transitions
    enableSmoothTransitions() {
        // Page transitions
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href^="/"]');
            if (link && !link.target && !e.ctrlKey && !e.metaKey) {
                e.preventDefault();
                this.smoothNavigate(link.href);
            }
        });
    }
    
    smoothNavigate(url) {
        // Add loading overlay
        const overlay = document.createElement('div');
        overlay.className = 'page-transition-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255,255,255,0.9);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.3s;
        `;
        overlay.innerHTML = '<div class="spinner-border text-primary"></div>';
        
        document.body.appendChild(overlay);
        setTimeout(() => overlay.style.opacity = '1', 10);
        
        // Navigate after animation
        setTimeout(() => {
            window.location.href = url;
        }, 300);
    }
    
    // Track user behavior
    trackUserBehavior() {
        // Track form abandonment
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            let hasInteracted = false;
            
            form.addEventListener('input', () => {
                hasInteracted = true;
            });
            
            window.addEventListener('beforeunload', (e) => {
                if (hasInteracted && !form.dataset.submitted) {
                    this.analytics.abandonmentPoints.push({
                        form: form.id || form.action,
                        timestamp: Date.now()
                    });
                }
            });
            
            form.addEventListener('submit', () => {
                form.dataset.submitted = 'true';
            });
        });
        
        // Track interaction patterns
        document.addEventListener('click', (e) => {
            this.analytics.interactions.push({
                element: e.target.tagName,
                className: e.target.className,
                timestamp: Date.now()
            });
        });
    }
    
    // User preferences
    loadUserPreferences() {
        const saved = localStorage.getItem('cibozer_user_preferences');
        return saved ? JSON.parse(saved) : {};
    }
    
    saveUserPreferences(preferences) {
        localStorage.setItem('cibozer_user_preferences', JSON.stringify({
            ...this.userPreferences,
            ...preferences,
            lastUpdated: Date.now()
        }));
    }
    
    // Utility functions
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 150);
        }, 5000);
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.userFlowOptimizer = new UserFlowOptimizer();
});
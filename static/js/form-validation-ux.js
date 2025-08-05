/**
 * Enhanced Form Validation and UX
 * Provides real-time validation with helpful feedback
 */

class FormValidationUX {
    constructor() {
        this.validators = this.setupValidators();
        this.validationCache = new Map();
        this.init();
    }
    
    init() {
        // Setup form validation
        this.enhanceAllForms();
        
        // Setup field validators
        this.setupFieldValidation();
        
        // Setup password strength meter
        this.setupPasswordStrength();
        
        // Setup email validation
        this.setupEmailValidation();
        
        // Setup numeric input helpers
        this.setupNumericInputs();
        
        // Setup date/time helpers
        this.setupDateTimeInputs();
        
        // Setup form progress tracking
        this.setupFormProgress();
    }
    
    setupValidators() {
        return {
            email: {
                pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                message: 'Please enter a valid email address',
                suggestions: ['Check for typos', 'Ensure format is name@example.com']
            },
            password: {
                minLength: 8,
                patterns: [
                    { regex: /[a-z]/, message: 'Include at least one lowercase letter' },
                    { regex: /[A-Z]/, message: 'Include at least one uppercase letter' },
                    { regex: /[0-9]/, message: 'Include at least one number' },
                    { regex: /[!@#$%^&*]/, message: 'Include at least one special character' }
                ],
                strength: {
                    weak: { score: 0, color: '#dc3545', text: 'Weak' },
                    fair: { score: 1, color: '#ffc107', text: 'Fair' },
                    good: { score: 2, color: '#28a745', text: 'Good' },
                    strong: { score: 3, color: '#007bff', text: 'Strong' }
                }
            },
            phone: {
                patterns: [
                    /^\d{10}$/,
                    /^\(\d{3}\) \d{3}-\d{4}$/,
                    /^\d{3}-\d{3}-\d{4}$/,
                    /^\+1 \d{3}-\d{3}-\d{4}$/
                ],
                formatter: (value) => {
                    const cleaned = value.replace(/\D/g, '');
                    if (cleaned.length === 10) {
                        return `(${cleaned.slice(0,3)}) ${cleaned.slice(3,6)}-${cleaned.slice(6)}`;
                    }
                    return value;
                }
            },
            calories: {
                min: 1200,
                max: 5000,
                step: 50,
                message: 'Calories should be between 1200 and 5000',
                suggestions: [
                    'Most adults need 1500-2500 calories',
                    'Consider your activity level',
                    'Consult a nutritionist for personalized advice'
                ]
            },
            creditCard: {
                patterns: {
                    visa: /^4[0-9]{12}(?:[0-9]{3})?$/,
                    mastercard: /^5[1-5][0-9]{14}$/,
                    amex: /^3[47][0-9]{13}$/,
                    discover: /^6(?:011|5[0-9]{2})[0-9]{12}$/
                },
                formatter: (value) => {
                    return value.replace(/\s/g, '').replace(/(.{4})/g, '$1 ').trim();
                }
            }
        };
    }
    
    enhanceAllForms() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            // Add novalidate to use custom validation
            form.setAttribute('novalidate', true);
            
            // Track form state
            form.dataset.touched = 'false';
            
            // Add submit handler
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                
                if (this.validateForm(form)) {
                    this.handleFormSubmit(form);
                } else {
                    this.showFormErrors(form);
                }
            });
            
            // Add change handler for form-level validation
            form.addEventListener('change', () => {
                form.dataset.touched = 'true';
                this.updateFormProgress(form);
            });
        });
    }
    
    setupFieldValidation() {
        // Real-time validation on blur
        document.addEventListener('blur', (e) => {
            if (e.target.matches('input, select, textarea')) {
                this.validateField(e.target);
            }
        }, true);
        
        // Clear errors on input
        document.addEventListener('input', (e) => {
            const field = e.target;
            if (field.matches('input, textarea')) {
                this.clearFieldError(field);
                
                // Show success for valid fields
                if (field.value && this.isFieldValid(field)) {
                    this.showFieldSuccess(field);
                }
                
                // Update character count if applicable
                this.updateCharacterCount(field);
            }
        });
        
        // Format on input for specific fields
        document.addEventListener('input', (e) => {
            const field = e.target;
            
            // Phone formatting
            if (field.type === 'tel' || field.name === 'phone') {
                field.value = this.validators.phone.formatter(field.value);
            }
            
            // Credit card formatting
            if (field.name === 'creditCard' || field.dataset.creditCard) {
                field.value = this.validators.creditCard.formatter(field.value);
                this.detectCardType(field);
            }
        });
    }
    
    validateField(field) {
        if (!field.value && !field.required) return true;
        
        const validationResult = this.getFieldValidation(field);
        
        if (validationResult.isValid) {
            this.showFieldSuccess(field);
        } else {
            this.showFieldError(field, validationResult.message, validationResult.suggestions);
        }
        
        return validationResult.isValid;
    }
    
    getFieldValidation(field) {
        const value = field.value.trim();
        const type = field.type;
        const name = field.name;
        
        // Required field check
        if (field.required && !value) {
            return {
                isValid: false,
                message: 'This field is required',
                suggestions: []
            };
        }
        
        // Email validation
        if (type === 'email' || name === 'email') {
            const isValid = this.validators.email.pattern.test(value);
            return {
                isValid,
                message: this.validators.email.message,
                suggestions: isValid ? [] : this.validators.email.suggestions
            };
        }
        
        // Password validation
        if (type === 'password' || name === 'password') {
            return this.validatePassword(value);
        }
        
        // Numeric validation
        if (type === 'number' || field.dataset.numeric) {
            return this.validateNumeric(field, value);
        }
        
        // Pattern validation
        if (field.pattern) {
            const pattern = new RegExp(field.pattern);
            const isValid = pattern.test(value);
            return {
                isValid,
                message: field.dataset.patternError || 'Please match the required format',
                suggestions: []
            };
        }
        
        // Length validation
        if (field.minLength || field.maxLength) {
            return this.validateLength(field, value);
        }
        
        return { isValid: true, message: '', suggestions: [] };
    }
    
    validatePassword(password) {
        const issues = [];
        
        if (password.length < this.validators.password.minLength) {
            issues.push(`At least ${this.validators.password.minLength} characters`);
        }
        
        this.validators.password.patterns.forEach(({ regex, message }) => {
            if (!regex.test(password)) {
                issues.push(message);
            }
        });
        
        return {
            isValid: issues.length === 0,
            message: issues.length ? 'Password requirements:' : 'Password is strong',
            suggestions: issues
        };
    }
    
    validateNumeric(field, value) {
        const num = parseFloat(value);
        const min = parseFloat(field.min);
        const max = parseFloat(field.max);
        
        if (isNaN(num)) {
            return {
                isValid: false,
                message: 'Please enter a valid number',
                suggestions: []
            };
        }
        
        if (!isNaN(min) && num < min) {
            return {
                isValid: false,
                message: `Value must be at least ${min}`,
                suggestions: field.dataset.suggestions ? JSON.parse(field.dataset.suggestions) : []
            };
        }
        
        if (!isNaN(max) && num > max) {
            return {
                isValid: false,
                message: `Value must be no more than ${max}`,
                suggestions: field.dataset.suggestions ? JSON.parse(field.dataset.suggestions) : []
            };
        }
        
        return { isValid: true, message: '', suggestions: [] };
    }
    
    validateLength(field, value) {
        const minLength = parseInt(field.minLength);
        const maxLength = parseInt(field.maxLength);
        
        if (minLength && value.length < minLength) {
            return {
                isValid: false,
                message: `At least ${minLength} characters required`,
                suggestions: [`You've entered ${value.length} characters`]
            };
        }
        
        if (maxLength && value.length > maxLength) {
            return {
                isValid: false,
                message: `Maximum ${maxLength} characters allowed`,
                suggestions: [`You've entered ${value.length} characters`]
            };
        }
        
        return { isValid: true, message: '', suggestions: [] };
    }
    
    showFieldError(field, message, suggestions = []) {
        field.classList.add('is-invalid');
        field.classList.remove('is-valid');
        
        // Remove existing feedback
        this.removeFieldFeedback(field);
        
        // Create error message
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback d-block animated fadeIn';
        feedback.innerHTML = `
            <i class="fas fa-exclamation-circle me-1"></i>
            <span>${message}</span>
            ${suggestions.length ? `
                <ul class="mb-0 mt-1">
                    ${suggestions.map(s => `<li>${s}</li>`).join('')}
                </ul>
            ` : ''}
        `;
        
        field.parentElement.appendChild(feedback);
        
        // Add shake animation to field
        field.classList.add('shake');
        setTimeout(() => field.classList.remove('shake'), 500);
    }
    
    showFieldSuccess(field) {
        field.classList.add('is-valid');
        field.classList.remove('is-invalid');
        
        // Remove existing feedback
        this.removeFieldFeedback(field);
        
        // Add success icon
        const feedback = document.createElement('div');
        feedback.className = 'valid-feedback d-block animated fadeIn';
        feedback.innerHTML = '<i class="fas fa-check-circle me-1"></i> Looks good!';
        
        field.parentElement.appendChild(feedback);
    }
    
    clearFieldError(field) {
        field.classList.remove('is-invalid', 'is-valid');
        this.removeFieldFeedback(field);
    }
    
    removeFieldFeedback(field) {
        const feedback = field.parentElement.querySelector('.invalid-feedback, .valid-feedback');
        if (feedback) {
            feedback.classList.add('fadeOut');
            setTimeout(() => feedback.remove(), 300);
        }
    }
    
    isFieldValid(field) {
        return this.getFieldValidation(field).isValid;
    }
    
    setupPasswordStrength() {
        const passwordFields = document.querySelectorAll('input[type="password"]');
        
        passwordFields.forEach(field => {
            // Skip confirmation fields
            if (field.name === 'confirmPassword' || field.name === 'password_confirm') return;
            
            // Create strength meter
            const meter = document.createElement('div');
            meter.className = 'password-strength-meter mt-2';
            meter.innerHTML = `
                <div class="progress" style="height: 5px;">
                    <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                </div>
                <small class="text-muted">Password strength: <span class="strength-text">-</span></small>
            `;
            
            field.parentElement.appendChild(meter);
            
            // Update on input
            field.addEventListener('input', () => {
                this.updatePasswordStrength(field, meter);
            });
        });
    }
    
    updatePasswordStrength(field, meter) {
        const password = field.value;
        let score = 0;
        
        // Length score
        if (password.length >= 8) score++;
        if (password.length >= 12) score++;
        
        // Pattern scores
        if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++;
        if (/[0-9]/.test(password)) score++;
        if (/[!@#$%^&*]/.test(password)) score++;
        
        // Determine strength level
        let strength;
        if (score <= 2) strength = this.validators.password.strength.weak;
        else if (score <= 3) strength = this.validators.password.strength.fair;
        else if (score <= 4) strength = this.validators.password.strength.good;
        else strength = this.validators.password.strength.strong;
        
        // Update meter
        const progressBar = meter.querySelector('.progress-bar');
        const strengthText = meter.querySelector('.strength-text');
        
        progressBar.style.width = `${(score / 5) * 100}%`;
        progressBar.style.backgroundColor = strength.color;
        strengthText.textContent = strength.text;
        strengthText.style.color = strength.color;
    }
    
    setupEmailValidation() {
        const emailFields = document.querySelectorAll('input[type="email"]');
        
        emailFields.forEach(field => {
            // Add debounced validation
            let timeout;
            field.addEventListener('input', () => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    if (field.value && this.validators.email.pattern.test(field.value)) {
                        this.checkEmailAvailability(field);
                    }
                }, 500);
            });
        });
    }
    
    async checkEmailAvailability(field) {
        // Skip if not a registration form
        if (!field.closest('form').querySelector('[name="password"]')) return;
        
        const email = field.value;
        
        // Show checking indicator
        const indicator = document.createElement('div');
        indicator.className = 'email-check-indicator';
        indicator.innerHTML = '<small class="text-muted"><i class="fas fa-spinner fa-spin me-1"></i>Checking availability...</small>';
        
        this.removeFieldFeedback(field);
        field.parentElement.appendChild(indicator);
        
        try {
            // Simulate API check (replace with actual endpoint)
            const response = await fetch('/api/check-email', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            
            const data = await response.json();
            
            indicator.remove();
            
            if (data.available) {
                this.showFieldSuccess(field);
            } else {
                this.showFieldError(field, 'This email is already registered', [
                    'Try logging in instead',
                    'Use a different email address'
                ]);
            }
        } catch (error) {
            indicator.remove();
        }
    }
    
    setupNumericInputs() {
        const numericInputs = document.querySelectorAll('input[type="number"]');
        
        numericInputs.forEach(input => {
            // Add increment/decrement buttons
            const wrapper = document.createElement('div');
            wrapper.className = 'numeric-input-wrapper';
            
            const decrementBtn = document.createElement('button');
            decrementBtn.type = 'button';
            decrementBtn.className = 'btn btn-sm btn-outline-secondary numeric-decrement';
            decrementBtn.innerHTML = '<i class="fas fa-minus"></i>';
            
            const incrementBtn = document.createElement('button');
            incrementBtn.type = 'button';
            incrementBtn.className = 'btn btn-sm btn-outline-secondary numeric-increment';
            incrementBtn.innerHTML = '<i class="fas fa-plus"></i>';
            
            input.parentNode.insertBefore(wrapper, input);
            wrapper.appendChild(decrementBtn);
            wrapper.appendChild(input);
            wrapper.appendChild(incrementBtn);
            
            // Handle clicks
            decrementBtn.addEventListener('click', () => {
                const step = parseFloat(input.step) || 1;
                const min = parseFloat(input.min);
                const current = parseFloat(input.value) || 0;
                const newValue = current - step;
                
                if (isNaN(min) || newValue >= min) {
                    input.value = newValue;
                    input.dispatchEvent(new Event('input'));
                }
            });
            
            incrementBtn.addEventListener('click', () => {
                const step = parseFloat(input.step) || 1;
                const max = parseFloat(input.max);
                const current = parseFloat(input.value) || 0;
                const newValue = current + step;
                
                if (isNaN(max) || newValue <= max) {
                    input.value = newValue;
                    input.dispatchEvent(new Event('input'));
                }
            });
        });
    }
    
    setupDateTimeInputs() {
        // Enhance date inputs with calendar widget
        const dateInputs = document.querySelectorAll('input[type="date"]');
        
        dateInputs.forEach(input => {
            // Add calendar icon
            const icon = document.createElement('i');
            icon.className = 'fas fa-calendar-alt date-icon';
            icon.style.cssText = 'position: absolute; right: 10px; top: 50%; transform: translateY(-50%); pointer-events: none;';
            
            input.style.paddingRight = '35px';
            input.parentElement.style.position = 'relative';
            input.parentElement.appendChild(icon);
        });
    }
    
    updateCharacterCount(field) {
        if (!field.maxLength) return;
        
        let counter = field.parentElement.querySelector('.character-counter');
        
        if (!counter) {
            counter = document.createElement('small');
            counter.className = 'character-counter text-muted';
            field.parentElement.appendChild(counter);
        }
        
        const remaining = field.maxLength - field.value.length;
        counter.textContent = `${remaining} characters remaining`;
        
        if (remaining < 10) {
            counter.classList.add('text-danger');
            counter.classList.remove('text-muted');
        } else {
            counter.classList.add('text-muted');
            counter.classList.remove('text-danger');
        }
    }
    
    setupFormProgress() {
        const forms = document.querySelectorAll('form[data-show-progress="true"]');
        
        forms.forEach(form => {
            const progress = document.createElement('div');
            progress.className = 'form-progress mb-3';
            progress.innerHTML = `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <small class="text-muted">Form Progress</small>
                    <small class="text-muted progress-percentage">0%</small>
                </div>
                <div class="progress" style="height: 5px;">
                    <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                </div>
            `;
            
            form.insertBefore(progress, form.firstChild);
            
            // Update on change
            form.addEventListener('change', () => {
                this.updateFormProgress(form);
            });
        });
    }
    
    updateFormProgress(form) {
        const progress = form.querySelector('.form-progress');
        if (!progress) return;
        
        const fields = form.querySelectorAll('input, select, textarea');
        const requiredFields = Array.from(fields).filter(f => f.required);
        const filledFields = requiredFields.filter(f => f.value.trim());
        
        const percentage = Math.round((filledFields.length / requiredFields.length) * 100);
        
        progress.querySelector('.progress-bar').style.width = `${percentage}%`;
        progress.querySelector('.progress-percentage').textContent = `${percentage}%`;
        
        if (percentage === 100) {
            progress.querySelector('.progress-bar').classList.add('bg-success');
        }
    }
    
    validateForm(form) {
        const fields = form.querySelectorAll('input, select, textarea');
        let isValid = true;
        let firstError = null;
        
        fields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
                if (!firstError) firstError = field;
            }
        });
        
        if (firstError) {
            firstError.focus();
            firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        
        return isValid;
    }
    
    showFormErrors(form) {
        // Show general error message
        let alert = form.querySelector('.form-error-alert');
        
        if (!alert) {
            alert = document.createElement('div');
            alert.className = 'alert alert-danger alert-dismissible fade show form-error-alert';
            alert.innerHTML = `
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Please fix the errors below</strong>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            form.insertBefore(alert, form.firstChild);
        }
        
        // Scroll to alert
        alert.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    
    handleFormSubmit(form) {
        // Show loading state
        const submitBtn = form.querySelector('[type="submit"]');
        const originalText = submitBtn.innerHTML;
        
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
        
        // Actually submit the form
        form.submit();
    }
    
    detectCardType(field) {
        const value = field.value.replace(/\s/g, '');
        let cardType = null;
        
        if (/^4/.test(value)) cardType = 'visa';
        else if (/^5[1-5]/.test(value)) cardType = 'mastercard';
        else if (/^3[47]/.test(value)) cardType = 'amex';
        else if (/^6(?:011|5)/.test(value)) cardType = 'discover';
        
        // Update card icon
        let icon = field.parentElement.querySelector('.card-type-icon');
        
        if (!icon && cardType) {
            icon = document.createElement('i');
            icon.className = 'card-type-icon';
            icon.style.cssText = 'position: absolute; right: 10px; top: 50%; transform: translateY(-50%);';
            field.parentElement.style.position = 'relative';
            field.parentElement.appendChild(icon);
        }
        
        if (icon && cardType) {
            icon.className = `fab fa-cc-${cardType} card-type-icon`;
        } else if (icon && !cardType) {
            icon.remove();
        }
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.formValidationUX = new FormValidationUX();
});

// Add CSS for animations and styling
const style = document.createElement('style');
style.textContent = `
    /* Form validation animations */
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
    
    .shake {
        animation: shake 0.5s ease-in-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes fadeOut {
        from { opacity: 1; transform: translateY(0); }
        to { opacity: 0; transform: translateY(-10px); }
    }
    
    .animated.fadeIn {
        animation: fadeIn 0.3s ease-in;
    }
    
    .animated.fadeOut {
        animation: fadeOut 0.3s ease-out;
    }
    
    /* Numeric input wrapper */
    .numeric-input-wrapper {
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }
    
    .numeric-input-wrapper input[type="number"] {
        text-align: center;
        -moz-appearance: textfield;
    }
    
    .numeric-input-wrapper input[type="number"]::-webkit-outer-spin-button,
    .numeric-input-wrapper input[type="number"]::-webkit-inner-spin-button {
        -webkit-appearance: none;
        margin: 0;
    }
    
    /* Password strength meter */
    .password-strength-meter {
        margin-top: 0.5rem;
    }
    
    /* Character counter */
    .character-counter {
        display: block;
        margin-top: 0.25rem;
        font-size: 0.875rem;
    }
    
    /* Form progress */
    .form-progress {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1.5rem;
    }
    
    /* Card type icon */
    .card-type-icon {
        font-size: 1.5rem;
        color: #6c757d;
    }
    
    .fab.fa-cc-visa { color: #1a1f71; }
    .fab.fa-cc-mastercard { color: #eb001b; }
    .fab.fa-cc-amex { color: #006fcf; }
    .fab.fa-cc-discover { color: #ff6000; }
`;
document.head.appendChild(style);
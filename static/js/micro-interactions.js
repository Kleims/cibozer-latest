/**
 * Micro-interactions and Animations for Cibozer
 * Provides delightful user feedback and smooth transitions
 */

class MicroInteractions {
    constructor() {
        this.prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        this.activeAnimations = new Set();
        this.init();
    }
    
    init() {
        // Button interactions
        this.setupButtonInteractions();
        
        // Card interactions
        this.setupCardInteractions();
        
        // Form interactions
        this.setupFormInteractions();
        
        // Navigation interactions
        this.setupNavigationInteractions();
        
        // Success animations
        this.setupSuccessAnimations();
        
        // Copy feedback
        this.setupCopyFeedback();
        
        // Hover effects
        this.setupHoverEffects();
        
        // Page transitions
        this.setupPageTransitions();
        
        // Scroll animations
        this.setupScrollAnimations();
        
        // Confetti for special moments
        this.setupConfetti();
    }
    
    setupButtonInteractions() {
        // Ripple effect on click
        document.addEventListener('click', (e) => {
            const button = e.target.closest('.btn, button');
            if (!button || this.prefersReducedMotion) return;
            
            this.createRipple(button, e);
        });
        
        // Hover lift effect
        const buttons = document.querySelectorAll('.btn, button');
        buttons.forEach(button => {
            if (!button.classList.contains('btn-link')) {
                button.addEventListener('mouseenter', () => this.liftElement(button));
                button.addEventListener('mouseleave', () => this.dropElement(button));
            }
        });
        
        // Success state for submit buttons
        const submitButtons = document.querySelectorAll('[type="submit"]');
        submitButtons.forEach(button => {
            const form = button.closest('form');
            if (form) {
                form.addEventListener('submit', () => {
                    this.showButtonSuccess(button);
                });
            }
        });
    }
    
    createRipple(element, event) {
        const ripple = document.createElement('span');
        ripple.className = 'ripple';
        
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        
        element.style.position = 'relative';
        element.style.overflow = 'hidden';
        element.appendChild(ripple);
        
        ripple.addEventListener('animationend', () => {
            ripple.remove();
        });
    }
    
    liftElement(element) {
        if (this.prefersReducedMotion) return;
        
        element.style.transform = 'translateY(-2px)';
        element.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        element.style.transition = 'all 0.2s ease';
    }
    
    dropElement(element) {
        element.style.transform = 'translateY(0)';
        element.style.boxShadow = '';
    }
    
    showButtonSuccess(button) {
        if (this.prefersReducedMotion) return;
        
        const originalContent = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check animated-check"></i>';
        button.disabled = true;
        button.classList.add('btn-success');
        
        setTimeout(() => {
            button.innerHTML = originalContent;
            button.disabled = false;
            button.classList.remove('btn-success');
        }, 2000);
    }
    
    setupCardInteractions() {
        const cards = document.querySelectorAll('.card, .meal-card');
        
        cards.forEach(card => {
            // Hover tilt effect
            card.addEventListener('mousemove', (e) => this.tiltCard(card, e));
            card.addEventListener('mouseleave', () => this.resetCardTilt(card));
            
            // Click feedback
            card.addEventListener('click', () => this.pulseCard(card));
            
            // Focus glow
            if (card.tabIndex >= 0) {
                card.addEventListener('focus', () => this.glowElement(card));
                card.addEventListener('blur', () => this.removeGlow(card));
            }
        });
    }
    
    tiltCard(card, event) {
        if (this.prefersReducedMotion) return;
        
        const rect = card.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = (y - centerY) / 10;
        const rotateY = (centerX - x) / 10;
        
        card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.02)`;
        card.style.transition = 'transform 0.1s ease';
    }
    
    resetCardTilt(card) {
        card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale(1)';
    }
    
    pulseCard(card) {
        if (this.prefersReducedMotion) return;
        
        card.classList.add('pulse');
        setTimeout(() => card.classList.remove('pulse'), 600);
    }
    
    glowElement(element) {
        if (this.prefersReducedMotion) return;
        
        element.classList.add('glow');
    }
    
    removeGlow(element) {
        element.classList.remove('glow');
    }
    
    setupFormInteractions() {
        // Input focus animations
        const inputs = document.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            // Floating label effect
            const label = input.parentElement.querySelector('label');
            if (label && !input.placeholder) {
                this.setupFloatingLabel(input, label);
            }
            
            // Focus animations
            input.addEventListener('focus', () => this.animateInputFocus(input));
            input.addEventListener('blur', () => this.animateInputBlur(input));
            
            // Character count animation
            if (input.maxLength > 0) {
                input.addEventListener('input', () => this.animateCharacterCount(input));
            }
        });
        
        // Checkbox and radio animations
        const checkboxes = document.querySelectorAll('input[type="checkbox"], input[type="radio"]');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => this.animateCheckbox(checkbox));
        });
    }
    
    setupFloatingLabel(input, label) {
        input.addEventListener('focus', () => {
            label.classList.add('floating');
        });
        
        input.addEventListener('blur', () => {
            if (!input.value) {
                label.classList.remove('floating');
            }
        });
        
        // Check initial state
        if (input.value) {
            label.classList.add('floating');
        }
    }
    
    animateInputFocus(input) {
        if (this.prefersReducedMotion) return;
        
        const wrapper = input.parentElement;
        wrapper.classList.add('input-focused');
        
        // Animate underline
        const underline = wrapper.querySelector('.input-underline') || this.createUnderline(wrapper);
        underline.style.width = '100%';
    }
    
    animateInputBlur(input) {
        const wrapper = input.parentElement;
        wrapper.classList.remove('input-focused');
        
        const underline = wrapper.querySelector('.input-underline');
        if (underline && !input.value) {
            underline.style.width = '0';
        }
    }
    
    createUnderline(wrapper) {
        const underline = document.createElement('div');
        underline.className = 'input-underline';
        wrapper.appendChild(underline);
        return underline;
    }
    
    animateCharacterCount(input) {
        const counter = input.parentElement.querySelector('.character-counter');
        if (!counter) return;
        
        const remaining = input.maxLength - input.value.length;
        const percentage = (input.value.length / input.maxLength) * 100;
        
        if (percentage > 80) {
            counter.classList.add('warning');
            this.shakeElement(counter);
        } else {
            counter.classList.remove('warning');
        }
    }
    
    animateCheckbox(checkbox) {
        if (this.prefersReducedMotion) return;
        
        const label = checkbox.nextElementSibling;
        if (label) {
            if (checkbox.checked) {
                label.classList.add('bounce-in');
                setTimeout(() => label.classList.remove('bounce-in'), 400);
            }
        }
        
        // Create check animation
        if (checkbox.checked && checkbox.type === 'checkbox') {
            this.createCheckMark(checkbox);
        }
    }
    
    createCheckMark(checkbox) {
        const checkmark = document.createElement('span');
        checkmark.className = 'animated-checkmark';
        checkbox.parentElement.appendChild(checkmark);
        
        setTimeout(() => checkmark.remove(), 600);
    }
    
    setupNavigationInteractions() {
        // Active page indicator animation
        const currentPage = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-link');
        
        navLinks.forEach(link => {
            if (link.getAttribute('href') === currentPage) {
                link.classList.add('active');
                this.animateActiveIndicator(link);
            }
            
            // Hover animations
            link.addEventListener('mouseenter', () => this.animateNavHover(link));
            link.addEventListener('mouseleave', () => this.resetNavHover(link));
        });
        
        // Mobile menu animations
        const mobileToggle = document.querySelector('.navbar-toggler');
        if (mobileToggle) {
            mobileToggle.addEventListener('click', () => this.animateMobileMenu());
        }
    }
    
    animateActiveIndicator(link) {
        if (this.prefersReducedMotion) return;
        
        const indicator = document.createElement('span');
        indicator.className = 'active-indicator';
        link.appendChild(indicator);
        
        requestAnimationFrame(() => {
            indicator.style.width = '100%';
        });
    }
    
    animateNavHover(link) {
        if (this.prefersReducedMotion || link.classList.contains('active')) return;
        
        const hoverIndicator = document.createElement('span');
        hoverIndicator.className = 'hover-indicator';
        link.appendChild(hoverIndicator);
        
        requestAnimationFrame(() => {
            hoverIndicator.style.width = '100%';
        });
    }
    
    resetNavHover(link) {
        const hoverIndicator = link.querySelector('.hover-indicator');
        if (hoverIndicator) {
            hoverIndicator.style.width = '0';
            setTimeout(() => hoverIndicator.remove(), 300);
        }
    }
    
    animateMobileMenu() {
        const navbar = document.querySelector('.navbar-collapse');
        if (navbar) {
            navbar.classList.toggle('slide-in');
        }
    }
    
    setupSuccessAnimations() {
        // Listen for custom success events
        document.addEventListener('success', (e) => {
            const { target, message } = e.detail;
            this.showSuccessAnimation(target, message);
        });
        
        // Form submission success
        document.addEventListener('form-success', (e) => {
            this.showFormSuccess(e.target);
        });
    }
    
    showSuccessAnimation(element, message) {
        if (this.prefersReducedMotion) return;
        
        // Create success overlay
        const overlay = document.createElement('div');
        overlay.className = 'success-overlay';
        overlay.innerHTML = `
            <div class="success-content">
                <i class="fas fa-check-circle success-icon"></i>
                <p class="success-message">${message || 'Success!'}</p>
            </div>
        `;
        
        element.style.position = 'relative';
        element.appendChild(overlay);
        
        // Animate in
        requestAnimationFrame(() => {
            overlay.classList.add('show');
        });
        
        // Remove after animation
        setTimeout(() => {
            overlay.classList.remove('show');
            setTimeout(() => overlay.remove(), 300);
        }, 2000);
    }
    
    showFormSuccess(form) {
        if (this.prefersReducedMotion) return;
        
        // Animate all form fields
        const fields = form.querySelectorAll('input, textarea, select');
        fields.forEach((field, index) => {
            setTimeout(() => {
                field.classList.add('success-flash');
                setTimeout(() => field.classList.remove('success-flash'), 500);
            }, index * 50);
        });
        
        // Show success message
        this.showSuccessAnimation(form, 'Form submitted successfully!');
    }
    
    setupCopyFeedback() {
        // Add copy buttons to code blocks
        const codeBlocks = document.querySelectorAll('pre code');
        codeBlocks.forEach(block => {
            const copyBtn = document.createElement('button');
            copyBtn.className = 'copy-button';
            copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
            copyBtn.title = 'Copy to clipboard';
            
            block.parentElement.style.position = 'relative';
            block.parentElement.appendChild(copyBtn);
            
            copyBtn.addEventListener('click', () => this.copyToClipboard(block, copyBtn));
        });
        
        // Copy on click for specific elements
        const copyElements = document.querySelectorAll('[data-copy]');
        copyElements.forEach(element => {
            element.style.cursor = 'pointer';
            element.addEventListener('click', () => {
                this.copyToClipboard(element, element);
            });
        });
    }
    
    async copyToClipboard(element, button) {
        const text = element.dataset.copy || element.textContent;
        
        try {
            await navigator.clipboard.writeText(text);
            this.showCopySuccess(button);
        } catch (err) {
            this.showCopyError(button);
        }
    }
    
    showCopySuccess(button) {
        const originalContent = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check"></i>';
        button.classList.add('copy-success');
        
        // Particle effect
        this.createParticles(button, 'success');
        
        setTimeout(() => {
            button.innerHTML = originalContent;
            button.classList.remove('copy-success');
        }, 2000);
    }
    
    showCopyError(button) {
        button.classList.add('copy-error');
        this.shakeElement(button);
        
        setTimeout(() => {
            button.classList.remove('copy-error');
        }, 1000);
    }
    
    setupHoverEffects() {
        // Magnetic hover effect for icons
        const icons = document.querySelectorAll('.icon-magnetic');
        icons.forEach(icon => {
            icon.addEventListener('mousemove', (e) => this.magneticHover(icon, e));
            icon.addEventListener('mouseleave', () => this.resetMagnetic(icon));
        });
        
        // Gradient follow effect
        const gradientElements = document.querySelectorAll('[data-gradient-hover]');
        gradientElements.forEach(element => {
            element.addEventListener('mousemove', (e) => this.gradientFollow(element, e));
        });
    }
    
    magneticHover(element, event) {
        if (this.prefersReducedMotion) return;
        
        const rect = element.getBoundingClientRect();
        const x = event.clientX - rect.left - rect.width / 2;
        const y = event.clientY - rect.top - rect.height / 2;
        
        element.style.transform = `translate(${x * 0.3}px, ${y * 0.3}px)`;
        element.style.transition = 'transform 0.1s ease-out';
    }
    
    resetMagnetic(element) {
        element.style.transform = 'translate(0, 0)';
        element.style.transition = 'transform 0.3s ease-out';
    }
    
    gradientFollow(element, event) {
        if (this.prefersReducedMotion) return;
        
        const rect = element.getBoundingClientRect();
        const x = ((event.clientX - rect.left) / rect.width) * 100;
        const y = ((event.clientY - rect.top) / rect.height) * 100;
        
        element.style.background = `radial-gradient(circle at ${x}% ${y}%, rgba(46, 204, 113, 0.1), transparent)`;
    }
    
    setupPageTransitions() {
        // Animate page elements on load
        const animatedElements = document.querySelectorAll('[data-animate]');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.animateElement(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });
        
        animatedElements.forEach(element => {
            observer.observe(element);
        });
        
        // Smooth page transitions
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href^="/"]');
            if (link && !link.target && !e.ctrlKey && !e.metaKey) {
                e.preventDefault();
                this.smoothPageTransition(link.href);
            }
        });
    }
    
    animateElement(element) {
        if (this.prefersReducedMotion) return;
        
        const animation = element.dataset.animate;
        element.classList.add('animate-in', animation);
    }
    
    smoothPageTransition(url) {
        if (this.prefersReducedMotion) {
            window.location.href = url;
            return;
        }
        
        document.body.classList.add('page-exit');
        
        setTimeout(() => {
            window.location.href = url;
        }, 300);
    }
    
    setupScrollAnimations() {
        // Parallax scrolling
        const parallaxElements = document.querySelectorAll('[data-parallax]');
        
        window.addEventListener('scroll', () => {
            if (this.prefersReducedMotion) return;
            
            const scrolled = window.pageYOffset;
            
            parallaxElements.forEach(element => {
                const speed = element.dataset.parallax || 0.5;
                const yPos = -(scrolled * speed);
                element.style.transform = `translateY(${yPos}px)`;
            });
        });
        
        // Reveal on scroll
        const revealElements = document.querySelectorAll('.reveal-on-scroll');
        
        const revealObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');
                }
            });
        }, { threshold: 0.15 });
        
        revealElements.forEach(element => {
            revealObserver.observe(element);
        });
    }
    
    setupConfetti() {
        // Confetti for special achievements
        document.addEventListener('achievement', (e) => {
            this.launchConfetti(e.detail);
        });
        
        // First meal plan creation
        const generateBtn = document.querySelector('.generate-meal-plan');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => {
                const isFirstTime = !localStorage.getItem('has_generated_meal_plan');
                if (isFirstTime) {
                    setTimeout(() => {
                        this.launchConfetti({ message: 'First meal plan created!' });
                        localStorage.setItem('has_generated_meal_plan', 'true');
                    }, 2000);
                }
            });
        }
    }
    
    launchConfetti(options = {}) {
        if (this.prefersReducedMotion) return;
        
        const colors = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c', '#9b59b6'];
        const particleCount = options.particleCount || 100;
        
        for (let i = 0; i < particleCount; i++) {
            setTimeout(() => {
                this.createConfettiParticle(colors);
            }, i * 10);
        }
        
        if (options.message) {
            this.showAchievementMessage(options.message);
        }
    }
    
    createConfettiParticle(colors) {
        const particle = document.createElement('div');
        particle.className = 'confetti-particle';
        particle.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 3 + 's';
        particle.style.animationDuration = (Math.random() * 3 + 2) + 's';
        
        document.body.appendChild(particle);
        
        particle.addEventListener('animationend', () => {
            particle.remove();
        });
    }
    
    showAchievementMessage(message) {
        const achievement = document.createElement('div');
        achievement.className = 'achievement-message';
        achievement.innerHTML = `
            <i class="fas fa-trophy"></i>
            <span>${message}</span>
        `;
        
        document.body.appendChild(achievement);
        
        requestAnimationFrame(() => {
            achievement.classList.add('show');
        });
        
        setTimeout(() => {
            achievement.classList.remove('show');
            setTimeout(() => achievement.remove(), 500);
        }, 3000);
    }
    
    // Utility methods
    shakeElement(element) {
        if (this.prefersReducedMotion) return;
        
        element.classList.add('shake');
        setTimeout(() => element.classList.remove('shake'), 500);
    }
    
    createParticles(element, type = 'default') {
        if (this.prefersReducedMotion) return;
        
        const rect = element.getBoundingClientRect();
        const particleCount = 12;
        
        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('span');
            particle.className = `particle particle-${type}`;
            
            const angle = (360 / particleCount) * i;
            const velocity = 30 + Math.random() * 20;
            
            particle.style.left = rect.left + rect.width / 2 + 'px';
            particle.style.top = rect.top + rect.height / 2 + 'px';
            particle.style.setProperty('--angle', angle + 'deg');
            particle.style.setProperty('--velocity', velocity + 'px');
            
            document.body.appendChild(particle);
            
            particle.addEventListener('animationend', () => {
                particle.remove();
            });
        }
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.microInteractions = new MicroInteractions();
});

// Add CSS for micro-interactions
const style = document.createElement('style');
style.textContent = `
    /* Ripple Effect */
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.6);
        transform: scale(0);
        animation: ripple 0.6s ease-out;
        pointer-events: none;
    }
    
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    /* Pulse Animation */
    .pulse {
        animation: pulse 0.6s ease;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    /* Glow Effect */
    .glow {
        box-shadow: 0 0 20px rgba(46, 204, 113, 0.5);
        transition: box-shadow 0.3s ease;
    }
    
    /* Floating Label */
    label.floating {
        transform: translateY(-25px) scale(0.85);
        color: var(--primary-color);
        transition: all 0.3s ease;
    }
    
    /* Input Underline */
    .input-underline {
        position: absolute;
        bottom: 0;
        left: 0;
        height: 2px;
        width: 0;
        background: var(--primary-color);
        transition: width 0.3s ease;
    }
    
    .input-focused {
        transition: all 0.3s ease;
    }
    
    /* Animated Checkmark */
    .animated-checkmark {
        position: absolute;
        width: 20px;
        height: 20px;
        top: 50%;
        left: 10px;
        transform: translateY(-50%);
        pointer-events: none;
    }
    
    .animated-checkmark::after {
        content: '';
        position: absolute;
        width: 6px;
        height: 12px;
        border: solid var(--primary-color);
        border-width: 0 2px 2px 0;
        transform: rotate(45deg);
        animation: checkmark 0.3s ease;
    }
    
    @keyframes checkmark {
        0% {
            width: 0;
            height: 0;
        }
        50% {
            width: 6px;
            height: 0;
        }
        100% {
            width: 6px;
            height: 12px;
        }
    }
    
    /* Navigation Indicators */
    .active-indicator,
    .hover-indicator {
        position: absolute;
        bottom: 0;
        left: 0;
        height: 3px;
        width: 0;
        background: var(--primary-color);
        transition: width 0.3s ease;
    }
    
    .hover-indicator {
        background: rgba(46, 204, 113, 0.5);
    }
    
    /* Success Overlay */
    .success-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(46, 204, 113, 0.95);
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0;
        transform: scale(0.8);
        transition: all 0.3s ease;
        pointer-events: none;
        z-index: 10;
    }
    
    .success-overlay.show {
        opacity: 1;
        transform: scale(1);
    }
    
    .success-icon {
        font-size: 3rem;
        color: white;
        animation: successBounce 0.6s ease;
    }
    
    @keyframes successBounce {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.2); }
    }
    
    /* Copy Button */
    .copy-button {
        position: absolute;
        top: 5px;
        right: 5px;
        background: rgba(0, 0, 0, 0.1);
        border: none;
        padding: 5px 10px;
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .copy-button:hover {
        background: rgba(0, 0, 0, 0.2);
    }
    
    .copy-success {
        background: var(--primary-color);
        color: white;
    }
    
    /* Particles */
    .particle {
        position: fixed;
        width: 5px;
        height: 5px;
        border-radius: 50%;
        pointer-events: none;
        animation: particle-fly 0.6s ease-out forwards;
    }
    
    @keyframes particle-fly {
        to {
            transform: translate(
                calc(cos(var(--angle)) * var(--velocity)),
                calc(sin(var(--angle)) * var(--velocity))
            ) scale(0);
            opacity: 0;
        }
    }
    
    .particle-success {
        background: var(--primary-color);
    }
    
    /* Page Transitions */
    .page-exit {
        animation: pageExit 0.3s ease forwards;
    }
    
    @keyframes pageExit {
        to {
            opacity: 0;
            transform: translateY(-20px);
        }
    }
    
    /* Animate In */
    .animate-in {
        opacity: 0;
        animation: animateIn 0.6s ease forwards;
    }
    
    .fade-up {
        transform: translateY(30px);
    }
    
    .fade-left {
        transform: translateX(-30px);
    }
    
    .fade-right {
        transform: translateX(30px);
    }
    
    @keyframes animateIn {
        to {
            opacity: 1;
            transform: translate(0, 0);
        }
    }
    
    /* Reveal on Scroll */
    .reveal-on-scroll {
        opacity: 0;
        transform: translateY(20px);
        transition: all 0.6s ease;
    }
    
    .reveal-on-scroll.revealed {
        opacity: 1;
        transform: translateY(0);
    }
    
    /* Confetti */
    .confetti-particle {
        position: fixed;
        width: 10px;
        height: 10px;
        top: -10px;
        animation: confettiFall linear forwards;
        z-index: 9999;
    }
    
    @keyframes confettiFall {
        to {
            top: 100%;
            transform: rotate(360deg);
        }
    }
    
    /* Achievement Message */
    .achievement-message {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) scale(0.8);
        background: white;
        padding: 2rem 3rem;
        border-radius: 1rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        text-align: center;
        opacity: 0;
        transition: all 0.5s ease;
        z-index: 10000;
    }
    
    .achievement-message.show {
        opacity: 1;
        transform: translate(-50%, -50%) scale(1);
    }
    
    .achievement-message i {
        font-size: 3rem;
        color: #f39c12;
        display: block;
        margin-bottom: 1rem;
        animation: trophy 0.6s ease;
    }
    
    @keyframes trophy {
        0%, 100% { transform: rotate(0); }
        25% { transform: rotate(-10deg); }
        75% { transform: rotate(10deg); }
    }
    
    /* Shake Animation */
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
    
    .shake {
        animation: shake 0.5s ease;
    }
    
    /* Bounce In */
    .bounce-in {
        animation: bounceIn 0.4s ease;
    }
    
    @keyframes bounceIn {
        0% { transform: scale(0.3); opacity: 0; }
        50% { transform: scale(1.05); }
        70% { transform: scale(0.9); }
        100% { transform: scale(1); opacity: 1; }
    }
    
    /* Success Flash */
    .success-flash {
        animation: successFlash 0.5s ease;
    }
    
    @keyframes successFlash {
        0%, 100% { background-color: transparent; }
        50% { background-color: rgba(46, 204, 113, 0.1); }
    }
    
    /* Reduced Motion */
    @media (prefers-reduced-motion: reduce) {
        *,
        *::before,
        *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
    }
`;
document.head.appendChild(style);
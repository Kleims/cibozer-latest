/**
 * Tooltips and Onboarding System for Cibozer
 * Provides contextual help and user guidance
 */

class TooltipsOnboarding {
    constructor() {
        this.hasSeenOnboarding = localStorage.getItem('cibozer_onboarding_complete') === 'true';
        this.tooltipQueue = [];
        this.currentTour = null;
        this.init();
    }
    
    init() {
        // Setup tooltip system
        this.setupTooltips();
        
        // Setup onboarding tours
        this.setupOnboardingTours();
        
        // Setup contextual help
        this.setupContextualHelp();
        
        // Setup feature discovery
        this.setupFeatureDiscovery();
        
        // Setup interactive tutorials
        this.setupInteractiveTutorials();
        
        // Check if should show onboarding
        this.checkOnboarding();
    }
    
    setupTooltips() {
        // Find all elements with tooltip data
        const tooltipElements = document.querySelectorAll('[data-tooltip]');
        
        tooltipElements.forEach(element => {
            const tooltipConfig = {
                content: element.dataset.tooltip,
                position: element.dataset.tooltipPosition || 'top',
                trigger: element.dataset.tooltipTrigger || 'hover',
                delay: parseInt(element.dataset.tooltipDelay) || 0
            };
            
            this.attachTooltip(element, tooltipConfig);
        });
        
        // Setup dynamic tooltips
        this.setupDynamicTooltips();
    }
    
    attachTooltip(element, config) {
        let tooltipTimeout;
        let activeTooltip = null;
        
        const showTooltip = () => {
            if (activeTooltip) return;
            
            tooltipTimeout = setTimeout(() => {
                activeTooltip = this.createTooltip(element, config);
                this.positionTooltip(activeTooltip, element, config.position);
                
                // Animate in
                activeTooltip.style.opacity = '0';
                document.body.appendChild(activeTooltip);
                
                requestAnimationFrame(() => {
                    activeTooltip.style.transition = 'opacity 0.3s, transform 0.3s';
                    activeTooltip.style.opacity = '1';
                    activeTooltip.style.transform = 'scale(1)';
                });
            }, config.delay);
        };
        
        const hideTooltip = () => {
            clearTimeout(tooltipTimeout);
            
            if (activeTooltip) {
                activeTooltip.style.opacity = '0';
                activeTooltip.style.transform = 'scale(0.95)';
                
                setTimeout(() => {
                    activeTooltip?.remove();
                    activeTooltip = null;
                }, 300);
            }
        };
        
        // Attach event listeners based on trigger
        if (config.trigger === 'hover') {
            element.addEventListener('mouseenter', showTooltip);
            element.addEventListener('mouseleave', hideTooltip);
            element.addEventListener('focus', showTooltip);
            element.addEventListener('blur', hideTooltip);
        } else if (config.trigger === 'click') {
            element.addEventListener('click', (e) => {
                e.stopPropagation();
                if (activeTooltip) {
                    hideTooltip();
                } else {
                    showTooltip();
                }
            });
            
            // Close on outside click
            document.addEventListener('click', hideTooltip);
        } else if (config.trigger === 'focus') {
            element.addEventListener('focus', showTooltip);
            element.addEventListener('blur', hideTooltip);
        }
    }
    
    createTooltip(element, config) {
        const tooltip = document.createElement('div');
        tooltip.className = 'custom-tooltip';
        tooltip.setAttribute('role', 'tooltip');
        
        // Parse content for rich tooltips
        if (config.content.startsWith('{')) {
            const richConfig = JSON.parse(config.content);
            tooltip.innerHTML = this.createRichTooltipContent(richConfig);
        } else {
            tooltip.textContent = config.content;
        }
        
        // Add arrow
        const arrow = document.createElement('div');
        arrow.className = `tooltip-arrow tooltip-arrow-${config.position}`;
        tooltip.appendChild(arrow);
        
        return tooltip;
    }
    
    createRichTooltipContent(config) {
        return `
            ${config.title ? `<h6 class="tooltip-title">${config.title}</h6>` : ''}
            ${config.description ? `<p class="tooltip-description">${config.description}</p>` : ''}
            ${config.list ? `
                <ul class="tooltip-list">
                    ${config.list.map(item => `<li>${item}</li>`).join('')}
                </ul>
            ` : ''}
            ${config.link ? `
                <a href="${config.link.url}" class="tooltip-link">
                    ${config.link.text} <i class="fas fa-external-link-alt ms-1"></i>
                </a>
            ` : ''}
        `;
    }
    
    positionTooltip(tooltip, element, position) {
        const rect = element.getBoundingClientRect();
        const tooltipRect = {
            width: tooltip.offsetWidth || 200,
            height: tooltip.offsetHeight || 50
        };
        
        let top, left;
        
        switch (position) {
            case 'top':
                top = rect.top - tooltipRect.height - 10;
                left = rect.left + rect.width / 2 - tooltipRect.width / 2;
                break;
            case 'bottom':
                top = rect.bottom + 10;
                left = rect.left + rect.width / 2 - tooltipRect.width / 2;
                break;
            case 'left':
                top = rect.top + rect.height / 2 - tooltipRect.height / 2;
                left = rect.left - tooltipRect.width - 10;
                break;
            case 'right':
                top = rect.top + rect.height / 2 - tooltipRect.height / 2;
                left = rect.right + 10;
                break;
        }
        
        // Ensure tooltip stays within viewport
        const margin = 10;
        left = Math.max(margin, Math.min(left, window.innerWidth - tooltipRect.width - margin));
        top = Math.max(margin, Math.min(top, window.innerHeight - tooltipRect.height - margin));
        
        tooltip.style.position = 'fixed';
        tooltip.style.top = `${top}px`;
        tooltip.style.left = `${left}px`;
        tooltip.style.transform = 'scale(0.95)';
    }
    
    setupDynamicTooltips() {
        // Calorie input helper
        const calorieInput = document.querySelector('input[name="calories"]');
        if (calorieInput && !calorieInput.dataset.tooltip) {
            calorieInput.dataset.tooltip = JSON.stringify({
                title: 'Daily Calorie Guide',
                description: 'Recommended daily intake:',
                list: [
                    'Sedentary: 1,600-2,400 calories',
                    'Moderately active: 2,000-2,800 calories',
                    'Very active: 2,400-3,200 calories'
                ]
            });
            this.attachTooltip(calorieInput, {
                content: calorieInput.dataset.tooltip,
                position: 'right',
                trigger: 'focus'
            });
        }
        
        // Diet type helper
        const dietSelect = document.querySelector('select[name="diet_type"]');
        if (dietSelect && !dietSelect.dataset.tooltip) {
            dietSelect.dataset.tooltip = 'Choose a diet that matches your lifestyle and health goals';
            this.attachTooltip(dietSelect, {
                content: dietSelect.dataset.tooltip,
                position: 'right',
                trigger: 'focus'
            });
        }
    }
    
    setupOnboardingTours() {
        this.tours = {
            firstVisit: {
                id: 'first-visit',
                name: 'Welcome to Cibozer',
                steps: [
                    {
                        element: '.navbar-brand',
                        title: 'Welcome to Cibozer!',
                        content: 'Your AI-powered meal planning assistant. Let\'s take a quick tour.',
                        position: 'bottom'
                    },
                    {
                        element: '#calories',
                        title: 'Set Your Calorie Goal',
                        content: 'Enter your daily calorie target. Not sure? We\'ll help you calculate it.',
                        position: 'right'
                    },
                    {
                        element: '#diet_type',
                        title: 'Choose Your Diet',
                        content: 'Select a diet type that matches your preferences and goals.',
                        position: 'right'
                    },
                    {
                        element: '#preferences',
                        title: 'Add Preferences',
                        content: 'Tell us what you like or dislike. We\'ll customize your meals accordingly.',
                        position: 'top'
                    },
                    {
                        element: '.generate-btn',
                        title: 'Generate Your Meal Plan',
                        content: 'Click here to create your personalized meal plan instantly!',
                        position: 'top'
                    }
                ]
            },
            
            premiumFeatures: {
                id: 'premium-features',
                name: 'Premium Features Tour',
                steps: [
                    {
                        element: '.pdf-export-btn',
                        title: 'Export to PDF',
                        content: 'Download your meal plans as beautiful PDF documents.',
                        position: 'left'
                    },
                    {
                        element: '.shopping-list-btn',
                        title: 'Shopping Lists',
                        content: 'Get organized shopping lists for all your meals.',
                        position: 'left'
                    },
                    {
                        element: '.meal-history',
                        title: 'Unlimited History',
                        content: 'Access all your past meal plans anytime.',
                        position: 'top'
                    }
                ]
            }
        };
    }
    
    checkOnboarding() {
        // Skip if already completed
        if (this.hasSeenOnboarding) return;
        
        // Check if on main page
        const isMainPage = window.location.pathname === '/' || window.location.pathname === '/create';
        if (!isMainPage) return;
        
        // Show welcome message
        setTimeout(() => {
            this.showWelcomeModal();
        }, 1000);
    }
    
    showWelcomeModal() {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header border-0">
                        <h5 class="modal-title">
                            <i class="fas fa-utensils text-primary me-2"></i>
                            Welcome to Cibozer!
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p class="lead">Create personalized meal plans in seconds with AI.</p>
                        <p>Would you like a quick tour to get started?</p>
                        
                        <div class="features-preview mt-4">
                            <div class="d-flex align-items-center mb-3">
                                <i class="fas fa-check-circle text-success me-3"></i>
                                <span>Customized to your dietary needs</span>
                            </div>
                            <div class="d-flex align-items-center mb-3">
                                <i class="fas fa-check-circle text-success me-3"></i>
                                <span>Detailed nutritional information</span>
                            </div>
                            <div class="d-flex align-items-center">
                                <i class="fas fa-check-circle text-success me-3"></i>
                                <span>Shopping lists and meal prep tips</span>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer border-0">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            Skip Tour
                        </button>
                        <button type="button" class="btn btn-primary" id="start-tour">
                            <i class="fas fa-play me-2"></i>Start Tour
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Handle tour start
        document.getElementById('start-tour')?.addEventListener('click', () => {
            bsModal.hide();
            setTimeout(() => {
                this.startTour('firstVisit');
            }, 500);
        });
        
        // Mark as seen
        modal.addEventListener('hidden.bs.modal', () => {
            localStorage.setItem('cibozer_onboarding_complete', 'true');
            modal.remove();
        });
    }
    
    startTour(tourId) {
        const tour = this.tours[tourId];
        if (!tour) return;
        
        this.currentTour = {
            ...tour,
            currentStep: 0
        };
        
        // Create tour overlay
        this.createTourOverlay();
        
        // Start first step
        this.showTourStep(0);
    }
    
    createTourOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'tour-overlay';
        overlay.innerHTML = `
            <div class="tour-controls">
                <button class="btn btn-sm btn-secondary tour-skip">Skip Tour</button>
                <div class="tour-progress">
                    <span class="tour-step-indicator">Step 1 of X</span>
                </div>
                <div class="tour-navigation">
                    <button class="btn btn-sm btn-outline-primary tour-prev">
                        <i class="fas fa-arrow-left"></i>
                    </button>
                    <button class="btn btn-sm btn-primary tour-next">
                        Next <i class="fas fa-arrow-right ms-1"></i>
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        // Event handlers
        overlay.querySelector('.tour-skip').addEventListener('click', () => {
            this.endTour();
        });
        
        overlay.querySelector('.tour-prev').addEventListener('click', () => {
            this.previousStep();
        });
        
        overlay.querySelector('.tour-next').addEventListener('click', () => {
            this.nextStep();
        });
        
        this.tourOverlay = overlay;
    }
    
    showTourStep(stepIndex) {
        const step = this.currentTour.steps[stepIndex];
        const element = document.querySelector(step.element);
        
        if (!element) {
            this.nextStep();
            return;
        }
        
        // Update controls
        this.updateTourControls(stepIndex);
        
        // Highlight element
        this.highlightElement(element);
        
        // Show tooltip
        this.showTourTooltip(element, step);
        
        // Scroll to element
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    
    highlightElement(element) {
        // Remove previous highlights
        document.querySelectorAll('.tour-highlight').forEach(el => {
            el.classList.remove('tour-highlight');
        });
        
        // Add highlight
        element.classList.add('tour-highlight');
        
        // Create spotlight effect
        const rect = element.getBoundingClientRect();
        const spotlight = document.createElement('div');
        spotlight.className = 'tour-spotlight';
        spotlight.style.cssText = `
            position: fixed;
            top: ${rect.top - 10}px;
            left: ${rect.left - 10}px;
            width: ${rect.width + 20}px;
            height: ${rect.height + 20}px;
            pointer-events: none;
            z-index: 9998;
        `;
        
        document.body.appendChild(spotlight);
        this.currentSpotlight = spotlight;
    }
    
    showTourTooltip(element, step) {
        // Remove previous tooltip
        this.currentTourTooltip?.remove();
        
        const tooltip = document.createElement('div');
        tooltip.className = 'tour-tooltip';
        tooltip.innerHTML = `
            <h5 class="tour-tooltip-title">${step.title}</h5>
            <p class="tour-tooltip-content">${step.content}</p>
        `;
        
        document.body.appendChild(tooltip);
        this.positionTooltip(tooltip, element, step.position);
        
        // Animate in
        tooltip.style.opacity = '0';
        tooltip.style.transform = 'scale(0.9)';
        
        requestAnimationFrame(() => {
            tooltip.style.transition = 'all 0.3s';
            tooltip.style.opacity = '1';
            tooltip.style.transform = 'scale(1)';
        });
        
        this.currentTourTooltip = tooltip;
    }
    
    updateTourControls(stepIndex) {
        const totalSteps = this.currentTour.steps.length;
        
        // Update step indicator
        this.tourOverlay.querySelector('.tour-step-indicator').textContent = 
            `Step ${stepIndex + 1} of ${totalSteps}`;
        
        // Update navigation buttons
        const prevBtn = this.tourOverlay.querySelector('.tour-prev');
        const nextBtn = this.tourOverlay.querySelector('.tour-next');
        
        prevBtn.disabled = stepIndex === 0;
        
        if (stepIndex === totalSteps - 1) {
            nextBtn.innerHTML = 'Finish <i class="fas fa-check ms-1"></i>';
        } else {
            nextBtn.innerHTML = 'Next <i class="fas fa-arrow-right ms-1"></i>';
        }
    }
    
    nextStep() {
        const currentStep = this.currentTour.currentStep;
        const totalSteps = this.currentTour.steps.length;
        
        if (currentStep < totalSteps - 1) {
            this.currentTour.currentStep++;
            this.showTourStep(this.currentTour.currentStep);
        } else {
            this.endTour();
        }
    }
    
    previousStep() {
        if (this.currentTour.currentStep > 0) {
            this.currentTour.currentStep--;
            this.showTourStep(this.currentTour.currentStep);
        }
    }
    
    endTour() {
        // Clean up
        this.tourOverlay?.remove();
        this.currentTourTooltip?.remove();
        this.currentSpotlight?.remove();
        
        document.querySelectorAll('.tour-highlight').forEach(el => {
            el.classList.remove('tour-highlight');
        });
        
        // Mark tour as completed
        localStorage.setItem(`tour_${this.currentTour.id}_complete`, 'true');
        
        // Show completion message
        this.showCompletionMessage();
        
        this.currentTour = null;
    }
    
    showCompletionMessage() {
        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-white bg-success border-0';
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-check-circle me-2"></i>
                    Tour completed! You're ready to start creating meal plans.
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
    
    setupContextualHelp() {
        // Add help buttons to complex features
        const complexFeatures = [
            { selector: '.macro-calculator', help: 'Calculate your ideal macro ratios' },
            { selector: '.meal-customizer', help: 'Customize individual meals' },
            { selector: '.nutrition-tracker', help: 'Track your daily nutrition' }
        ];
        
        complexFeatures.forEach(({ selector, help }) => {
            const element = document.querySelector(selector);
            if (!element) return;
            
            const helpBtn = document.createElement('button');
            helpBtn.className = 'btn btn-sm btn-link contextual-help-btn';
            helpBtn.innerHTML = '<i class="fas fa-question-circle"></i>';
            helpBtn.setAttribute('aria-label', 'Get help');
            
            element.appendChild(helpBtn);
            
            this.attachTooltip(helpBtn, {
                content: help,
                position: 'top',
                trigger: 'click'
            });
        });
    }
    
    setupFeatureDiscovery() {
        // Highlight new or underused features
        const features = [
            {
                element: '.advanced-filters',
                message: 'New! Try our advanced dietary filters',
                condition: () => !localStorage.getItem('used_advanced_filters')
            },
            {
                element: '.meal-swap',
                message: 'Tip: Click any meal to swap it with alternatives',
                condition: () => {
                    const swapCount = parseInt(localStorage.getItem('meal_swap_count') || '0');
                    return swapCount < 3;
                }
            }
        ];
        
        features.forEach(feature => {
            const element = document.querySelector(feature.element);
            if (!element || !feature.condition()) return;
            
            // Add discovery indicator
            const indicator = document.createElement('span');
            indicator.className = 'feature-discovery-indicator';
            indicator.innerHTML = '<i class="fas fa-sparkles"></i>';
            
            element.style.position = 'relative';
            element.appendChild(indicator);
            
            // Show tooltip on hover
            this.attachTooltip(indicator, {
                content: feature.message,
                position: 'top',
                trigger: 'hover',
                delay: 500
            });
        });
    }
    
    setupInteractiveTutorials() {
        // Add tutorial mode for complex workflows
        const tutorialTriggers = document.querySelectorAll('[data-tutorial]');
        
        tutorialTriggers.forEach(trigger => {
            const tutorialId = trigger.dataset.tutorial;
            
            trigger.addEventListener('click', (e) => {
                e.preventDefault();
                this.startInteractiveTutorial(tutorialId);
            });
        });
    }
    
    startInteractiveTutorial(tutorialId) {
        const tutorials = {
            mealCustomization: {
                title: 'Customizing Your Meals',
                steps: [
                    {
                        action: 'Click on any meal card',
                        validation: () => document.querySelector('.meal-card.selected')
                    },
                    {
                        action: 'Adjust portion sizes using the slider',
                        validation: () => document.querySelector('.portion-slider:changed')
                    },
                    {
                        action: 'Save your customization',
                        validation: () => document.querySelector('.save-customization.clicked')
                    }
                ]
            }
        };
        
        const tutorial = tutorials[tutorialId];
        if (!tutorial) return;
        
        // Show tutorial overlay
        this.showTutorialMode(tutorial);
    }
    
    showTutorialMode(tutorial) {
        const overlay = document.createElement('div');
        overlay.className = 'tutorial-mode-overlay';
        overlay.innerHTML = `
            <div class="tutorial-mode-header">
                <h5>${tutorial.title}</h5>
                <button class="btn btn-sm btn-secondary exit-tutorial">Exit Tutorial</button>
            </div>
            <div class="tutorial-mode-instruction">
                <i class="fas fa-hand-point-right me-2"></i>
                <span class="instruction-text">${tutorial.steps[0].action}</span>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        // Track tutorial progress
        let currentStep = 0;
        
        const checkProgress = () => {
            if (tutorial.steps[currentStep].validation()) {
                currentStep++;
                
                if (currentStep < tutorial.steps.length) {
                    overlay.querySelector('.instruction-text').textContent = 
                        tutorial.steps[currentStep].action;
                } else {
                    this.completeTutorial(overlay);
                }
            }
        };
        
        // Monitor for progress
        const observer = new MutationObserver(checkProgress);
        observer.observe(document.body, { childList: true, subtree: true });
        
        // Exit handler
        overlay.querySelector('.exit-tutorial').addEventListener('click', () => {
            observer.disconnect();
            overlay.remove();
        });
    }
    
    completeTutorial(overlay) {
        overlay.innerHTML = `
            <div class="tutorial-complete">
                <i class="fas fa-trophy fa-3x text-warning mb-3"></i>
                <h5>Tutorial Complete!</h5>
                <p>You've mastered this feature.</p>
                <button class="btn btn-primary close-tutorial">Close</button>
            </div>
        `;
        
        overlay.querySelector('.close-tutorial').addEventListener('click', () => {
            overlay.remove();
        });
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.tooltipsOnboarding = new TooltipsOnboarding();
});

// Add CSS for tooltips and tours
const style = document.createElement('style');
style.textContent = `
    /* Custom Tooltips */
    .custom-tooltip {
        background: #333;
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        font-size: 0.875rem;
        max-width: 300px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 9999;
        pointer-events: none;
    }
    
    .tooltip-arrow {
        position: absolute;
        width: 0;
        height: 0;
        border-style: solid;
    }
    
    .tooltip-arrow-top {
        bottom: -5px;
        left: 50%;
        transform: translateX(-50%);
        border-width: 5px 5px 0 5px;
        border-color: #333 transparent transparent transparent;
    }
    
    .tooltip-arrow-bottom {
        top: -5px;
        left: 50%;
        transform: translateX(-50%);
        border-width: 0 5px 5px 5px;
        border-color: transparent transparent #333 transparent;
    }
    
    .tooltip-arrow-left {
        right: -5px;
        top: 50%;
        transform: translateY(-50%);
        border-width: 5px 0 5px 5px;
        border-color: transparent transparent transparent #333;
    }
    
    .tooltip-arrow-right {
        left: -5px;
        top: 50%;
        transform: translateY(-50%);
        border-width: 5px 5px 5px 0;
        border-color: transparent #333 transparent transparent;
    }
    
    /* Rich tooltip content */
    .tooltip-title {
        font-size: 1rem;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    
    .tooltip-description {
        margin-bottom: 0.5rem;
    }
    
    .tooltip-list {
        margin: 0;
        padding-left: 1.25rem;
        font-size: 0.813rem;
    }
    
    .tooltip-link {
        color: #4dabf7;
        text-decoration: none;
        font-size: 0.813rem;
    }
    
    .tooltip-link:hover {
        text-decoration: underline;
    }
    
    /* Tour Overlay */
    .tour-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.5);
        z-index: 9996;
        pointer-events: none;
    }
    
    .tour-controls {
        position: fixed;
        bottom: 2rem;
        left: 50%;
        transform: translateX(-50%);
        background: white;
        padding: 1rem 2rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        display: flex;
        align-items: center;
        gap: 2rem;
        pointer-events: all;
        z-index: 9999;
    }
    
    .tour-highlight {
        position: relative;
        z-index: 9997;
        box-shadow: 0 0 0 4px rgba(46, 204, 113, 0.5);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 4px rgba(46, 204, 113, 0.5); }
        50% { box-shadow: 0 0 0 8px rgba(46, 204, 113, 0.3); }
        100% { box-shadow: 0 0 0 4px rgba(46, 204, 113, 0.5); }
    }
    
    .tour-spotlight {
        border: 3px solid var(--primary-color);
        border-radius: 0.5rem;
        animation: spotlight 2s infinite;
    }
    
    @keyframes spotlight {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .tour-tooltip {
        position: fixed;
        background: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
        max-width: 350px;
        z-index: 9999;
    }
    
    .tour-tooltip-title {
        margin-bottom: 0.75rem;
        color: var(--primary-color);
    }
    
    .tour-tooltip-content {
        margin: 0;
        color: #495057;
    }
    
    /* Feature Discovery */
    .feature-discovery-indicator {
        position: absolute;
        top: -5px;
        right: -5px;
        background: var(--primary-color);
        color: white;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        animation: sparkle 2s infinite;
    }
    
    @keyframes sparkle {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.2); }
    }
    
    /* Tutorial Mode */
    .tutorial-mode-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: rgba(46, 204, 113, 0.1);
        border-bottom: 3px solid var(--primary-color);
        padding: 1rem;
        z-index: 9995;
    }
    
    .tutorial-mode-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    .tutorial-mode-instruction {
        max-width: 1200px;
        margin: 1rem auto 0;
        padding: 1rem;
        background: white;
        border-radius: 0.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        font-size: 1.1rem;
        color: var(--primary-dark);
    }
    
    .tutorial-complete {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 3rem;
        border-radius: 1rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.15);
    }
    
    /* Contextual Help */
    .contextual-help-btn {
        padding: 0.25rem 0.5rem;
        font-size: 0.875rem;
        color: #6c757d;
        text-decoration: none;
    }
    
    .contextual-help-btn:hover {
        color: var(--primary-color);
    }
`;
document.head.appendChild(style);
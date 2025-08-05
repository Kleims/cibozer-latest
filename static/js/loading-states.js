/**
 * Loading States and Skeleton Screens for Cibozer
 * Provides visual feedback during async operations
 */

class LoadingStates {
    constructor() {
        this.activeLoaders = new Map();
        this.init();
    }
    
    init() {
        // Intercept fetch requests
        this.interceptFetch();
        
        // Setup skeleton screens
        this.setupSkeletonScreens();
        
        // Setup button loading states
        this.setupButtonLoaders();
        
        // Setup form submission states
        this.setupFormLoaders();
        
        // Setup lazy loading
        this.setupLazyLoading();
        
        // Initialize progress indicators
        this.setupProgressIndicators();
    }
    
    interceptFetch() {
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            const url = args[0]?.url || args[0];
            const method = args[1]?.method || 'GET';
            
            // Show appropriate loader based on request
            const loaderId = this.showLoader(url, method);
            
            try {
                const response = await originalFetch(...args);
                return response;
            } finally {
                // Hide loader after request completes
                this.hideLoader(loaderId);
            }
        };
    }
    
    showLoader(url, method) {
        const loaderId = `loader-${Date.now()}-${Math.random()}`;
        
        // Determine loader type based on URL/method
        if (url.includes('/api/generate')) {
            this.showMealPlanLoader();
        } else if (url.includes('/api/save')) {
            this.showSaveLoader();
        } else if (method === 'GET' && !this.activeLoaders.size) {
            this.showGlobalLoader();
        }
        
        this.activeLoaders.set(loaderId, { url, method, startTime: Date.now() });
        return loaderId;
    }
    
    hideLoader(loaderId) {
        const loader = this.activeLoaders.get(loaderId);
        if (!loader) return;
        
        const duration = Date.now() - loader.startTime;
        
        // Ensure minimum display time for better UX
        const minDisplayTime = 300;
        const remainingTime = Math.max(0, minDisplayTime - duration);
        
        setTimeout(() => {
            this.activeLoaders.delete(loaderId);
            
            // Hide loaders if no active requests
            if (this.activeLoaders.size === 0) {
                this.hideAllLoaders();
            }
        }, remainingTime);
    }
    
    showMealPlanLoader() {
        const existingLoader = document.getElementById('meal-plan-loader');
        if (existingLoader) return;
        
        const loader = document.createElement('div');
        loader.id = 'meal-plan-loader';
        loader.className = 'meal-plan-loader';
        loader.innerHTML = `
            <div class="loader-overlay">
                <div class="loader-content">
                    <div class="chef-animation">
                        <i class="fas fa-utensils fa-3x mb-3"></i>
                    </div>
                    <h4 class="mb-3">Creating Your Perfect Meal Plan</h4>
                    <div class="progress mb-3" style="width: 300px;">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             role="progressbar" style="width: 0%"></div>
                    </div>
                    <p class="loading-message">Analyzing nutritional requirements...</p>
                    <div class="loading-tips mt-4">
                        <p class="tip-text small text-muted">
                            <i class="fas fa-lightbulb me-2"></i>
                            <span id="loading-tip">Did you know? A balanced meal includes protein, carbs, and healthy fats!</span>
                        </p>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(loader);
        
        // Animate progress and update messages
        this.animateMealPlanLoader(loader);
    }
    
    animateMealPlanLoader(loader) {
        const progressBar = loader.querySelector('.progress-bar');
        const message = loader.querySelector('.loading-message');
        const tipText = loader.querySelector('#loading-tip');
        
        const messages = [
            'Analyzing nutritional requirements...',
            'Selecting fresh ingredients...',
            'Balancing macronutrients...',
            'Calculating portion sizes...',
            'Finalizing your meal plan...'
        ];
        
        const tips = [
            'Did you know? A balanced meal includes protein, carbs, and healthy fats!',
            'Tip: Eating colorful vegetables provides diverse nutrients!',
            'Fun fact: Meal planning can save you 2-3 hours per week!',
            'Remember: Staying hydrated is key to good nutrition!',
            'Pro tip: Prep ingredients ahead for easier cooking!'
        ];
        
        let progress = 0;
        let messageIndex = 0;
        let tipIndex = 0;
        
        const updateLoader = setInterval(() => {
            progress += Math.random() * 20;
            
            if (progress >= 100) {
                progress = 100;
                clearInterval(updateLoader);
            }
            
            progressBar.style.width = `${progress}%`;
            
            // Update message
            const newMessageIndex = Math.floor(progress / 20);
            if (newMessageIndex !== messageIndex && messages[newMessageIndex]) {
                messageIndex = newMessageIndex;
                message.textContent = messages[messageIndex];
            }
            
            // Rotate tips every 3 seconds
            if (progress % 30 < 5) {
                tipIndex = (tipIndex + 1) % tips.length;
                tipText.style.opacity = '0';
                setTimeout(() => {
                    tipText.textContent = tips[tipIndex];
                    tipText.style.opacity = '1';
                }, 300);
            }
        }, 500);
        
        // Store interval ID for cleanup
        loader.dataset.intervalId = updateLoader;
    }
    
    showSaveLoader() {
        const toast = document.createElement('div');
        toast.className = 'save-loader toast align-items-center';
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                    Saving your changes...
                </div>
            </div>
        `;
        
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(container);
        }
        
        container.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast, { autohide: false });
        bsToast.show();
        
        // Store reference for hiding
        this.saveToast = { element: toast, instance: bsToast };
    }
    
    showGlobalLoader() {
        // Don't show for very quick requests
        this.globalLoaderTimeout = setTimeout(() => {
            const loader = document.createElement('div');
            loader.id = 'global-loader';
            loader.className = 'global-loader';
            loader.innerHTML = `
                <div class="loader-bar">
                    <div class="loader-progress"></div>
                </div>
            `;
            
            document.body.appendChild(loader);
            
            // Animate loader
            requestAnimationFrame(() => {
                loader.querySelector('.loader-progress').style.width = '70%';
            });
        }, 100);
    }
    
    hideAllLoaders() {
        // Hide meal plan loader
        const mealPlanLoader = document.getElementById('meal-plan-loader');
        if (mealPlanLoader) {
            const intervalId = mealPlanLoader.dataset.intervalId;
            if (intervalId) clearInterval(intervalId);
            
            mealPlanLoader.classList.add('fade-out');
            setTimeout(() => mealPlanLoader.remove(), 300);
        }
        
        // Hide save loader
        if (this.saveToast) {
            // Show success state
            this.saveToast.element.querySelector('.toast-body').innerHTML = `
                <i class="fas fa-check-circle text-success me-2"></i>
                Saved successfully!
            `;
            
            setTimeout(() => {
                this.saveToast.instance.hide();
                this.saveToast = null;
            }, 1500);
        }
        
        // Hide global loader
        clearTimeout(this.globalLoaderTimeout);
        const globalLoader = document.getElementById('global-loader');
        if (globalLoader) {
            globalLoader.querySelector('.loader-progress').style.width = '100%';
            setTimeout(() => {
                globalLoader.classList.add('fade-out');
                setTimeout(() => globalLoader.remove(), 300);
            }, 200);
        }
    }
    
    setupSkeletonScreens() {
        // Find elements marked for skeleton loading
        const skeletonElements = document.querySelectorAll('[data-skeleton]');
        
        skeletonElements.forEach(element => {
            const type = element.dataset.skeleton;
            
            // Show skeleton while content loads
            if (!element.hasChildNodes() || element.querySelector('.loading')) {
                this.showSkeleton(element, type);
            }
        });
    }
    
    showSkeleton(container, type) {
        const skeletons = {
            'meal-card': `
                <div class="skeleton-meal-card">
                    <div class="skeleton skeleton-heading mb-3"></div>
                    <div class="skeleton skeleton-text mb-2"></div>
                    <div class="skeleton skeleton-text mb-2"></div>
                    <div class="skeleton skeleton-text mb-2" style="width: 60%;"></div>
                    <div class="skeleton skeleton-badge mt-3"></div>
                </div>
            `,
            'list-item': `
                <div class="skeleton-list-item d-flex align-items-center p-3">
                    <div class="skeleton skeleton-avatar me-3"></div>
                    <div class="flex-grow-1">
                        <div class="skeleton skeleton-text mb-2" style="width: 70%;"></div>
                        <div class="skeleton skeleton-text" style="width: 40%;"></div>
                    </div>
                </div>
            `,
            'form': `
                <div class="skeleton-form">
                    <div class="mb-3">
                        <div class="skeleton skeleton-label mb-2"></div>
                        <div class="skeleton skeleton-input"></div>
                    </div>
                    <div class="mb-3">
                        <div class="skeleton skeleton-label mb-2"></div>
                        <div class="skeleton skeleton-input"></div>
                    </div>
                    <div class="skeleton skeleton-button"></div>
                </div>
            `,
            'stats': `
                <div class="skeleton-stats text-center">
                    <div class="skeleton skeleton-number mx-auto mb-2"></div>
                    <div class="skeleton skeleton-text mx-auto" style="width: 60%;"></div>
                </div>
            `
        };
        
        container.innerHTML = skeletons[type] || this.createGenericSkeleton();
    }
    
    createGenericSkeleton() {
        return `
            <div class="skeleton-generic">
                <div class="skeleton skeleton-text mb-2"></div>
                <div class="skeleton skeleton-text mb-2"></div>
                <div class="skeleton skeleton-text" style="width: 75%;"></div>
            </div>
        `;
    }
    
    setupButtonLoaders() {
        document.addEventListener('click', (e) => {
            const button = e.target.closest('.btn[data-loading]');
            if (!button) return;
            
            // Don't process if already loading
            if (button.classList.contains('loading')) return;
            
            const loadingText = button.dataset.loading || 'Loading...';
            const originalHtml = button.innerHTML;
            
            // Set loading state
            button.classList.add('loading');
            button.disabled = true;
            button.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                ${loadingText}
            `;
            
            // Store original content for restoration
            button.dataset.originalHtml = originalHtml;
        });
    }
    
    setupFormLoaders() {
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (!form.dataset.showLoader) return;
            
            const submitButton = form.querySelector('[type="submit"]');
            if (!submitButton) return;
            
            // Show loading state
            this.setButtonLoading(submitButton, true);
            
            // Add form overlay
            const overlay = document.createElement('div');
            overlay.className = 'form-loader-overlay';
            overlay.innerHTML = '<div class="spinner-border text-primary"></div>';
            form.style.position = 'relative';
            form.appendChild(overlay);
        });
    }
    
    setButtonLoading(button, isLoading) {
        if (isLoading) {
            const loadingText = button.dataset.loadingText || 'Processing...';
            button.dataset.originalHtml = button.innerHTML;
            button.classList.add('loading');
            button.disabled = true;
            button.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2"></span>
                ${loadingText}
            `;
        } else {
            button.classList.remove('loading');
            button.disabled = false;
            button.innerHTML = button.dataset.originalHtml || button.innerHTML;
        }
    }
    
    setupLazyLoading() {
        const lazyElements = document.querySelectorAll('[data-lazy-load]');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const element = entry.target;
                    const contentUrl = element.dataset.lazyLoad;
                    
                    // Show skeleton
                    this.showSkeleton(element, element.dataset.skeleton || 'generic');
                    
                    // Load content
                    this.loadContent(element, contentUrl);
                    
                    // Stop observing
                    observer.unobserve(element);
                }
            });
        }, {
            rootMargin: '100px'
        });
        
        lazyElements.forEach(el => observer.observe(el));
    }
    
    async loadContent(element, url) {
        try {
            const response = await fetch(url);
            const content = await response.text();
            
            // Fade out skeleton
            element.style.opacity = '0';
            
            setTimeout(() => {
                element.innerHTML = content;
                element.style.opacity = '1';
                element.classList.add('loaded');
            }, 300);
        } catch (error) {
            element.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Failed to load content. 
                    <a href="#" onclick="location.reload()">Refresh page</a>
                </div>
            `;
        }
    }
    
    setupProgressIndicators() {
        // File upload progress
        const fileInputs = document.querySelectorAll('input[type="file"]');
        
        fileInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.showUploadProgress(e.target);
                }
            });
        });
    }
    
    showUploadProgress(input) {
        const progressBar = document.createElement('div');
        progressBar.className = 'upload-progress mt-2';
        progressBar.innerHTML = `
            <div class="progress">
                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                     role="progressbar" style="width: 0%"></div>
            </div>
            <small class="text-muted">Uploading...</small>
        `;
        
        input.parentElement.appendChild(progressBar);
        
        // Simulate upload progress
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 30;
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
                
                setTimeout(() => {
                    progressBar.innerHTML = `
                        <div class="text-success">
                            <i class="fas fa-check-circle me-2"></i>
                            Upload complete!
                        </div>
                    `;
                }, 500);
            }
            
            progressBar.querySelector('.progress-bar').style.width = `${progress}%`;
        }, 500);
    }
    
    // Public methods
    showCustomLoader(options) {
        const loader = document.createElement('div');
        loader.className = `custom-loader ${options.className || ''}`;
        loader.innerHTML = options.content || `
            <div class="spinner-border ${options.size || ''}" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        `;
        
        const container = options.container || document.body;
        container.appendChild(loader);
        
        return loader;
    }
    
    hideCustomLoader(loader) {
        if (loader && loader.parentNode) {
            loader.classList.add('fade-out');
            setTimeout(() => loader.remove(), 300);
        }
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.loadingStates = new LoadingStates();
});

// CSS for loading states
const style = document.createElement('style');
style.textContent = `
    /* Skeleton Screens */
    .skeleton {
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
        border-radius: 0.25rem;
    }
    
    @keyframes loading {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    .skeleton-text { height: 1rem; margin-bottom: 0.5rem; }
    .skeleton-heading { height: 2rem; width: 60%; }
    .skeleton-badge { height: 1.5rem; width: 80px; display: inline-block; }
    .skeleton-avatar { width: 48px; height: 48px; border-radius: 50%; }
    .skeleton-input { height: 38px; }
    .skeleton-label { height: 1rem; width: 100px; }
    .skeleton-button { height: 38px; width: 120px; }
    .skeleton-number { height: 3rem; width: 100px; }
    
    /* Meal Plan Loader */
    .meal-plan-loader {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 9999;
    }
    
    .loader-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(255, 255, 255, 0.95);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .loader-content {
        text-align: center;
        max-width: 400px;
    }
    
    .chef-animation i {
        animation: bounce 1s infinite;
        color: var(--primary-color);
    }
    
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-20px); }
    }
    
    .loading-tips {
        opacity: 0.8;
        transition: opacity 0.3s;
    }
    
    /* Global Loader */
    .global-loader {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 9998;
    }
    
    .loader-bar {
        height: 3px;
        background: rgba(0,0,0,0.1);
        overflow: hidden;
    }
    
    .loader-progress {
        height: 100%;
        background: var(--primary-color);
        width: 0;
        transition: width 0.3s ease;
        box-shadow: 0 0 10px rgba(46, 204, 113, 0.7);
    }
    
    /* Button Loading States */
    .btn.loading {
        position: relative;
        color: transparent;
    }
    
    .btn.loading .spinner-border {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
    }
    
    /* Form Loader Overlay */
    .form-loader-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(255, 255, 255, 0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10;
        border-radius: inherit;
    }
    
    /* Fade Effects */
    .fade-out {
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    /* Upload Progress */
    .upload-progress {
        animation: fadeIn 0.3s;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
`;
document.head.appendChild(style);
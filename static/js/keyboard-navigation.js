/**
 * Keyboard Navigation and Focus Management for Cibozer
 * Ensures accessibility and keyboard-only navigation support
 */

class KeyboardNavigationManager {
    constructor() {
        this.focusableElements = [
            'button',
            'a[href]',
            'input:not([disabled]):not([type="hidden"])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            '[tabindex]:not([tabindex="-1"])',
            '[contenteditable="true"]'
        ].join(', ');
        
        this.shortcuts = new Map();
        this.focusHistory = [];
        this.currentModalStack = [];
        
        this.init();
    }
    
    init() {
        this.setupFocusManagement();
        this.setupKeyboardShortcuts();
        this.setupModalFocusTrapping();
        this.setupSkipLinks();
        this.enhanceFocusIndicators();
    }
    
    setupFocusManagement() {
        // Track focus changes
        document.addEventListener('focusin', (e) => {
            this.focusHistory.push(e.target);
            // Keep only last 10 focus events
            if (this.focusHistory.length > 10) {
                this.focusHistory.shift();
            }
        });
        
        // Handle focus loss
        document.addEventListener('focusout', (e) => {
            // If focus is lost completely, restore to last known good element
            setTimeout(() => {
                if (!document.activeElement || document.activeElement === document.body) {
                    this.restoreFocus();
                }
            }, 100);
        });
        
        // Handle page load focus
        document.addEventListener('DOMContentLoaded', () => {
            this.setInitialFocus();
        });
    }
    
    setupKeyboardShortcuts() {
        // Register default shortcuts
        this.registerShortcut('Escape', () => {
            this.handleEscape();
        });
        
        this.registerShortcut('Tab', (e) => {
            this.handleTabNavigation(e);
        });
        
        this.registerShortcut('ArrowUp', (e) => {
            this.handleArrowNavigation(e, 'up');
        });
        
        this.registerShortcut('ArrowDown', (e) => {
            this.handleArrowNavigation(e, 'down');
        });
        
        this.registerShortcut('ArrowLeft', (e) => {
            this.handleArrowNavigation(e, 'left');
        });
        
        this.registerShortcut('ArrowRight', (e) => {
            this.handleArrowNavigation(e, 'right');
        });
        
        this.registerShortcut('Enter', (e) => {
            this.handleEnterKey(e);
        });
        
        this.registerShortcut(' ', (e) => {
            this.handleSpaceKey(e);
        });
        
        // Application-specific shortcuts
        this.registerShortcut('Alt+h', () => {
            window.location.href = '/';
        });
        
        this.registerShortcut('Alt+c', () => {
            const createBtn = document.querySelector('[href*="create"]');
            if (createBtn) createBtn.click();
        });
        
        this.registerShortcut('Alt+d', () => {
            const dashboardBtn = document.querySelector('[href*="dashboard"]');
            if (dashboardBtn) dashboardBtn.click();
        });
        
        this.registerShortcut('Alt+?', () => {
            this.showKeyboardHelp();
        });
        
        // Listen for keyboard events
        document.addEventListener('keydown', (e) => {
            this.handleKeydown(e);
        });
    }
    
    setupModalFocusTrapping() {
        // Handle modal opening
        document.addEventListener('shown.bs.modal', (e) => {
            this.trapFocusInModal(e.target);
            this.currentModalStack.push(e.target);
        });
        
        // Handle modal closing
        document.addEventListener('hidden.bs.modal', (e) => {
            this.currentModalStack = this.currentModalStack.filter(modal => modal !== e.target);
            this.restoreFocus();
        });
    }
    
    setupSkipLinks() {
        // Create skip navigation links
        const skipNav = document.createElement('div');
        skipNav.className = 'skip-nav';
        skipNav.innerHTML = `
            <a href="#main-content" class="skip-link">Skip to main content</a>
            <a href="#navigation" class="skip-link">Skip to navigation</a>
        `;
        
        // Add skip navigation styles
        const style = document.createElement('style');
        style.textContent = `
            .skip-nav {
                position: absolute;
                top: -100px;
                left: 0;
                z-index: 9999;
            }
            
            .skip-link {
                position: absolute;
                top: 0;
                left: 0;
                background: #000;
                color: #fff;
                padding: 8px 16px;
                text-decoration: none;
                font-weight: bold;
                z-index: 10000;
            }
            
            .skip-link:focus {
                top: 0;
                outline: 2px solid #fff;
                outline-offset: 2px;
            }
        `;
        
        document.head.appendChild(style);
        document.body.insertBefore(skipNav, document.body.firstChild);
        
        // Add IDs to skip targets if they don't exist
        const mainContent = document.querySelector('main') || 
                           document.querySelector('.container') || 
                           document.querySelector('#main-content');
        if (mainContent && !mainContent.id) {
            mainContent.id = 'main-content';
        }
        
        const navigation = document.querySelector('nav') || 
                          document.querySelector('.navbar') || 
                          document.querySelector('#navigation');
        if (navigation && !navigation.id) {
            navigation.id = 'navigation';
        }
    }
    
    enhanceFocusIndicators() {
        // Enhanced focus indicators
        const style = document.createElement('style');
        style.textContent = `
            *:focus-visible {
                outline: 3px solid var(--primary-color, #007bff) !important;
                outline-offset: 2px !important;
                border-radius: 4px;
                box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.8);
            }
            
            .btn:focus-visible {
                outline: 3px solid var(--primary-color, #007bff) !important;
                outline-offset: 2px !important;
                transform: translateY(-1px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            
            .form-control:focus,
            .form-select:focus {
                border-color: var(--primary-color, #007bff) !important;
                box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25) !important;
                outline: 2px solid var(--primary-color, #007bff) !important;
                outline-offset: 2px !important;
            }
        `;
        document.head.appendChild(style);
    }
    
    registerShortcut(key, callback) {
        this.shortcuts.set(key.toLowerCase(), callback);
    }
    
    handleKeydown(e) {
        const key = this.getKeyString(e);
        const callback = this.shortcuts.get(key.toLowerCase());
        
        if (callback) {
            // Don't interfere with form inputs unless it's a global shortcut
            if (this.isFormElement(e.target) && !key.includes('Alt+') && !key.includes('Ctrl+')) {
                return;
            }
            
            callback(e);
        }
    }
    
    getKeyString(e) {
        let key = e.key;
        
        if (e.altKey) key = 'Alt+' + key;
        if (e.ctrlKey) key = 'Ctrl+' + key;
        if (e.shiftKey && key.length > 1) key = 'Shift+' + key;
        
        return key;
    }
    
    isFormElement(element) {
        const formElements = ['INPUT', 'TEXTAREA', 'SELECT'];
        return formElements.includes(element.tagName) || 
               element.contentEditable === 'true';
    }
    
    handleEscape() {
        // Close modal if open
        if (this.currentModalStack.length > 0) {
            const currentModal = this.currentModalStack[this.currentModalStack.length - 1];
            const bsModal = bootstrap.Modal.getInstance(currentModal);
            if (bsModal) {
                bsModal.hide();
                return;
            }
        }
        
        // Close dropdown if open
        const openDropdown = document.querySelector('.dropdown-menu.show');
        if (openDropdown) {
            const dropdown = bootstrap.Dropdown.getInstance(openDropdown.previousElementSibling);
            if (dropdown) {
                dropdown.hide();
                return;
            }
        }
        
        // Clear form if focused on form element
        if (this.isFormElement(document.activeElement)) {
            if (document.activeElement.tagName === 'INPUT' && 
                document.activeElement.type === 'text') {
                document.activeElement.value = '';
            }
        }
    }
    
    handleTabNavigation(e) {
        // Enhanced tab navigation for modals
        if (this.currentModalStack.length > 0) {
            const currentModal = this.currentModalStack[this.currentModalStack.length - 1];
            this.constrainTabToModal(e, currentModal);
        }
    }
    
    handleArrowNavigation(e, direction) {
        const activeElement = document.activeElement;
        
        // Handle dropdown navigation
        if (activeElement.closest('.dropdown-menu')) {
            e.preventDefault();
            this.navigateDropdown(activeElement, direction);
            return;
        }
        
        // Handle tab navigation
        if (activeElement.closest('.nav-tabs') || activeElement.closest('.nav-pills')) {
            e.preventDefault();
            this.navigateTabs(activeElement, direction);
            return;
        }
        
        // Handle list navigation
        if (activeElement.closest('.list-group')) {
            e.preventDefault();
            this.navigateList(activeElement, direction);
            return;
        }
    }
    
    handleEnterKey(e) {
        // Activate buttons and links
        if (e.target.tagName === 'BUTTON' || 
            (e.target.tagName === 'A' && e.target.href)) {
            e.target.click();
        }
    }
    
    handleSpaceKey(e) {
        // Activate buttons
        if (e.target.tagName === 'BUTTON') {
            e.preventDefault();
            e.target.click();
        }
    }
    
    trapFocusInModal(modal) {
        const focusableElements = modal.querySelectorAll(this.focusableElements);
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        if (firstElement) {
            firstElement.focus();
        }
        
        modal.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                if (e.shiftKey) {
                    if (document.activeElement === firstElement) {
                        e.preventDefault();
                        lastElement.focus();
                    }
                } else {
                    if (document.activeElement === lastElement) {
                        e.preventDefault();
                        firstElement.focus();
                    }
                }
            }
        });
    }
    
    constrainTabToModal(e, modal) {
        const focusableElements = Array.from(modal.querySelectorAll(this.focusableElements));
        const currentIndex = focusableElements.indexOf(document.activeElement);
        
        if (currentIndex === -1) return;
        
        if (e.shiftKey) {
            // Shift+Tab - go to previous element
            if (currentIndex === 0) {
                e.preventDefault();
                focusableElements[focusableElements.length - 1].focus();
            }
        } else {
            // Tab - go to next element
            if (currentIndex === focusableElements.length - 1) {
                e.preventDefault();
                focusableElements[0].focus();
            }
        }
    }
    
    navigateDropdown(element, direction) {
        const dropdown = element.closest('.dropdown-menu');
        const items = Array.from(dropdown.querySelectorAll('.dropdown-item:not([disabled])'));
        const currentIndex = items.indexOf(element);
        
        let nextIndex;
        if (direction === 'up') {
            nextIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
        } else if (direction === 'down') {
            nextIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
        }
        
        if (items[nextIndex]) {
            items[nextIndex].focus();
        }
    }
    
    navigateTabs(element, direction) {
        const tabContainer = element.closest('.nav-tabs, .nav-pills');
        const tabs = Array.from(tabContainer.querySelectorAll('.nav-link:not([disabled])'));
        const currentIndex = tabs.indexOf(element);
        
        let nextIndex;
        if (direction === 'left') {
            nextIndex = currentIndex > 0 ? currentIndex - 1 : tabs.length - 1;
        } else if (direction === 'right') {
            nextIndex = currentIndex < tabs.length - 1 ? currentIndex + 1 : 0;
        }
        
        if (tabs[nextIndex]) {
            tabs[nextIndex].focus();
            tabs[nextIndex].click(); // Activate the tab
        }
    }
    
    navigateList(element, direction) {
        const list = element.closest('.list-group');
        const items = Array.from(list.querySelectorAll('.list-group-item:not([disabled])'));
        const currentIndex = items.indexOf(element);
        
        let nextIndex;
        if (direction === 'up') {
            nextIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
        } else if (direction === 'down') {
            nextIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
        }
        
        if (items[nextIndex]) {
            items[nextIndex].focus();
        }
    }
    
    setInitialFocus() {
        // Set focus to first interactive element or skip link
        const skipLink = document.querySelector('.skip-link');
        if (skipLink) {
            // Don't auto-focus skip link, let user activate it
            return;
        }
        
        const firstFocusable = document.querySelector(this.focusableElements);
        if (firstFocusable) {
            // Only focus if not in a form to avoid unexpected behavior
            if (!this.isFormElement(firstFocusable)) {
                firstFocusable.focus();
            }
        }
    }
    
    restoreFocus() {
        // Find the last valid focus target
        for (let i = this.focusHistory.length - 1; i >= 0; i--) {
            const element = this.focusHistory[i];
            if (element && element.isConnected && element.offsetParent !== null) {
                element.focus();
                return;
            }
        }
        
        // Fallback to first focusable element
        const firstFocusable = document.querySelector(this.focusableElements);
        if (firstFocusable) {
            firstFocusable.focus();
        }
    }
    
    showKeyboardHelp() {
        const helpModal = document.createElement('div');
        helpModal.className = 'modal fade';
        helpModal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Keyboard Shortcuts</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6>Navigation</h6>
                                <ul class="list-unstyled">
                                    <li><kbd>Alt</kbd> + <kbd>H</kbd> - Home</li>
                                    <li><kbd>Alt</kbd> + <kbd>C</kbd> - Create</li>
                                    <li><kbd>Alt</kbd> + <kbd>D</kbd> - Dashboard</li>
                                    <li><kbd>Tab</kbd> - Next element</li>
                                    <li><kbd>Shift</kbd> + <kbd>Tab</kbd> - Previous element</li>
                                </ul>
                            </div>
                            <div class="col-md-6">
                                <h6>General</h6>
                                <ul class="list-unstyled">
                                    <li><kbd>Esc</kbd> - Close modal/dropdown</li>
                                    <li><kbd>Enter</kbd> - Activate button/link</li>
                                    <li><kbd>Space</kbd> - Activate button</li>
                                    <li><kbd>↑</kbd><kbd>↓</kbd> - Navigate lists</li>
                                    <li><kbd>Alt</kbd> + <kbd>?</kbd> - This help</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Got it!</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(helpModal);
        const modal = new bootstrap.Modal(helpModal);
        modal.show();
        
        // Clean up after modal is hidden
        helpModal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(helpModal);
        });
    }
}

// Initialize keyboard navigation when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.keyboardNav = new KeyboardNavigationManager();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = KeyboardNavigationManager;
}
/**
 * Keyboard Navigation Enhancement for Cibozer
 * Provides comprehensive keyboard accessibility
 */

class KeyboardNavigation {
    constructor() {
        this.focusableElements = [];
        this.currentFocusIndex = -1;
        this.shortcuts = new Map();
        this.modalStack = [];
        this.init();
    }
    
    init() {
        // Setup keyboard shortcuts
        this.setupKeyboardShortcuts();
        
        // Setup focus management
        this.setupFocusManagement();
        
        // Setup skip links
        this.setupSkipLinks();
        
        // Setup modal focus trap
        this.setupModalFocusTrap();
        
        // Setup dropdown keyboard navigation
        this.setupDropdownNavigation();
        
        // Setup tab panel navigation
        this.setupTabNavigation();
        
        // Setup form navigation enhancements
        this.setupFormNavigation();
        
        // Setup custom component navigation
        this.setupCustomComponents();
        
        // Display shortcut help
        this.setupShortcutHelp();
    }
    
    setupKeyboardShortcuts() {
        // Define global shortcuts
        this.shortcuts.set('/', () => this.focusSearch());
        this.shortcuts.set('g h', () => this.navigate('/'));
        this.shortcuts.set('g c', () => this.navigate('/create'));
        this.shortcuts.set('g d', () => this.navigate('/dashboard'));
        this.shortcuts.set('g s', () => this.navigate('/settings'));
        this.shortcuts.set('?', () => this.showShortcutHelp());
        this.shortcuts.set('Escape', () => this.handleEscape());
        
        // Form shortcuts
        this.shortcuts.set('ctrl+Enter', () => this.submitActiveForm());
        this.shortcuts.set('ctrl+s', () => this.saveActiveForm());
        
        // Navigation shortcuts
        this.shortcuts.set('j', () => this.navigateNext());
        this.shortcuts.set('k', () => this.navigatePrevious());
        this.shortcuts.set('Enter', () => this.activateCurrentElement());
        
        // Accessibility shortcuts
        this.shortcuts.set('alt+/', () => this.announcePageInfo());
        this.shortcuts.set('alt+m', () => this.focusMainContent());
        
        // Setup key sequence detection
        this.setupKeySequenceDetection();
        
        // Main keyboard event handler
        document.addEventListener('keydown', (e) => {
            // Skip if in input field (unless it's a global shortcut)
            if (this.isInInputField(e.target) && !this.isGlobalShortcut(e)) {
                return;
            }
            
            this.handleKeyboardShortcut(e);
        });
    }
    
    setupKeySequenceDetection() {
        this.keySequence = [];
        this.sequenceTimeout = null;
        
        document.addEventListener('keydown', (e) => {
            // Only track printable characters and special keys
            if (e.key.length === 1 || ['Enter', 'Escape', 'Space'].includes(e.key)) {
                this.keySequence.push(e.key);
                
                // Clear sequence after delay
                clearTimeout(this.sequenceTimeout);
                this.sequenceTimeout = setTimeout(() => {
                    this.keySequence = [];
                }, 500);
                
                // Check for multi-key shortcuts
                const sequence = this.keySequence.join(' ');
                if (this.shortcuts.has(sequence)) {
                    e.preventDefault();
                    this.shortcuts.get(sequence)();
                    this.keySequence = [];
                }
            }
        });
    }
    
    handleKeyboardShortcut(e) {
        // Build shortcut string
        const parts = [];
        if (e.ctrlKey || e.metaKey) parts.push('ctrl');
        if (e.altKey) parts.push('alt');
        if (e.shiftKey) parts.push('shift');
        parts.push(e.key.toLowerCase());
        
        const shortcut = parts.join('+');
        
        // Check single key shortcuts
        if (this.shortcuts.has(e.key)) {
            e.preventDefault();
            this.shortcuts.get(e.key)();
        }
        // Check modifier shortcuts
        else if (this.shortcuts.has(shortcut)) {
            e.preventDefault();
            this.shortcuts.get(shortcut)();
        }
    }
    
    isInInputField(element) {
        return element.matches('input, textarea, select, [contenteditable="true"]');
    }
    
    isGlobalShortcut(e) {
        const globalKeys = ['/', '?', 'Escape'];
        return globalKeys.includes(e.key) || e.ctrlKey || e.metaKey || e.altKey;
    }
    
    setupFocusManagement() {
        // Track focusable elements
        this.updateFocusableElements();
        
        // Update on DOM changes
        const observer = new MutationObserver(() => {
            this.updateFocusableElements();
        });
        
        observer.observe(document.body, { 
            childList: true, 
            subtree: true,
            attributes: true,
            attributeFilter: ['disabled', 'tabindex']
        });
        
        // Add focus indicators
        document.addEventListener('focusin', (e) => {
            this.handleFocusIn(e.target);
        });
        
        document.addEventListener('focusout', (e) => {
            this.handleFocusOut(e.target);
        });
    }
    
    updateFocusableElements() {
        const selector = [
            'a[href]',
            'button:not([disabled])',
            'input:not([disabled])',
            'textarea:not([disabled])',
            'select:not([disabled])',
            '[tabindex]:not([tabindex="-1"])',
            '[contenteditable="true"]',
            'details',
            'summary'
        ].join(', ');
        
        this.focusableElements = Array.from(document.querySelectorAll(selector))
            .filter(el => this.isVisible(el))
            .sort((a, b) => {
                const tabindexA = parseInt(a.getAttribute('tabindex') || '0');
                const tabindexB = parseInt(b.getAttribute('tabindex') || '0');
                
                if (tabindexA !== tabindexB) {
                    if (tabindexA === 0) return 1;
                    if (tabindexB === 0) return -1;
                    return tabindexA - tabindexB;
                }
                
                return 0;
            });
    }
    
    isVisible(element) {
        const style = window.getComputedStyle(element);
        return style.display !== 'none' && 
               style.visibility !== 'hidden' && 
               element.offsetParent !== null;
    }
    
    handleFocusIn(element) {
        // Update current focus index
        this.currentFocusIndex = this.focusableElements.indexOf(element);
        
        // Add focus class for enhanced styling
        element.classList.add('keyboard-focus');
        
        // Announce element to screen readers if needed
        this.announceElement(element);
    }
    
    handleFocusOut(element) {
        element.classList.remove('keyboard-focus');
    }
    
    announceElement(element) {
        // Skip if already has aria-label or aria-describedby
        if (element.getAttribute('aria-label') || element.getAttribute('aria-describedby')) {
            return;
        }
        
        // Add helpful announcements for specific elements
        if (element.matches('.btn-danger')) {
            this.announce('Caution: This action cannot be undone');
        } else if (element.matches('[data-toggle="dropdown"]')) {
            this.announce('Press space or enter to open menu');
        }
    }
    
    announce(message, priority = 'polite') {
        // Create or get announcement region
        let announcer = document.getElementById('keyboard-announcer');
        
        if (!announcer) {
            announcer = document.createElement('div');
            announcer.id = 'keyboard-announcer';
            announcer.className = 'sr-only';
            announcer.setAttribute('aria-live', priority);
            announcer.setAttribute('aria-atomic', 'true');
            document.body.appendChild(announcer);
        }
        
        // Update message
        announcer.textContent = message;
        
        // Clear after delay
        setTimeout(() => {
            announcer.textContent = '';
        }, 1000);
    }
    
    setupSkipLinks() {
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.className = 'skip-link sr-only-focusable';
        skipLink.textContent = 'Skip to main content';
        
        document.body.insertBefore(skipLink, document.body.firstChild);
        
        // Ensure main content has ID
        const main = document.querySelector('main, [role="main"], .main-content');
        if (main && !main.id) {
            main.id = 'main-content';
            main.setAttribute('tabindex', '-1');
        }
        
        // Handle skip link click
        skipLink.addEventListener('click', (e) => {
            e.preventDefault();
            const target = document.querySelector(skipLink.getAttribute('href'));
            if (target) {
                target.focus();
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    }
    
    setupModalFocusTrap() {
        // Monitor for modal open/close
        const observer = new MutationObserver((mutations) => {
            mutations.forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if (node.classList?.contains('modal')) {
                        this.handleModalOpen(node);
                    }
                });
                
                mutation.removedNodes.forEach(node => {
                    if (node.classList?.contains('modal')) {
                        this.handleModalClose(node);
                    }
                });
            });
        });
        
        observer.observe(document.body, { childList: true });
        
        // Setup Bootstrap modal events
        document.addEventListener('shown.bs.modal', (e) => {
            this.handleModalOpen(e.target);
        });
        
        document.addEventListener('hidden.bs.modal', (e) => {
            this.handleModalClose(e.target);
        });
    }
    
    handleModalOpen(modal) {
        // Store last focused element
        this.lastFocusedElement = document.activeElement;
        
        // Get focusable elements in modal
        const focusableInModal = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        if (focusableInModal.length > 0) {
            // Focus first element or close button
            const closeButton = modal.querySelector('[data-bs-dismiss="modal"]');
            const firstElement = closeButton || focusableInModal[0];
            
            setTimeout(() => firstElement.focus(), 100);
            
            // Setup focus trap
            this.trapFocus(modal, focusableInModal);
        }
        
        // Add to modal stack
        this.modalStack.push(modal);
    }
    
    handleModalClose(modal) {
        // Remove from modal stack
        const index = this.modalStack.indexOf(modal);
        if (index > -1) {
            this.modalStack.splice(index, 1);
        }
        
        // Restore focus
        if (this.lastFocusedElement && this.modalStack.length === 0) {
            this.lastFocusedElement.focus();
            this.lastFocusedElement = null;
        }
    }
    
    trapFocus(container, focusableElements) {
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        const trapHandler = (e) => {
            if (e.key !== 'Tab') return;
            
            if (e.shiftKey) {
                // Shift + Tab
                if (document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                }
            } else {
                // Tab
                if (document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        };
        
        container.addEventListener('keydown', trapHandler);
        
        // Clean up on close
        container.addEventListener('hidden.bs.modal', () => {
            container.removeEventListener('keydown', trapHandler);
        }, { once: true });
    }
    
    setupDropdownNavigation() {
        document.addEventListener('keydown', (e) => {
            const dropdown = e.target.closest('.dropdown');
            if (!dropdown) return;
            
            const toggle = dropdown.querySelector('[data-bs-toggle="dropdown"]');
            const menu = dropdown.querySelector('.dropdown-menu');
            const items = Array.from(menu?.querySelectorAll('.dropdown-item:not(.disabled)') || []);
            
            if (!items.length) return;
            
            const currentIndex = items.indexOf(document.activeElement);
            
            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    if (!menu.classList.contains('show')) {
                        toggle.click();
                        items[0]?.focus();
                    } else {
                        const nextIndex = currentIndex + 1 < items.length ? currentIndex + 1 : 0;
                        items[nextIndex].focus();
                    }
                    break;
                    
                case 'ArrowUp':
                    e.preventDefault();
                    if (menu.classList.contains('show')) {
                        const prevIndex = currentIndex - 1 >= 0 ? currentIndex - 1 : items.length - 1;
                        items[prevIndex].focus();
                    }
                    break;
                    
                case 'Home':
                    e.preventDefault();
                    items[0]?.focus();
                    break;
                    
                case 'End':
                    e.preventDefault();
                    items[items.length - 1]?.focus();
                    break;
                    
                case 'Escape':
                    e.preventDefault();
                    toggle.click();
                    toggle.focus();
                    break;
            }
        });
    }
    
    setupTabNavigation() {
        const tabLists = document.querySelectorAll('[role="tablist"]');
        
        tabLists.forEach(tabList => {
            const tabs = Array.from(tabList.querySelectorAll('[role="tab"]'));
            
            tabList.addEventListener('keydown', (e) => {
                const currentTab = document.activeElement;
                const currentIndex = tabs.indexOf(currentTab);
                
                if (currentIndex === -1) return;
                
                let nextIndex;
                
                switch (e.key) {
                    case 'ArrowRight':
                    case 'ArrowDown':
                        e.preventDefault();
                        nextIndex = (currentIndex + 1) % tabs.length;
                        this.activateTab(tabs[nextIndex]);
                        break;
                        
                    case 'ArrowLeft':
                    case 'ArrowUp':
                        e.preventDefault();
                        nextIndex = currentIndex - 1 >= 0 ? currentIndex - 1 : tabs.length - 1;
                        this.activateTab(tabs[nextIndex]);
                        break;
                        
                    case 'Home':
                        e.preventDefault();
                        this.activateTab(tabs[0]);
                        break;
                        
                    case 'End':
                        e.preventDefault();
                        this.activateTab(tabs[tabs.length - 1]);
                        break;
                }
            });
        });
    }
    
    activateTab(tab) {
        // Deactivate all tabs
        const tabList = tab.closest('[role="tablist"]');
        tabList.querySelectorAll('[role="tab"]').forEach(t => {
            t.setAttribute('aria-selected', 'false');
            t.setAttribute('tabindex', '-1');
        });
        
        // Activate selected tab
        tab.setAttribute('aria-selected', 'true');
        tab.setAttribute('tabindex', '0');
        tab.focus();
        
        // Show associated panel
        const panelId = tab.getAttribute('aria-controls');
        if (panelId) {
            document.querySelectorAll('[role="tabpanel"]').forEach(panel => {
                panel.classList.toggle('show', panel.id === panelId);
                panel.classList.toggle('active', panel.id === panelId);
            });
        }
    }
    
    setupFormNavigation() {
        // Enter key navigation in forms
        document.addEventListener('keydown', (e) => {
            if (e.key !== 'Enter') return;
            
            const field = e.target;
            if (!field.matches('input:not([type="submit"]), select')) return;
            
            const form = field.form;
            if (!form || field.type === 'textarea') return;
            
            e.preventDefault();
            
            // Find next field
            const fields = Array.from(form.elements).filter(el => 
                !el.disabled && 
                el.type !== 'hidden' && 
                el.tabIndex !== -1
            );
            
            const currentIndex = fields.indexOf(field);
            const nextField = fields[currentIndex + 1];
            
            if (nextField) {
                nextField.focus();
                if (nextField.type === 'text' || nextField.type === 'email') {
                    nextField.select();
                }
            } else {
                // Submit form if on last field
                const submitBtn = form.querySelector('[type="submit"]');
                if (submitBtn) {
                    submitBtn.click();
                }
            }
        });
    }
    
    setupCustomComponents() {
        // Custom slider navigation
        this.setupSliderKeyboard();
        
        // Custom select navigation
        this.setupCustomSelectKeyboard();
        
        // Meal card navigation
        this.setupMealCardNavigation();
    }
    
    setupSliderKeyboard() {
        const sliders = document.querySelectorAll('input[type="range"]');
        
        sliders.forEach(slider => {
            slider.addEventListener('keydown', (e) => {
                const step = parseFloat(slider.step) || 1;
                const min = parseFloat(slider.min) || 0;
                const max = parseFloat(slider.max) || 100;
                let value = parseFloat(slider.value);
                
                switch (e.key) {
                    case 'ArrowLeft':
                    case 'ArrowDown':
                        e.preventDefault();
                        value = Math.max(min, value - step);
                        break;
                        
                    case 'ArrowRight':
                    case 'ArrowUp':
                        e.preventDefault();
                        value = Math.min(max, value + step);
                        break;
                        
                    case 'PageDown':
                        e.preventDefault();
                        value = Math.max(min, value - step * 10);
                        break;
                        
                    case 'PageUp':
                        e.preventDefault();
                        value = Math.min(max, value + step * 10);
                        break;
                        
                    case 'Home':
                        e.preventDefault();
                        value = min;
                        break;
                        
                    case 'End':
                        e.preventDefault();
                        value = max;
                        break;
                        
                    default:
                        return;
                }
                
                slider.value = value;
                slider.dispatchEvent(new Event('input'));
                
                // Announce new value
                this.announce(`${slider.getAttribute('aria-label') || 'Slider'}: ${value}`);
            });
        });
    }
    
    setupCustomSelectKeyboard() {
        const customSelects = document.querySelectorAll('.custom-select');
        
        customSelects.forEach(select => {
            const options = select.querySelectorAll('.custom-option');
            let currentIndex = -1;
            
            select.setAttribute('tabindex', '0');
            select.setAttribute('role', 'combobox');
            select.setAttribute('aria-expanded', 'false');
            
            select.addEventListener('keydown', (e) => {
                switch (e.key) {
                    case 'Enter':
                    case ' ':
                        e.preventDefault();
                        this.toggleCustomSelect(select);
                        break;
                        
                    case 'ArrowDown':
                        e.preventDefault();
                        currentIndex = Math.min(currentIndex + 1, options.length - 1);
                        this.highlightOption(options[currentIndex]);
                        break;
                        
                    case 'ArrowUp':
                        e.preventDefault();
                        currentIndex = Math.max(currentIndex - 1, 0);
                        this.highlightOption(options[currentIndex]);
                        break;
                        
                    case 'Escape':
                        e.preventDefault();
                        this.closeCustomSelect(select);
                        break;
                }
            });
        });
    }
    
    setupMealCardNavigation() {
        const mealGrid = document.querySelector('.meal-grid, .meal-list');
        if (!mealGrid) return;
        
        const cards = Array.from(mealGrid.querySelectorAll('.meal-card'));
        let currentIndex = -1;
        
        mealGrid.addEventListener('keydown', (e) => {
            const columns = Math.floor(mealGrid.offsetWidth / cards[0].offsetWidth);
            
            switch (e.key) {
                case 'ArrowRight':
                    e.preventDefault();
                    currentIndex = Math.min(currentIndex + 1, cards.length - 1);
                    cards[currentIndex]?.focus();
                    break;
                    
                case 'ArrowLeft':
                    e.preventDefault();
                    currentIndex = Math.max(currentIndex - 1, 0);
                    cards[currentIndex]?.focus();
                    break;
                    
                case 'ArrowDown':
                    e.preventDefault();
                    currentIndex = Math.min(currentIndex + columns, cards.length - 1);
                    cards[currentIndex]?.focus();
                    break;
                    
                case 'ArrowUp':
                    e.preventDefault();
                    currentIndex = Math.max(currentIndex - columns, 0);
                    cards[currentIndex]?.focus();
                    break;
                    
                case 'Enter':
                case ' ':
                    e.preventDefault();
                    cards[currentIndex]?.click();
                    break;
            }
        });
        
        // Make cards focusable
        cards.forEach((card, index) => {
            card.setAttribute('tabindex', '0');
            card.setAttribute('role', 'button');
            
            card.addEventListener('focus', () => {
                currentIndex = index;
            });
        });
    }
    
    // Navigation helper methods
    focusSearch() {
        const searchInput = document.querySelector('input[type="search"], input[name="search"], #search');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        }
    }
    
    navigate(path) {
        window.location.href = path;
    }
    
    handleEscape() {
        // Close modals
        const modal = document.querySelector('.modal.show');
        if (modal) {
            const closeBtn = modal.querySelector('[data-bs-dismiss="modal"]');
            closeBtn?.click();
            return;
        }
        
        // Close dropdowns
        const openDropdown = document.querySelector('.dropdown-menu.show');
        if (openDropdown) {
            const toggle = openDropdown.closest('.dropdown').querySelector('[data-bs-toggle="dropdown"]');
            toggle?.click();
            return;
        }
        
        // Clear focus
        document.activeElement?.blur();
    }
    
    submitActiveForm() {
        const form = document.activeElement?.closest('form');
        if (form) {
            const submitBtn = form.querySelector('[type="submit"]');
            submitBtn?.click();
        }
    }
    
    saveActiveForm() {
        const form = document.activeElement?.closest('form');
        if (form && form.dataset.autoSave) {
            this.announce('Form saved');
            // Trigger save logic
            form.dispatchEvent(new Event('save'));
        }
    }
    
    navigateNext() {
        if (this.currentFocusIndex < this.focusableElements.length - 1) {
            this.currentFocusIndex++;
            this.focusableElements[this.currentFocusIndex]?.focus();
        }
    }
    
    navigatePrevious() {
        if (this.currentFocusIndex > 0) {
            this.currentFocusIndex--;
            this.focusableElements[this.currentFocusIndex]?.focus();
        }
    }
    
    activateCurrentElement() {
        const element = document.activeElement;
        if (element) {
            element.click();
        }
    }
    
    announcePageInfo() {
        const pageTitle = document.title;
        const pageHeading = document.querySelector('h1')?.textContent || '';
        const mainContent = document.querySelector('main, [role="main"]');
        
        let message = `Page: ${pageTitle}`;
        if (pageHeading) message += `. ${pageHeading}`;
        
        if (mainContent) {
            const links = mainContent.querySelectorAll('a').length;
            const buttons = mainContent.querySelectorAll('button').length;
            const forms = mainContent.querySelectorAll('form').length;
            
            message += `. ${links} links, ${buttons} buttons, ${forms} forms`;
        }
        
        this.announce(message);
    }
    
    focusMainContent() {
        const main = document.querySelector('main, [role="main"], #main-content');
        if (main) {
            main.setAttribute('tabindex', '-1');
            main.focus();
            this.announce('Main content focused');
        }
    }
    
    setupShortcutHelp() {
        // Create help panel
        const helpPanel = document.createElement('div');
        helpPanel.className = 'keyboard-help-panel';
        helpPanel.innerHTML = `
            <div class="help-header">
                <h5>Keyboard Shortcuts</h5>
                <button class="btn-close" aria-label="Close help"></button>
            </div>
            <div class="help-content">
                <div class="help-section">
                    <h6>Navigation</h6>
                    <dl>
                        <dt>/</dt><dd>Focus search</dd>
                        <dt>g h</dt><dd>Go to home</dd>
                        <dt>g c</dt><dd>Go to create meal plan</dd>
                        <dt>g d</dt><dd>Go to dashboard</dd>
                        <dt>j / k</dt><dd>Navigate next/previous</dd>
                    </dl>
                </div>
                <div class="help-section">
                    <h6>Actions</h6>
                    <dl>
                        <dt>Enter</dt><dd>Activate element</dd>
                        <dt>Ctrl+Enter</dt><dd>Submit form</dd>
                        <dt>Ctrl+S</dt><dd>Save form</dd>
                        <dt>Escape</dt><dd>Close modal/dropdown</dd>
                    </dl>
                </div>
                <div class="help-section">
                    <h6>Accessibility</h6>
                    <dl>
                        <dt>Alt+/</dt><dd>Announce page info</dd>
                        <dt>Alt+M</dt><dd>Focus main content</dd>
                        <dt>Tab</dt><dd>Navigate forward</dd>
                        <dt>Shift+Tab</dt><dd>Navigate backward</dd>
                    </dl>
                </div>
            </div>
        `;
        
        document.body.appendChild(helpPanel);
        
        // Close button handler
        helpPanel.querySelector('.btn-close').addEventListener('click', () => {
            this.hideShortcutHelp();
        });
        
        this.helpPanel = helpPanel;
    }
    
    showShortcutHelp() {
        this.helpPanel.classList.add('show');
        this.helpPanel.querySelector('.btn-close').focus();
        
        // Trap focus in help panel
        const focusableInHelp = this.helpPanel.querySelectorAll('button, a');
        this.trapFocus(this.helpPanel, focusableInHelp);
    }
    
    hideShortcutHelp() {
        this.helpPanel.classList.remove('show');
        
        // Restore focus
        if (this.lastFocusedElement) {
            this.lastFocusedElement.focus();
        }
    }
    
    // Utility methods
    toggleCustomSelect(select) {
        const isOpen = select.getAttribute('aria-expanded') === 'true';
        select.setAttribute('aria-expanded', !isOpen);
        
        const dropdown = select.querySelector('.custom-dropdown');
        if (dropdown) {
            dropdown.classList.toggle('show', !isOpen);
        }
    }
    
    closeCustomSelect(select) {
        select.setAttribute('aria-expanded', 'false');
        const dropdown = select.querySelector('.custom-dropdown');
        dropdown?.classList.remove('show');
    }
    
    highlightOption(option) {
        if (!option) return;
        
        // Remove previous highlight
        option.parentElement.querySelectorAll('.highlighted').forEach(opt => {
            opt.classList.remove('highlighted');
        });
        
        // Add highlight
        option.classList.add('highlighted');
        option.scrollIntoView({ block: 'nearest' });
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.keyboardNavigation = new KeyboardNavigation();
});

// Add CSS for keyboard navigation
const style = document.createElement('style');
style.textContent = `
    /* Skip Links */
    .skip-link {
        position: absolute;
        top: -40px;
        left: 0;
        background: var(--primary-color);
        color: white;
        padding: 8px 16px;
        text-decoration: none;
        border-radius: 0 0 4px 0;
        z-index: 10000;
    }
    
    .skip-link:focus {
        top: 0;
    }
    
    /* Enhanced Focus Indicators */
    .keyboard-focus {
        outline: 3px solid var(--primary-color) !important;
        outline-offset: 2px !important;
        box-shadow: 0 0 0 4px rgba(46, 204, 113, 0.25) !important;
    }
    
    /* Focus visible only for keyboard users */
    :focus:not(:focus-visible) {
        outline: none !important;
    }
    
    :focus-visible {
        outline: 3px solid var(--primary-color) !important;
        outline-offset: 2px !important;
    }
    
    /* Keyboard Help Panel */
    .keyboard-help-panel {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) scale(0.9);
        background: white;
        border-radius: 0.5rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        max-width: 600px;
        max-height: 80vh;
        overflow: hidden;
        z-index: 10000;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s;
    }
    
    .keyboard-help-panel.show {
        opacity: 1;
        visibility: visible;
        transform: translate(-50%, -50%) scale(1);
    }
    
    .help-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 1.5rem;
        border-bottom: 1px solid #e9ecef;
    }
    
    .help-content {
        padding: 1.5rem;
        overflow-y: auto;
        max-height: calc(80vh - 60px);
    }
    
    .help-section {
        margin-bottom: 2rem;
    }
    
    .help-section h6 {
        color: var(--primary-color);
        margin-bottom: 1rem;
        font-weight: 600;
    }
    
    .help-section dl {
        display: grid;
        grid-template-columns: 100px 1fr;
        gap: 0.5rem 1rem;
        margin: 0;
    }
    
    .help-section dt {
        font-family: monospace;
        background: #f8f9fa;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: normal;
        text-align: center;
    }
    
    .help-section dd {
        margin: 0;
        padding: 0.25rem 0;
    }
    
    /* Custom Component Focus */
    .meal-card:focus {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }
    
    .custom-option.highlighted {
        background: rgba(46, 204, 113, 0.1);
        color: var(--primary-dark);
    }
    
    /* Announcement Region */
    #keyboard-announcer {
        position: absolute;
        left: -10000px;
        width: 1px;
        height: 1px;
        overflow: hidden;
    }
    
    /* Focus trap overlay */
    .focus-trap-active {
        position: relative;
    }
    
    .focus-trap-active::after {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.5);
        z-index: 9998;
        pointer-events: none;
    }
`;
document.head.appendChild(style);
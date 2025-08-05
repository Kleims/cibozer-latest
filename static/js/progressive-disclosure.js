/**
 * Progressive Disclosure System for Cibozer
 * Shows information progressively to avoid overwhelming users
 */

class ProgressiveDisclosure {
    constructor() {
        this.userLevel = this.determineUserLevel();
        this.expandedSections = new Set();
        this.init();
    }
    
    init() {
        // Setup collapsible sections
        this.setupCollapsibleSections();
        
        // Setup expandable details
        this.setupExpandableDetails();
        
        // Setup progressive forms
        this.setupProgressiveForms();
        
        // Setup smart tooltips
        this.setupSmartTooltips();
        
        // Setup contextual information
        this.setupContextualInfo();
        
        // Track user interactions
        this.trackInteractions();
    }
    
    determineUserLevel() {
        // Check local storage for user experience level
        const visits = parseInt(localStorage.getItem('cibozer_visits') || '0');
        const lastVisit = localStorage.getItem('cibozer_last_visit');
        
        // Update visit count
        localStorage.setItem('cibozer_visits', visits + 1);
        localStorage.setItem('cibozer_last_visit', new Date().toISOString());
        
        // Determine level based on visits and activity
        if (visits === 0) return 'beginner';
        if (visits < 5) return 'intermediate';
        return 'advanced';
    }
    
    setupCollapsibleSections() {
        // Find all sections marked for progressive disclosure
        const sections = document.querySelectorAll('[data-progressive="true"]');
        
        sections.forEach(section => {
            const priority = section.dataset.priority || 'medium';
            const showFor = section.dataset.showFor || 'all';
            
            // Determine if section should be initially visible
            const shouldShow = this.shouldShowSection(priority, showFor);
            
            if (!shouldShow) {
                this.makeCollapsible(section);
            }
        });
    }
    
    shouldShowSection(priority, showFor) {
        // Always show high priority content
        if (priority === 'high') return true;
        
        // Show based on user level
        if (showFor === 'all') return true;
        if (showFor === 'advanced' && this.userLevel !== 'advanced') return false;
        if (showFor === 'intermediate' && this.userLevel === 'beginner') return false;
        
        // Show medium priority for non-beginners
        if (priority === 'medium' && this.userLevel !== 'beginner') return true;
        
        return false;
    }
    
    makeCollapsible(section) {
        const header = section.querySelector('h2, h3, h4, .section-header');
        if (!header) return;
        
        const content = section.querySelector('.section-content') || section;
        const sectionId = section.id || `section-${Math.random().toString(36).substr(2, 9)}`;
        
        // Hide content initially
        content.style.display = 'none';
        content.classList.add('progressive-content');
        
        // Add expand/collapse button
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'btn btn-sm btn-link progressive-toggle';
        toggleBtn.innerHTML = '<i class="fas fa-plus-circle"></i> Show More';
        toggleBtn.setAttribute('aria-expanded', 'false');
        toggleBtn.setAttribute('aria-controls', sectionId);
        
        header.appendChild(toggleBtn);
        header.style.cursor = 'pointer';
        
        // Handle toggle
        const toggle = () => {
            const isExpanded = toggleBtn.getAttribute('aria-expanded') === 'true';
            
            if (isExpanded) {
                this.collapseSection(content, toggleBtn);
                this.expandedSections.delete(sectionId);
            } else {
                this.expandSection(content, toggleBtn);
                this.expandedSections.add(sectionId);
                
                // Track expansion for analytics
                this.trackExpansion(sectionId, section.dataset.trackingName);
            }
        };
        
        toggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggle();
        });
        
        header.addEventListener('click', toggle);
    }
    
    expandSection(content, toggleBtn) {
        // Animate expansion
        content.style.display = 'block';
        content.style.height = '0';
        content.style.overflow = 'hidden';
        content.style.transition = 'height 0.3s ease-out';
        
        requestAnimationFrame(() => {
            content.style.height = content.scrollHeight + 'px';
            
            setTimeout(() => {
                content.style.height = 'auto';
                content.style.overflow = 'visible';
            }, 300);
        });
        
        toggleBtn.innerHTML = '<i class="fas fa-minus-circle"></i> Show Less';
        toggleBtn.setAttribute('aria-expanded', 'true');
    }
    
    collapseSection(content, toggleBtn) {
        // Animate collapse
        content.style.height = content.scrollHeight + 'px';
        content.style.overflow = 'hidden';
        
        requestAnimationFrame(() => {
            content.style.transition = 'height 0.3s ease-out';
            content.style.height = '0';
            
            setTimeout(() => {
                content.style.display = 'none';
            }, 300);
        });
        
        toggleBtn.innerHTML = '<i class="fas fa-plus-circle"></i> Show More';
        toggleBtn.setAttribute('aria-expanded', 'false');
    }
    
    setupExpandableDetails() {
        // Find all expandable detail elements
        const details = document.querySelectorAll('[data-expandable="true"]');
        
        details.forEach(detail => {
            const summary = detail.dataset.summary;
            const fullContent = detail.innerHTML;
            
            if (!summary) return;
            
            // Create expandable structure
            const container = document.createElement('div');
            container.className = 'expandable-detail';
            
            const summaryEl = document.createElement('div');
            summaryEl.className = 'detail-summary';
            summaryEl.innerHTML = summary;
            
            const expandLink = document.createElement('a');
            expandLink.href = '#';
            expandLink.className = 'expand-link ms-1';
            expandLink.textContent = 'Learn more';
            expandLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleDetail(container, summaryEl, detail, fullContent);
            });
            
            summaryEl.appendChild(expandLink);
            container.appendChild(summaryEl);
            
            // Replace original element
            detail.parentNode.replaceChild(container, detail);
        });
    }
    
    toggleDetail(container, summaryEl, originalDetail, fullContent) {
        if (container.classList.contains('expanded')) {
            // Collapse
            const fullEl = container.querySelector('.detail-full');
            fullEl.style.height = fullEl.scrollHeight + 'px';
            
            requestAnimationFrame(() => {
                fullEl.style.transition = 'height 0.3s ease-out';
                fullEl.style.height = '0';
                
                setTimeout(() => {
                    fullEl.remove();
                    summaryEl.style.display = 'block';
                    container.classList.remove('expanded');
                }, 300);
            });
        } else {
            // Expand
            summaryEl.style.display = 'none';
            
            const fullEl = document.createElement('div');
            fullEl.className = 'detail-full';
            fullEl.innerHTML = fullContent;
            fullEl.style.height = '0';
            fullEl.style.overflow = 'hidden';
            
            container.appendChild(fullEl);
            container.classList.add('expanded');
            
            requestAnimationFrame(() => {
                fullEl.style.transition = 'height 0.3s ease-out';
                fullEl.style.height = fullEl.scrollHeight + 'px';
                
                setTimeout(() => {
                    fullEl.style.height = 'auto';
                    fullEl.style.overflow = 'visible';
                }, 300);
            });
        }
    }
    
    setupProgressiveForms() {
        const forms = document.querySelectorAll('form[data-progressive-fields="true"]');
        
        forms.forEach(form => {
            const optionalFields = form.querySelectorAll('.optional-field-group');
            
            if (optionalFields.length === 0) return;
            
            // Hide optional fields initially
            optionalFields.forEach(fieldGroup => {
                fieldGroup.style.display = 'none';
                fieldGroup.classList.add('progressive-field');
            });
            
            // Add "Show more options" button
            const showMoreBtn = document.createElement('button');
            showMoreBtn.type = 'button';
            showMoreBtn.className = 'btn btn-link show-more-fields';
            showMoreBtn.innerHTML = '<i class="fas fa-cog"></i> Advanced Options';
            
            const lastRequiredField = form.querySelector('.required-fields-end') || 
                                    form.querySelector('button[type="submit"]').parentElement;
            
            lastRequiredField.parentNode.insertBefore(showMoreBtn, lastRequiredField);
            
            showMoreBtn.addEventListener('click', () => {
                const isShowing = showMoreBtn.classList.contains('showing');
                
                if (isShowing) {
                    this.hideOptionalFields(optionalFields, showMoreBtn);
                } else {
                    this.showOptionalFields(optionalFields, showMoreBtn);
                }
            });
        });
    }
    
    showOptionalFields(fields, button) {
        fields.forEach((field, index) => {
            setTimeout(() => {
                field.style.display = 'block';
                field.style.opacity = '0';
                field.style.transform = 'translateY(-10px)';
                
                requestAnimationFrame(() => {
                    field.style.transition = 'opacity 0.3s, transform 0.3s';
                    field.style.opacity = '1';
                    field.style.transform = 'translateY(0)';
                });
            }, index * 100);
        });
        
        button.innerHTML = '<i class="fas fa-cog"></i> Hide Advanced Options';
        button.classList.add('showing');
    }
    
    hideOptionalFields(fields, button) {
        fields.forEach((field, index) => {
            setTimeout(() => {
                field.style.transition = 'opacity 0.3s, transform 0.3s';
                field.style.opacity = '0';
                field.style.transform = 'translateY(-10px)';
                
                setTimeout(() => {
                    field.style.display = 'none';
                }, 300);
            }, index * 50);
        });
        
        button.innerHTML = '<i class="fas fa-cog"></i> Advanced Options';
        button.classList.remove('showing');
    }
    
    setupSmartTooltips() {
        // Progressive tooltips that appear based on user behavior
        const tooltipTriggers = document.querySelectorAll('[data-smart-tooltip]');
        
        tooltipTriggers.forEach(trigger => {
            const tooltipContent = trigger.dataset.smartTooltip;
            const showAfter = parseInt(trigger.dataset.showAfter || '3');
            const showFor = trigger.dataset.showFor || 'beginner';
            
            // Check if tooltip should be shown for this user
            if (!this.shouldShowTooltip(showFor)) return;
            
            let hoverCount = 0;
            let tooltipShown = false;
            
            trigger.addEventListener('mouseenter', () => {
                hoverCount++;
                
                if (hoverCount >= showAfter && !tooltipShown) {
                    this.showSmartTooltip(trigger, tooltipContent);
                    tooltipShown = true;
                    
                    // Remember that we've shown this tooltip
                    localStorage.setItem(`tooltip_shown_${trigger.id}`, 'true');
                }
            });
        });
    }
    
    shouldShowTooltip(showFor) {
        if (showFor === 'all') return true;
        if (showFor === 'beginner' && this.userLevel === 'beginner') return true;
        if (showFor === 'intermediate' && this.userLevel !== 'advanced') return true;
        return false;
    }
    
    showSmartTooltip(element, content) {
        const tooltip = document.createElement('div');
        tooltip.className = 'smart-tooltip';
        tooltip.innerHTML = `
            <div class="tooltip-arrow"></div>
            <div class="tooltip-content">
                ${content}
                <button class="tooltip-dismiss"><i class="fas fa-times"></i></button>
            </div>
        `;
        
        document.body.appendChild(tooltip);
        
        // Position tooltip
        const rect = element.getBoundingClientRect();
        tooltip.style.position = 'absolute';
        tooltip.style.top = `${rect.bottom + window.scrollY + 10}px`;
        tooltip.style.left = `${rect.left + rect.width / 2}px`;
        tooltip.style.transform = 'translateX(-50%)';
        
        // Animate in
        tooltip.style.opacity = '0';
        tooltip.style.animation = 'fadeInTooltip 0.3s forwards';
        
        // Dismiss functionality
        tooltip.querySelector('.tooltip-dismiss').addEventListener('click', () => {
            tooltip.style.animation = 'fadeOutTooltip 0.3s forwards';
            setTimeout(() => tooltip.remove(), 300);
        });
        
        // Auto-dismiss after 10 seconds
        setTimeout(() => {
            if (tooltip.parentNode) {
                tooltip.style.animation = 'fadeOutTooltip 0.3s forwards';
                setTimeout(() => tooltip.remove(), 300);
            }
        }, 10000);
    }
    
    setupContextualInfo() {
        // Add contextual information panels that appear when needed
        const contextTriggers = document.querySelectorAll('[data-context-info]');
        
        contextTriggers.forEach(trigger => {
            const infoId = trigger.dataset.contextInfo;
            const infoPanel = document.getElementById(infoId);
            
            if (!infoPanel) return;
            
            // Initially hide info panel
            infoPanel.style.display = 'none';
            infoPanel.classList.add('context-info-panel');
            
            // Show on focus/interaction
            trigger.addEventListener('focus', () => {
                this.showContextPanel(infoPanel, trigger);
            });
            
            trigger.addEventListener('blur', () => {
                setTimeout(() => {
                    if (!infoPanel.contains(document.activeElement)) {
                        this.hideContextPanel(infoPanel);
                    }
                }, 100);
            });
        });
    }
    
    showContextPanel(panel, trigger) {
        panel.style.display = 'block';
        panel.style.opacity = '0';
        panel.style.transform = 'translateY(-10px)';
        
        // Position near trigger
        const rect = trigger.getBoundingClientRect();
        if (rect.right + panel.offsetWidth > window.innerWidth) {
            panel.style.right = '20px';
        }
        
        requestAnimationFrame(() => {
            panel.style.transition = 'opacity 0.3s, transform 0.3s';
            panel.style.opacity = '1';
            panel.style.transform = 'translateY(0)';
        });
    }
    
    hideContextPanel(panel) {
        panel.style.transition = 'opacity 0.3s, transform 0.3s';
        panel.style.opacity = '0';
        panel.style.transform = 'translateY(-10px)';
        
        setTimeout(() => {
            panel.style.display = 'none';
        }, 300);
    }
    
    trackInteractions() {
        // Track which progressive elements users interact with
        document.addEventListener('click', (e) => {
            const progressive = e.target.closest('[data-progressive]');
            if (progressive) {
                const action = e.target.closest('.progressive-toggle') ? 'toggle' : 'interact';
                this.logInteraction(progressive.id, action);
            }
        });
    }
    
    trackExpansion(sectionId, trackingName) {
        const expansions = JSON.parse(localStorage.getItem('cibozer_expansions') || '{}');
        expansions[sectionId] = (expansions[sectionId] || 0) + 1;
        localStorage.setItem('cibozer_expansions', JSON.stringify(expansions));
        
        // Send to analytics if available
        if (window.gtag) {
            window.gtag('event', 'progressive_disclosure', {
                'event_category': 'engagement',
                'event_label': trackingName || sectionId
            });
        }
    }
    
    logInteraction(elementId, action) {
        const interactions = JSON.parse(localStorage.getItem('cibozer_pd_interactions') || '[]');
        interactions.push({
            element: elementId,
            action: action,
            timestamp: Date.now(),
            userLevel: this.userLevel
        });
        
        // Keep only last 100 interactions
        if (interactions.length > 100) {
            interactions.shift();
        }
        
        localStorage.setItem('cibozer_pd_interactions', JSON.stringify(interactions));
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.progressiveDisclosure = new ProgressiveDisclosure();
});

// Add CSS for progressive disclosure
const style = document.createElement('style');
style.textContent = `
    .progressive-toggle {
        padding: 0.25rem 0.5rem;
        margin-left: 0.5rem;
        font-size: 0.875rem;
        text-decoration: none;
        transition: all 0.2s;
    }
    
    .progressive-toggle:hover {
        transform: scale(1.05);
    }
    
    .progressive-content {
        margin-top: 1rem;
    }
    
    .expandable-detail {
        margin: 1rem 0;
    }
    
    .expand-link {
        font-size: 0.9rem;
        text-decoration: underline;
    }
    
    .progressive-field {
        padding-top: 1rem;
        border-top: 1px solid rgba(0,0,0,0.1);
        margin-top: 1rem;
    }
    
    .show-more-fields {
        margin: 1rem 0;
        padding: 0.5rem 1rem;
        font-size: 0.9rem;
    }
    
    .smart-tooltip {
        background: #333;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        max-width: 300px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1050;
    }
    
    .tooltip-arrow {
        position: absolute;
        top: -5px;
        left: 50%;
        transform: translateX(-50%);
        width: 0;
        height: 0;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-bottom: 5px solid #333;
    }
    
    .tooltip-dismiss {
        position: absolute;
        top: 0.5rem;
        right: 0.5rem;
        background: none;
        border: none;
        color: white;
        opacity: 0.7;
        cursor: pointer;
        padding: 0.25rem;
    }
    
    .tooltip-dismiss:hover {
        opacity: 1;
    }
    
    .context-info-panel {
        position: absolute;
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
        max-width: 300px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        z-index: 100;
    }
    
    @keyframes fadeInTooltip {
        from { opacity: 0; transform: translateX(-50%) translateY(-10px); }
        to { opacity: 1; transform: translateX(-50%) translateY(0); }
    }
    
    @keyframes fadeOutTooltip {
        from { opacity: 1; transform: translateX(-50%) translateY(0); }
        to { opacity: 0; transform: translateX(-50%) translateY(-10px); }
    }
`;
document.head.appendChild(style);
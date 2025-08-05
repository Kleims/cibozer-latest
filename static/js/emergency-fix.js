// Emergency fix for stuck page
console.log('EMERGENCY FIX ACTIVATED');

// Immediate fixes
(function() {
    // 1. Remove ALL modal backdrops immediately
    document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
    
    // 2. Fix body classes
    document.body.classList.remove('modal-open');
    document.body.style = '';
    
    // 3. Hide all modals
    document.querySelectorAll('.modal').forEach(modal => {
        modal.classList.remove('show');
        modal.style.display = 'none';
        modal.setAttribute('aria-hidden', 'true');
    });
    
    // 4. Fix hero section overlay
    const style = document.createElement('style');
    style.textContent = `
        .hero-section::before,
        .hero-section::after {
            pointer-events: none !important;
            z-index: -1 !important;
        }
        
        /* Ensure all interactive elements are clickable */
        a, button, input, select, textarea, .btn {
            position: relative !important;
            z-index: 10 !important;
            pointer-events: auto !important;
        }
        
        /* Remove any blocking overlays */
        .modal-backdrop {
            display: none !important;
        }
        
        /* Fix body */
        body.modal-open {
            overflow: auto !important;
            padding-right: 0 !important;
        }
    `;
    document.head.appendChild(style);
    
    console.log('Emergency styles applied');
})();

// After DOM loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded - applying additional fixes');
    
    // Monitor for modal issues
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.target.classList && mutation.target.classList.contains('modal-backdrop')) {
                console.log('Detected modal backdrop, checking...');
                // If there's a backdrop but no visible modal, remove it
                const visibleModals = document.querySelectorAll('.modal.show');
                if (visibleModals.length === 0) {
                    console.log('Removing orphaned backdrop');
                    mutation.target.remove();
                }
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['class']
    });
    
    // Fix navigation
    const fixNavigation = () => {
        const navLinks = document.querySelectorAll('a[href], .nav-link');
        navLinks.forEach(link => {
            link.style.cursor = 'pointer';
            link.onclick = null; // Remove any blocking handlers
        });
        console.log(`Fixed ${navLinks.length} navigation links`);
    };
    
    fixNavigation();
    
    // Periodic cleanup
    setInterval(() => {
        const backdrops = document.querySelectorAll('.modal-backdrop');
        if (backdrops.length > 0 && document.querySelectorAll('.modal.show').length === 0) {
            console.log('Cleaning up orphaned backdrops');
            backdrops.forEach(el => el.remove());
            document.body.classList.remove('modal-open');
        }
    }, 1000);
    
    console.log('Emergency fix fully activated');
});
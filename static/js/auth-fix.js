// Auth flow fix
console.log('Auth fix loading...');

document.addEventListener('DOMContentLoaded', function() {
    // Fix for login form getting stuck
    const loginForm = document.querySelector('form[action*="login"]');
    if (loginForm) {
        console.log('Found login form, adding submit handler');
        
        loginForm.addEventListener('submit', function(e) {
            console.log('Login form submitted');
            
            // Show visual feedback
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Signing in...';
                
                // Re-enable after timeout (in case something goes wrong)
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 5000);
            }
        });
    }
    
    // Remove any stuck loading states on page load
    const removeStuckLoading = () => {
        // Remove loading classes
        document.body.classList.remove('loading');
        
        // Remove any loading overlays
        const loadingOverlays = document.querySelectorAll('.loading-overlay, .modal-backdrop, [id*="loading"]');
        loadingOverlays.forEach(el => {
            if (el.style.display !== 'none' && !el.classList.contains('modal')) {
                console.log('Removing stuck loading element:', el);
                el.style.display = 'none';
            }
        });
        
        // Enable all disabled buttons
        const disabledButtons = document.querySelectorAll('button[disabled], .btn[disabled]');
        disabledButtons.forEach(btn => {
            console.log('Re-enabling button:', btn.textContent);
            btn.disabled = false;
        });
    };
    
    // Run cleanup immediately
    removeStuckLoading();
    
    // Also run after a short delay
    setTimeout(removeStuckLoading, 500);
    
    // Check for navigation issues
    const checkNavigation = () => {
        const currentPath = window.location.pathname;
        console.log('Current path:', currentPath);
        
        // If we're stuck on a page, make sure we can navigate
        const links = document.querySelectorAll('a[href]');
        links.forEach(link => {
            link.addEventListener('click', function(e) {
                console.log('Link clicked:', this.href);
                // Let navigation proceed normally
            });
        });
    };
    
    checkNavigation();
});
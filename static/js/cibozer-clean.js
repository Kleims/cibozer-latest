/**
 * Cibozer - Clean JavaScript Solution
 * Single file to handle all interactions without conflicts
 */

console.log('Cibozer Clean JS loading...');

// Global state
let isLoading = false;

// Main initialization
document.addEventListener('DOMContentLoaded', function() {
    console.log('Cibozer Clean JS initialized');
    
    // Remove any existing issues immediately
    cleanupStuckStates();
    
    // Initialize components
    initializeTooltips();
    initializeModals();
    initializeNavigation();
    
    console.log('Cibozer Clean JS ready');
});

/**
 * Clean up any stuck states
 */
function cleanupStuckStates() {
    // Remove orphaned backdrops
    const backdrops = document.querySelectorAll('.modal-backdrop');
    backdrops.forEach(backdrop => {
        console.log('Removing orphaned backdrop');
        backdrop.remove();
    });
    
    // Fix body classes
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
    
    // Hide any stuck modals
    const modals = document.querySelectorAll('.modal.show');
    modals.forEach(modal => {
        if (!modal.dataset.shouldBeVisible) {
            console.log('Hiding stuck modal:', modal.id);
            modal.classList.remove('show');
            modal.style.display = 'none';
            modal.setAttribute('aria-hidden', 'true');
        }
    });
}

/**
 * Initialize Bootstrap tooltips safely
 */
function initializeTooltips() {
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(el => {
            try {
                new bootstrap.Tooltip(el);
            } catch (e) {
                console.error('Tooltip error:', e);
            }
        });
    }
}

/**
 * Initialize modal handling
 */
function initializeModals() {
    // Clean modal event handling
    document.addEventListener('show.bs.modal', function(e) {
        console.log('Modal showing:', e.target.id);
        isLoading = true;
    });
    
    document.addEventListener('hidden.bs.modal', function(e) {
        console.log('Modal hidden:', e.target.id);
        isLoading = false;
        
        // Ensure cleanup
        setTimeout(() => {
            cleanupStuckStates();
        }, 100);
    });
}

/**
 * Initialize navigation
 */
function initializeNavigation() {
    // Only add click handlers to specific elements, not all links
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Only log, don't prevent navigation
            console.log('Navigation clicked:', this.href);
        });
    });
}

/**
 * Show loading state
 */
function showLoading(message = 'Loading...') {
    console.log('Showing loading:', message);
    isLoading = true;
    
    // Find or create loading modal
    let loadingModal = document.getElementById('loadingModal');
    if (loadingModal) {
        const modal = bootstrap.Modal.getInstance(loadingModal) || new bootstrap.Modal(loadingModal);
        modal.show();
    }
}

/**
 * Hide loading state
 */
function hideLoading() {
    console.log('Hiding loading');
    isLoading = false;
    
    // Hide loading modal
    const loadingModal = document.getElementById('loadingModal');
    if (loadingModal) {
        const modal = bootstrap.Modal.getInstance(loadingModal);
        if (modal) {
            modal.hide();
        }
    }
    
    // Cleanup
    setTimeout(() => {
        cleanupStuckStates();
    }, 100);
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // Create notification element
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
    `;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

/**
 * Global error handler
 */
window.addEventListener('error', function(e) {
    console.error('🚨 GLOBAL ERROR:', e.message, 'at', e.filename, ':', e.lineno);
    console.error('🚨 ERROR STACK:', e.error ? e.error.stack : 'No stack available');
    
    // If error might be related to stuck state, try to fix it
    if (e.message.includes('modal') || e.message.includes('backdrop')) {
        console.log('Modal-related error detected, attempting cleanup');
        cleanupStuckStates();
    }
});

// Unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(e) {
    console.error('🚨 UNHANDLED PROMISE REJECTION:', e.reason);
    console.error('🚨 PROMISE:', e.promise);
});

/**
 * Download meal plan as PDF
 */
function downloadPDF() {
    console.log('Download PDF clicked');
    showNotification('PDF download feature coming soon!', 'info');
}

/**
 * View shopping list
 */
function viewShoppingList() {
    console.log('View shopping list clicked');
    showNotification('Shopping list feature coming soon!', 'info');
}

/**
 * Generate another meal plan
 */
function generateAnother() {
    console.log('Generate another clicked');
    // Hide results modal and reset form
    const resultsModal = bootstrap.Modal.getInstance(document.getElementById('resultsModal'));
    if (resultsModal) {
        resultsModal.hide();
    }
    // Reset form if exists
    const form = document.getElementById('mealPlanForm');
    if (form) {
        form.reset();
    }
}

// Export functions for global use
window.CibozerClean = {
    showLoading,
    hideLoading,
    showNotification,
    cleanupStuckStates
};

// Export additional functions globally
window.downloadPDF = downloadPDF;
window.viewShoppingList = viewShoppingList;
window.generateAnother = generateAnother;

// Periodic cleanup (every 5 seconds)
setInterval(() => {
    if (!isLoading) {
        cleanupStuckStates();
    }
}, 5000);

console.log('Cibozer Clean JS loaded successfully');
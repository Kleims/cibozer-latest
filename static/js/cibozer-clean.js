/**
 * Cibozer - Clean JavaScript Solution
 * Single file to handle all interactions without conflicts
 * Enhanced with robust error handling and resilience
 */

// Import error handling utilities
// Note: error-handling.js and api-client.js should be loaded before this file

// Global state
let isLoading = false;

// Main initialization
document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initializeTooltips();
    initializeModals();
    initializeNavigation();
    
    // Delayed cleanup to avoid interfering with page load
    setTimeout(() => {
        cleanupStuckStates();  // Use the existing cleanup function
    }, 1000);
});

/**
 * Clean up any stuck states
 */
function cleanupStuckStates() {
    // Remove orphaned backdrops
    const backdrops = document.querySelectorAll('.modal-backdrop');
    backdrops.forEach(backdrop => {
        // Remove orphaned backdrop
        backdrop.remove();
    });
    
    // Fix body classes
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
    
    // Hide any stuck modals (but not if they were just shown)
    const modals = document.querySelectorAll('.modal.show');
    modals.forEach(modal => {
        // Skip modals that have Bootstrap instances (they're being managed)
        const bsModal = bootstrap.Modal.getInstance(modal);
        if (bsModal && bsModal._isShown) {
            return; // Skip this modal, it's actively being shown
        }
        
        if (!modal.dataset.shouldBeVisible) {
            // Hide stuck modal
            modal.classList.remove('show');
            modal.style.display = 'none';
            modal.setAttribute('aria-hidden', 'true');
        }
    });
}

/**
 * Initialize Bootstrap tooltips safely with enhanced error handling
 */
function initializeTooltips() {
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(el => {
            try {
                new bootstrap.Tooltip(el);
            } catch (e) {
                if (window.ErrorHandling) {
                    window.ErrorHandling.logError('Tooltip Initialization Error', { 
                        element: el.tagName, 
                        error: e.message 
                    });
                }
                // Don't let tooltip errors break the page
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
        // Modal showing
        isLoading = true;
    });
    
    document.addEventListener('hidden.bs.modal', function(e) {
        // Modal hidden
        isLoading = false;
        
        // Only cleanup if this was the results modal being closed by user
        if (e.target.id === 'resultsModal') {
            // Clear the shouldBeVisible flag when user closes results
            e.target.dataset.shouldBeVisible = 'false';
            setTimeout(() => {
                cleanupStuckStates();
            }, 300);
        }
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
            // Navigation clicked
        });
    });
}

/**
 * Show loading state with error handling
 */
function showLoading(message = 'Loading...') {
    try {
        // Show loading state
        isLoading = true;
        
        // Find or create loading modal
        let loadingModal = document.getElementById('loadingModal');
        if (loadingModal) {
            const modal = bootstrap.Modal.getInstance(loadingModal) || new bootstrap.Modal(loadingModal);
            modal.show();
        }
    } catch (e) {
        if (window.ErrorHandling) {
            window.ErrorHandling.logError('Show Loading Error', { error: e.message });
        }
        // Continue without loading modal if it fails
    }
}

/**
 * Hide loading state with error handling
 */
function hideLoading() {
    try {
        // Hide loading state
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
    } catch (e) {
        if (window.ErrorHandling) {
            window.ErrorHandling.logError('Hide Loading Error', { error: e.message });
        }
        // Force cleanup even if modal hiding fails
        isLoading = false;
        cleanupStuckStates();
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Log message (removed for production)
    
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
        // Modal-related error detected, attempting cleanup
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
    // Download PDF clicked
    showNotification('PDF download feature coming soon!', 'info');
}

/**
 * View shopping list
 */
function viewShoppingList() {
    // View shopping list clicked
    showNotification('Shopping list feature coming soon!', 'info');
}

/**
 * Generate another meal plan
 */
function generateAnother() {
    // Generate another clicked
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

// Periodic cleanup (every 5 seconds) with memory leak prevention
let cleanupInterval = setInterval(() => {
    if (!isLoading) {
        cleanupStuckStates();
    }
}, 5000);

// Clear interval on page unload to prevent memory leaks
window.addEventListener('beforeunload', function() {
    if (cleanupInterval) {
        clearInterval(cleanupInterval);
        cleanupInterval = null;
    }
});

// Clear interval when navigating away (SPA behavior)
window.addEventListener('pagehide', function() {
    if (cleanupInterval) {
        clearInterval(cleanupInterval);
        cleanupInterval = null;
    }
});

// Cibozer Clean JS loaded successfully
// Minimal JavaScript - just console logging
console.log('Minimal JS loaded');

// Log any errors
window.addEventListener('error', function(e) {
    console.error('Error:', e.message, 'at', e.filename, ':', e.lineno);
});

// Simple click handler for debugging
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM ready');
    
    // Add click listener to all clickable elements
    document.addEventListener('click', function(e) {
        console.log('Clicked:', e.target.tagName, e.target.className);
    });
});
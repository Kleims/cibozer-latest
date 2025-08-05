// Diagnostic script to find click issues
console.log('=== CIBOZER DIAGNOSTIC TOOL ===');

window.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded');
    
    // Check for jQuery conflicts
    if (typeof $ !== 'undefined') {
        console.log('jQuery version:', $.fn.jquery);
    }
    
    // Check for Bootstrap
    if (typeof bootstrap !== 'undefined') {
        console.log('Bootstrap loaded:', bootstrap.VERSION || 'unknown version');
    }
    
    // Find all clickable elements
    const clickables = document.querySelectorAll('button, a, input[type="submit"], .btn');
    console.log(`Found ${clickables.length} clickable elements`);
    
    // Test each element
    clickables.forEach((el, index) => {
        const rect = el.getBoundingClientRect();
        const computed = window.getComputedStyle(el);
        
        // Check if element is visible and clickable
        const isVisible = rect.width > 0 && rect.height > 0 && computed.display !== 'none';
        const isClickable = computed.pointerEvents !== 'none';
        
        if (!isVisible || !isClickable) {
            console.warn(`Element ${index} might not be clickable:`, {
                element: el,
                text: el.textContent.trim().substring(0, 50),
                visible: isVisible,
                clickable: isClickable,
                display: computed.display,
                pointerEvents: computed.pointerEvents,
                position: computed.position,
                zIndex: computed.zIndex
            });
        }
    });
    
    // Check what's at click position
    document.addEventListener('mousedown', (e) => {
        console.log('=== CLICK DIAGNOSTIC ===');
        console.log('Click at:', e.clientX, e.clientY);
        
        const elements = document.elementsFromPoint(e.clientX, e.clientY);
        console.log('Elements under cursor (top to bottom):');
        
        elements.forEach((el, index) => {
            const computed = window.getComputedStyle(el);
            console.log(`${index}: ${el.tagName}.${el.className}`, {
                id: el.id,
                pointerEvents: computed.pointerEvents,
                position: computed.position,
                zIndex: computed.zIndex,
                cursor: computed.cursor
            });
        });
        
        console.log('=== END DIAGNOSTIC ===');
    }, true);
    
    // Check for any error in console
    const originalError = console.error;
    console.error = function(...args) {
        console.log('=== ERROR DETECTED ===');
        originalError.apply(console, args);
        console.log('=== END ERROR ===');
    };
    
    console.log('Diagnostic tool loaded. Click anywhere to see diagnostic info.');
});
// Click fix for Cibozer
console.log('Loading click fix...');

document.addEventListener('DOMContentLoaded', function() {
    console.log('Applying click fixes...');
    
    // Fix 1: Remove any blocking modal backdrops
    const removeBlockingBackdrops = () => {
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => {
            console.log('Removing stray backdrop:', backdrop);
            backdrop.remove();
        });
        
        // Also check for stuck modals
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            if (!modal.classList.contains('d-block')) {
                console.log('Hiding stuck modal:', modal.id);
                modal.classList.remove('show');
                modal.style.display = 'none';
            }
        });
    };
    
    // Fix 2: Ensure body is not locked
    const unlockBody = () => {
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    };
    
    // Fix 3: Check for invisible overlays
    const checkForOverlays = () => {
        const elements = document.elementsFromPoint(window.innerWidth / 2, window.innerHeight / 2);
        console.log('Elements at center of screen:', elements);
        
        elements.forEach(el => {
            const computed = window.getComputedStyle(el);
            if (computed.pointerEvents === 'none' || 
                (computed.position === 'fixed' && computed.zIndex > 1000)) {
                console.log('Potential blocking element:', el, {
                    pointerEvents: computed.pointerEvents,
                    position: computed.position,
                    zIndex: computed.zIndex
                });
            }
        });
    };
    
    // Fix 4: Force enable clicks on buttons and links
    const forceEnableClicks = () => {
        const clickables = document.querySelectorAll('button, a, input, select, textarea, .btn, [role="button"]');
        clickables.forEach(el => {
            el.style.pointerEvents = 'auto';
            el.style.position = 'relative';
            el.style.zIndex = '10';
        });
        console.log(`Enabled clicks on ${clickables.length} elements`);
    };
    
    // Fix 5: Add debug click handler
    const addDebugHandler = () => {
        document.addEventListener('click', function(e) {
            console.log('Click detected on:', e.target, {
                tagName: e.target.tagName,
                className: e.target.className,
                id: e.target.id,
                href: e.target.href || 'N/A'
            });
            
            // If clicking seems blocked, try to force through
            if (e.target.tagName === 'A' && e.target.href && !e.defaultPrevented) {
                console.log('Link click might be blocked, attempting navigation...');
            }
        }, true);
    };
    
    // Apply all fixes
    removeBlockingBackdrops();
    unlockBody();
    checkForOverlays();
    forceEnableClicks();
    addDebugHandler();
    
    // Reapply fixes after a delay (in case of dynamic content)
    setTimeout(() => {
        console.log('Reapplying fixes...');
        removeBlockingBackdrops();
        unlockBody();
        forceEnableClicks();
    }, 1000);
    
    // Also fix on window focus (in case user switched tabs)
    window.addEventListener('focus', () => {
        removeBlockingBackdrops();
        unlockBody();
    });
    
    console.log('Click fixes applied!');
});
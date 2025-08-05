/**
 * Touch Gesture Handler for Cibozer Mobile Experience
 * Handles swipe, pinch, tap, and other mobile gestures
 */

class TouchGestureHandler {
    constructor() {
        this.touches = new Map();
        this.gestures = new Map();
        this.settings = {
            swipeThreshold: 50,
            swipeVelocity: 0.3,
            tapTimeout: 300,
            longPressTimeout: 500,
            doubleTapTimeout: 300,
            pinchThreshold: 10
        };
        
        this.init();
    }
    
    init() {
        if (!this.isTouchDevice()) {
            return; // Skip on non-touch devices
        }
        
        this.setupTouchListeners();
        this.setupGestureDetection();
        this.enhanceMobileInteractions();
    }
    
    isTouchDevice() {
        return 'ontouchstart' in window || 
               navigator.maxTouchPoints > 0 || 
               navigator.msMaxTouchPoints > 0;
    }
    
    setupTouchListeners() {
        // Passive listeners for better performance
        document.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
        document.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        document.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false });
        document.addEventListener('touchcancel', this.handleTouchCancel.bind(this), { passive: true });
        
        // Prevent default behaviors that interfere with gestures
        document.addEventListener('touchstart', (e) => {
            // Prevent zoom on double tap for specific elements
            const target = e.target.closest('.no-zoom, .btn, .form-control');
            if (target) {
                e.preventDefault();
            }
        }, { passive: false });
    }
    
    setupGestureDetection() {
        // Register common gestures
        this.registerGesture('swipe-left', this.handleSwipeLeft.bind(this));
        this.registerGesture('swipe-right', this.handleSwipeRight.bind(this));
        this.registerGesture('swipe-up', this.handleSwipeUp.bind(this));
        this.registerGesture('swipe-down', this.handleSwipeDown.bind(this));
        this.registerGesture('tap', this.handleTap.bind(this));
        this.registerGesture('double-tap', this.handleDoubleTap.bind(this));
        this.registerGesture('long-press', this.handleLongPress.bind(this));
        this.registerGesture('pinch', this.handlePinch.bind(this));
    }
    
    enhanceMobileInteractions() {
        // Card swipe gestures
        this.enhanceCardSwiping();
        
        // Modal gestures
        this.enhanceModalGestures();
        
        // Navigation gestures
        this.enhanceNavigationGestures();
        
        // Form interactions
        this.enhanceFormInteractions();
        
        // List interactions
        this.enhanceListInteractions();
    }
    
    handleTouchStart(e) {
        const timestamp = Date.now();
        
        Array.from(e.changedTouches).forEach(touch => {
            this.touches.set(touch.identifier, {
                startX: touch.clientX,
                startY: touch.clientY,
                currentX: touch.clientX,
                currentY: touch.clientY,
                startTime: timestamp,
                target: e.target,
                moved: false
            });
        });
        
        // Handle multi-touch
        if (e.touches.length === 2) {
            this.handlePinchStart(e);
        }
    }
    
    handleTouchMove(e) {
        Array.from(e.changedTouches).forEach(touch => {
            const touchData = this.touches.get(touch.identifier);
            if (touchData) {
                touchData.currentX = touch.clientX;
                touchData.currentY = touch.clientY;
                touchData.moved = true;
                
                // Calculate movement
                const deltaX = touchData.currentX - touchData.startX;
                const deltaY = touchData.currentY - touchData.startY;
                const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
                
                if (distance > 10) {
                    touchData.moved = true;
                }
            }
        });
        
        // Handle pinch
        if (e.touches.length === 2) {
            this.handlePinchMove(e);
        }
    }
    
    handleTouchEnd(e) {
        const timestamp = Date.now();
        
        Array.from(e.changedTouches).forEach(touch => {
            const touchData = this.touches.get(touch.identifier);
            if (touchData) {
                const deltaX = touchData.currentX - touchData.startX;
                const deltaY = touchData.currentY - touchData.startY;
                const duration = timestamp - touchData.startTime;
                const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
                const velocity = distance / duration;
                
                // Determine gesture
                this.detectGesture(touchData, deltaX, deltaY, duration, velocity, e);
                
                this.touches.delete(touch.identifier);
            }
        });
    }
    
    handleTouchCancel(e) {
        Array.from(e.changedTouches).forEach(touch => {
            this.touches.delete(touch.identifier);
        });
    }
    
    detectGesture(touchData, deltaX, deltaY, duration, velocity, originalEvent) {
        const absX = Math.abs(deltaX);
        const absY = Math.abs(deltaY);
        
        // Swipe detection
        if (velocity > this.settings.swipeVelocity && 
            (absX > this.settings.swipeThreshold || absY > this.settings.swipeThreshold)) {
            
            if (absX > absY) {
                // Horizontal swipe
                const direction = deltaX > 0 ? 'right' : 'left';
                this.triggerGesture(`swipe-${direction}`, {
                    target: touchData.target,
                    deltaX,
                    deltaY,
                    velocity,
                    originalEvent
                });
            } else {
                // Vertical swipe
                const direction = deltaY > 0 ? 'down' : 'up';
                this.triggerGesture(`swipe-${direction}`, {
                    target: touchData.target,
                    deltaX,
                    deltaY,
                    velocity,
                    originalEvent
                });
            }
        }
        // Tap detection
        else if (!touchData.moved && duration < this.settings.tapTimeout) {
            this.handleTapGesture(touchData, originalEvent);
        }
        // Long press detection
        else if (!touchData.moved && duration > this.settings.longPressTimeout) {
            this.triggerGesture('long-press', {
                target: touchData.target,
                duration,
                originalEvent
            });
        }
    }
    
    handleTapGesture(touchData, originalEvent) {
        const now = Date.now();
        const lastTap = this.lastTapTime || 0;
        const lastTapTarget = this.lastTapTarget;
        
        if (now - lastTap < this.settings.doubleTapTimeout && 
            lastTapTarget === touchData.target) {
            // Double tap
            this.triggerGesture('double-tap', {
                target: touchData.target,
                originalEvent
            });
            this.lastTapTime = 0; // Reset to prevent triple tap
        } else {
            // Single tap
            setTimeout(() => {
                if (this.lastTapTime === now) {
                    this.triggerGesture('tap', {
                        target: touchData.target,
                        originalEvent
                    });
                }
            }, this.settings.doubleTapTimeout);
        }
        
        this.lastTapTime = now;
        this.lastTapTarget = touchData.target;
    }
    
    handlePinchStart(e) {
        if (e.touches.length !== 2) return;
        
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        
        this.pinchData = {
            startDistance: this.getDistance(touch1, touch2),
            startScale: 1,
            target: e.target
        };
    }
    
    handlePinchMove(e) {
        if (e.touches.length !== 2 || !this.pinchData) return;
        
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        const currentDistance = this.getDistance(touch1, touch2);
        const scale = currentDistance / this.pinchData.startDistance;
        
        if (Math.abs(scale - this.pinchData.startScale) > 0.1) {
            this.triggerGesture('pinch', {
                target: this.pinchData.target,
                scale,
                originalEvent: e
            });
            this.pinchData.startScale = scale;
        }
    }
    
    getDistance(touch1, touch2) {
        const dx = touch1.clientX - touch2.clientX;
        const dy = touch1.clientY - touch2.clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }
    
    registerGesture(name, handler) {
        this.gestures.set(name, handler);
    }
    
    triggerGesture(name, data) {
        const handler = this.gestures.get(name);
        if (handler) {
            try {
                handler(data);
            } catch (error) {
                if (window.errorHandler) {
                    window.errorHandler.logError('Gesture Handler Error', {
                        gesture: name,
                        error: error.message
                    });
                }
            }
        }
        
        // Dispatch custom event
        const event = new CustomEvent(`cibozer-gesture-${name}`, {
            detail: data,
            bubbles: true
        });
        data.target.dispatchEvent(event);
    }
    
    // Gesture Handlers
    handleSwipeLeft(data) {
        const element = data.target.closest('.swipeable, .card, .modal');
        
        if (element?.classList.contains('meal-plan-card')) {
            this.handleMealPlanSwipe(element, 'left');
        } else if (element?.classList.contains('modal')) {
            this.handleModalSwipe(element, 'left');
        }
    }
    
    handleSwipeRight(data) {
        const element = data.target.closest('.swipeable, .card, .modal');
        
        if (element?.classList.contains('meal-plan-card')) {
            this.handleMealPlanSwipe(element, 'right');
        } else if (element?.classList.contains('modal')) {
            this.handleModalSwipe(element, 'right');
        } else {
            // Global back navigation on right swipe
            this.handleBackNavigation();
        }
    }
    
    handleSwipeUp(data) {
        const element = data.target.closest('.modal, .sheet');
        
        if (element?.classList.contains('modal')) {
            // Dismiss modal on swipe up
            const bsModal = bootstrap.Modal.getInstance(element);
            if (bsModal) {
                bsModal.hide();
            }
        }
    }
    
    handleSwipeDown(data) {
        // Pull to refresh gesture
        if (data.target.closest('.refresh-container') && window.scrollY === 0) {
            this.handlePullToRefresh();
        }
    }
    
    handleTap(data) {
        // Enhanced tap handling for better touch response
        const target = data.target;
        
        // Add visual feedback
        this.addTapFeedback(target);
        
        // Handle special tap targets
        if (target.classList.contains('tap-to-copy')) {
            this.handleTapToCopy(target);
        }
    }
    
    handleDoubleTap(data) {
        const target = data.target;
        
        if (target.closest('.zoomable')) {
            this.handleZoom(target);
        } else if (target.closest('.likeable')) {
            this.handleDoubleTapLike(target);
        }
    }
    
    handleLongPress(data) {
        const target = data.target;
        
        // Show context menu or additional options
        if (target.closest('.meal-plan-card')) {
            this.showMealPlanContextMenu(target, data.originalEvent);
        } else if (target.closest('.ingredient-item')) {
            this.showIngredientOptions(target, data.originalEvent);
        }
    }
    
    handlePinch(data) {
        const target = data.target.closest('.zoomable, .image-container');
        
        if (target) {
            this.handlePinchZoom(target, data.scale);
        }
    }
    
    // Enhancement Methods
    enhanceCardSwiping() {
        const cards = document.querySelectorAll('.meal-plan-card, .recipe-card');
        cards.forEach(card => {
            card.classList.add('swipeable');
            
            // Add swipe indicators
            if (!card.querySelector('.swipe-indicators')) {
                const indicators = document.createElement('div');
                indicators.className = 'swipe-indicators';
                indicators.innerHTML = `
                    <div class="swipe-action left">
                        <i class="fas fa-heart"></i>
                    </div>
                    <div class="swipe-action right">
                        <i class="fas fa-share"></i>
                    </div>
                `;
                card.appendChild(indicators);
            }
        });
    }
    
    enhanceModalGestures() {
        document.addEventListener('shown.bs.modal', (e) => {
            const modal = e.target;
            modal.classList.add('touch-enhanced');
            
            // Add swipe-to-dismiss indicator
            if (!modal.querySelector('.swipe-indicator')) {
                const indicator = document.createElement('div');
                indicator.className = 'swipe-indicator';
                indicator.innerHTML = '<div class="swipe-handle"></div>';
                modal.querySelector('.modal-content').prepend(indicator);
            }
        });
    }
    
    enhanceNavigationGestures() {
        // Add edge swipe zones for navigation
        const leftEdge = document.createElement('div');
        leftEdge.className = 'edge-swipe-zone left';
        leftEdge.style.cssText = `
            position: fixed;
            left: 0;
            top: 0;
            width: 20px;
            height: 100vh;
            z-index: 1000;
            pointer-events: none;
        `;
        
        document.body.appendChild(leftEdge);
    }
    
    enhanceFormInteractions() {
        // Improve form interactions on mobile
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            // Add form navigation gestures
            form.addEventListener('cibozer-gesture-swipe-left', (e) => {
                this.focusNextField(form, e.detail.target);
            });
            
            form.addEventListener('cibozer-gesture-swipe-right', (e) => {
                this.focusPreviousField(form, e.detail.target);
            });
        });
    }
    
    enhanceListInteractions() {
        const lists = document.querySelectorAll('.list-group, .ingredient-list');
        lists.forEach(list => {
            list.addEventListener('cibozer-gesture-swipe-left', (e) => {
                const item = e.detail.target.closest('.list-group-item, .ingredient-item');
                if (item) {
                    this.showItemActions(item);
                }
            });
        });
    }
    
    // Helper Methods
    handleMealPlanSwipe(card, direction) {
        if (direction === 'left') {
            // Like meal plan
            this.likeMealPlan(card);
        } else if (direction === 'right') {
            // Share meal plan
            this.shareMealPlan(card);
        }
    }
    
    handleModalSwipe(modal, direction) {
        if (direction === 'left' || direction === 'right') {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        }
    }
    
    handleBackNavigation() {
        if (window.history.length > 1) {
            window.history.back();
        }
    }
    
    handlePullToRefresh() {
        if (window.location.reload) {
            // Add visual feedback
            this.showPullToRefreshFeedback();
            setTimeout(() => {
                window.location.reload();
            }, 500);
        }
    }
    
    addTapFeedback(target) {
        target.classList.add('tap-feedback');
        setTimeout(() => {
            target.classList.remove('tap-feedback');
        }, 150);
    }
    
    showMealPlanContextMenu(target, event) {
        // Implementation would show context menu
        if (window.CibozerApp?.showNotification) {
            window.CibozerApp.showNotification('Long press detected on meal plan', 'info');
        }
    }
    
    likeMealPlan(card) {
        const likeBtn = card.querySelector('.like-btn, .favorite-btn');
        if (likeBtn) {
            likeBtn.click();
        }
        
        // Visual feedback
        this.showSwipeAction(card, 'liked');
    }
    
    shareMealPlan(card) {
        const shareBtn = card.querySelector('.share-btn');
        if (shareBtn) {
            shareBtn.click();
        }
        
        // Visual feedback
        this.showSwipeAction(card, 'shared');
    }
    
    showSwipeAction(card, action) {
        const feedback = document.createElement('div');
        feedback.className = `swipe-feedback ${action}`;
        feedback.textContent = action === 'liked' ? '❤️ Liked!' : '📤 Shared!';
        
        card.appendChild(feedback);
        
        setTimeout(() => {
            feedback.remove();
        }, 2000);
    }
    
    showPullToRefreshFeedback() {
        const feedback = document.createElement('div');
        feedback.className = 'pull-refresh-feedback';
        feedback.innerHTML = `
            <div class="spinner-border spinner-border-sm" role="status">
                <span class="visually-hidden">Refreshing...</span>
            </div>
            <span class="ms-2">Refreshing...</span>
        `;
        
        document.body.appendChild(feedback);
        
        setTimeout(() => {
            feedback.remove();
        }, 2000);
    }
    
    focusNextField(form, currentField) {
        const fields = Array.from(form.querySelectorAll('input, select, textarea'));
        const currentIndex = fields.indexOf(currentField);
        const nextField = fields[currentIndex + 1];
        
        if (nextField) {
            nextField.focus();
        }
    }
    
    focusPreviousField(form, currentField) {
        const fields = Array.from(form.querySelectorAll('input, select, textarea'));
        const currentIndex = fields.indexOf(currentField);
        const prevField = fields[currentIndex - 1];
        
        if (prevField) {
            prevField.focus();
        }
    }
}

// Add touch gesture styles
const style = document.createElement('style');
style.textContent = `
.tap-feedback {
    transform: scale(0.95);
    transition: transform 0.15s ease;
}

.swipe-indicators {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
    z-index: 1;
}

.swipe-action {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    width: 60px;
    height: 60px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    color: white;
    opacity: 0;
    transition: opacity 0.2s ease;
}

.swipe-action.left {
    left: 20px;
    background: #e74c3c;
}

.swipe-action.right {
    right: 20px;
    background: #3498db;
}

.swipe-feedback {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 14px;
    z-index: 1000;
    animation: swipeFeedback 2s ease forwards;
}

@keyframes swipeFeedback {
    0% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
    20% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
    80% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
    100% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
}

.swipe-indicator {
    display: flex;
    justify-content: center;
    padding: 8px;
}

.swipe-handle {
    width: 40px;
    height: 4px;
    background: #dee2e6;
    border-radius: 2px;
}

.pull-refresh-feedback {
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: white;
    padding: 12px 20px;
    border-radius: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    z-index: 1050;
    display: flex;
    align-items: center;
}

.touch-enhanced {
    touch-action: pan-y;
}

.no-zoom {
    touch-action: manipulation;
}
`;

document.head.appendChild(style);

// Initialize touch gestures when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (window.matchMedia('(pointer: coarse)').matches) {
        window.touchGestures = new TouchGestureHandler();
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TouchGestureHandler;
}
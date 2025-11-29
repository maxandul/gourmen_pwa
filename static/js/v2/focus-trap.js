/**
 * Focus Trap for Modals and Overlays
 * 
 * Ensures keyboard users stay within modal when tabbing
 * WCAG 2.1 compliant
 * 
 * Usage:
 *   const trap = new FocusTrap(modalElement);
 *   trap.activate();
 *   // ... when closing modal
 *   trap.deactivate();
 */

class FocusTrap {
  constructor(element) {
    this.element = element;
    this.focusableSelectors = [
      'a[href]',
      'button:not([disabled])',
      'textarea:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      '[tabindex]:not([tabindex="-1"])'
    ].join(', ');
    
    this.firstFocusableElement = null;
    this.lastFocusableElement = null;
    this.previousActiveElement = null;
    this.isActive = false;
    
    this.handleKeyDown = this.handleKeyDown.bind(this);
  }

  activate() {
    if (this.isActive) return;

    // Store currently focused element to restore later
    this.previousActiveElement = document.activeElement;

    // Get all focusable elements
    this.updateFocusableElements();

    // Focus first element
    if (this.firstFocusableElement) {
      this.firstFocusableElement.focus();
    }

    // Listen for Tab key
    this.element.addEventListener('keydown', this.handleKeyDown);
    
    this.isActive = true;
  }

  deactivate() {
    if (!this.isActive) return;

    // Remove event listener
    this.element.removeEventListener('keydown', this.handleKeyDown);

    // Restore focus to previous element
    if (this.previousActiveElement && this.previousActiveElement.focus) {
      this.previousActiveElement.focus();
    }

    this.isActive = false;
  }

  updateFocusableElements() {
    const focusableElements = this.element.querySelectorAll(this.focusableSelectors);
    const visibleFocusableElements = Array.from(focusableElements).filter(el => {
      return el.offsetParent !== null; // Check if element is visible
    });

    this.firstFocusableElement = visibleFocusableElements[0];
    this.lastFocusableElement = visibleFocusableElements[visibleFocusableElements.length - 1];
  }

  handleKeyDown(e) {
    // Only handle Tab key
    if (e.key !== 'Tab') return;

    // Update focusable elements in case DOM changed
    this.updateFocusableElements();

    // Shift + Tab (going backwards)
    if (e.shiftKey) {
      if (document.activeElement === this.firstFocusableElement) {
        e.preventDefault();
        this.lastFocusableElement.focus();
      }
    } 
    // Tab (going forwards)
    else {
      if (document.activeElement === this.lastFocusableElement) {
        e.preventDefault();
        this.firstFocusableElement.focus();
      }
    }
  }
}

/**
 * Helper function to create and manage focus trap
 */
function createFocusTrap(element) {
  return new FocusTrap(element);
}

// Export for module systems (optional)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { FocusTrap, createFocusTrap };
}


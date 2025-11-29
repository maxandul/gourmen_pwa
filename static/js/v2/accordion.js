/**
 * Accordion Component
 * 
 * Auto-initializes all accordions on page
 * Supports single and multiple open items
 * 
 * HTML:
 * <div class="accordion" data-accordion>
 *   <div class="accordion-item">
 *     <button class="accordion-item__header">...</button>
 *     <div class="accordion-item__content">...</div>
 *   </div>
 * </div>
 */

class Accordion {
  constructor(element, options = {}) {
    this.element = element;
    this.allowMultiple = options.allowMultiple !== false; // Default: true
    this.items = [];
    this.init();
  }

  init() {
    const items = this.element.querySelectorAll('.accordion-item');
    
    items.forEach((item, index) => {
      const header = item.querySelector('.accordion-item__header');
      const content = item.querySelector('.accordion-item__content');
      
      if (!header || !content) return;

      // Set up ARIA attributes
      const id = `accordion-${Date.now()}-${index}`;
      header.setAttribute('aria-controls', id);
      header.setAttribute('aria-expanded', item.classList.contains('accordion-item--open'));
      content.setAttribute('id', id);

      // Click handler
      header.addEventListener('click', () => this.toggle(item));

      this.items.push({ item, header, content });
    });
  }

  toggle(targetItem) {
    const isOpen = targetItem.classList.contains('accordion-item--open');

    // If not allowing multiple, close all others
    if (!this.allowMultiple && !isOpen) {
      this.items.forEach(({ item, header }) => {
        if (item !== targetItem) {
          item.classList.remove('accordion-item--open');
          header.setAttribute('aria-expanded', 'false');
        }
      });
    }

    // Toggle target
    if (isOpen) {
      this.close(targetItem);
    } else {
      this.open(targetItem);
    }
  }

  open(item) {
    const header = item.querySelector('.accordion-item__header');
    item.classList.add('accordion-item--open');
    header.setAttribute('aria-expanded', 'true');
  }

  close(item) {
    const header = item.querySelector('.accordion-item__header');
    item.classList.remove('accordion-item--open');
    header.setAttribute('aria-expanded', 'false');
  }

  openAll() {
    this.items.forEach(({ item }) => this.open(item));
  }

  closeAll() {
    this.items.forEach(({ item }) => this.close(item));
  }
}

/**
 * Auto-initialize all accordions on page
 */
function initAccordions() {
  const accordions = document.querySelectorAll('[data-accordion]');
  accordions.forEach(element => {
    const allowMultiple = element.hasAttribute('data-allow-multiple');
    new Accordion(element, { allowMultiple });
  });
}

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAccordions);
} else {
  initAccordions();
}

// Export for module systems (optional)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { Accordion, initAccordions };
}


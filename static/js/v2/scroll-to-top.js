/**
 * Scroll to Top Button
 * 
 * Auto-shows when user scrolls down 300px
 * Smooth scrolls to top on click
 */

class ScrollToTop {
  constructor(options = {}) {
    this.threshold = options.threshold || 300;
    this.button = null;
    this.init();
  }

  init() {
    this.createButton();
    this.attachEvents();
  }

  createButton() {
    // Check if button already exists
    if (document.querySelector('.scroll-to-top')) {
      this.button = document.querySelector('.scroll-to-top');
      return;
    }

    // Create button
    this.button = document.createElement('button');
    this.button.className = 'scroll-to-top';
    this.button.setAttribute('aria-label', 'Scroll to top');
    this.button.innerHTML = `
      <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="12" y1="19" x2="12" y2="5"/>
        <polyline points="5 12 12 5 19 12"/>
      </svg>
    `;

    document.body.appendChild(this.button);
  }

  attachEvents() {
    // Show/hide on scroll
    window.addEventListener('scroll', () => this.handleScroll(), { passive: true });

    // Click to scroll to top
    this.button.addEventListener('click', () => this.scrollToTop());
  }

  handleScroll() {
    const scrolled = window.pageYOffset || document.documentElement.scrollTop;

    if (scrolled > this.threshold) {
      this.show();
    } else {
      this.hide();
    }
  }

  show() {
    this.button.classList.add('scroll-to-top--visible');
  }

  hide() {
    this.button.classList.remove('scroll-to-top--visible');
  }

  scrollToTop() {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  }
}

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new ScrollToTop();
  });
} else {
  new ScrollToTop();
}

// Export for module systems (optional)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ScrollToTop;
}


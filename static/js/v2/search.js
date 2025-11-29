/**
 * Instant Search Component
 * 
 * Auto-initializes all search fields on page
 * Filters target elements in real-time
 * 
 * HTML:
 * <div class="search-field" data-search data-search-target=".event-card">
 *   <svg class="search-field__icon">...</svg>
 *   <input type="search" class="search-field__input" placeholder="Suchen...">
 *   <button class="search-field__clear">×</button>
 * </div>
 */

class InstantSearch {
  constructor(element) {
    this.element = element;
    this.input = element.querySelector('.search-field__input');
    this.clearBtn = element.querySelector('.search-field__clear');
    this.targetSelector = element.dataset.searchTarget || '.card';
    this.searchAttribute = element.dataset.searchAttribute || 'data-search-text';
    this.debounceMs = parseInt(element.dataset.searchDebounce) || 150;
    this.debounceTimer = null;
    
    this.init();
  }

  init() {
    if (!this.input) return;

    // Input event with debounce
    this.input.addEventListener('input', (e) => {
      this.handleInput(e.target.value);
    });

    // Clear button
    if (this.clearBtn) {
      this.clearBtn.addEventListener('click', () => {
        this.clear();
      });
    }

    // Update clear button visibility
    this.updateClearButton();
  }

  handleInput(value) {
    // Update clear button
    this.updateClearButton();

    // Debounce search
    clearTimeout(this.debounceTimer);
    this.debounceTimer = setTimeout(() => {
      this.search(value);
    }, this.debounceMs);
  }

  search(query) {
    const normalizedQuery = query.toLowerCase().trim();
    const targets = document.querySelectorAll(this.targetSelector);
    let visibleCount = 0;

    targets.forEach(target => {
      // Get search text from attribute or innerText
      const searchText = (
        target.getAttribute(this.searchAttribute) || 
        target.innerText
      ).toLowerCase();

      const matches = searchText.includes(normalizedQuery);

      if (matches || normalizedQuery === '') {
        target.style.display = '';
        visibleCount++;
      } else {
        target.style.display = 'none';
      }
    });

    // Dispatch custom event with results
    this.element.dispatchEvent(new CustomEvent('search', {
      detail: {
        query,
        totalResults: targets.length,
        visibleResults: visibleCount
      }
    }));

    // Optional: Show "no results" message
    this.showNoResults(visibleCount === 0 && query !== '');
  }

  clear() {
    this.input.value = '';
    this.input.focus();
    this.search('');
    this.updateClearButton();
  }

  updateClearButton() {
    const hasValue = this.input.value.length > 0;
    
    if (hasValue) {
      this.element.classList.add('search-field--has-value');
    } else {
      this.element.classList.remove('search-field--has-value');
    }
  }

  showNoResults(show) {
    // Optional: Implement "no results" message
    const existingMessage = document.querySelector('[data-search-no-results]');
    
    if (show && !existingMessage) {
      const message = document.createElement('div');
      message.className = 'search-no-results';
      message.setAttribute('data-search-no-results', '');
      message.innerHTML = `
        <p style="text-align: center; padding: 2rem; color: var(--color-text-secondary);">
          Keine Ergebnisse gefunden
        </p>
      `;
      
      // Insert after search field or at target container
      const container = document.querySelector(this.targetSelector)?.parentElement;
      if (container) {
        container.appendChild(message);
      }
    } else if (!show && existingMessage) {
      existingMessage.remove();
    }
  }
}

/**
 * Auto-initialize all search fields on page
 */
function initSearchFields() {
  const searchFields = document.querySelectorAll('[data-search]');
  searchFields.forEach(element => {
    new InstantSearch(element);
  });
}

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initSearchFields);
} else {
  initSearchFields();
}

// Export for module systems (optional)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { InstantSearch, initSearchFields };
}


/**
 * Theme Manager - Light/Dark Mode Switching
 * 
 * Features:
 * - Prevents FOUC (Flash of Unstyled Content)
 * - Respects system preferences
 * - Persists user choice in localStorage
 * - Smooth transitions
 * - Accessibility compliant
 */

class ThemeManager {
  constructor() {
    this.themeKey = 'theme';
    this.defaultTheme = 'dark'; // Entspricht deiner Präferenz
    this.html = document.documentElement;
    this.mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    this.init();
  }

  /**
   * Initialize theme on page load
   * Must run BEFORE CSS loads to prevent FOUC
   */
  init() {
    // Get theme from localStorage or system preference
    const theme = this.getTheme();
    
    // Apply immediately (before CSS loads)
    this.applyTheme(theme, false); // false = no transition on init
    
    // Listen for system preference changes (only if no manual override)
    this.mediaQuery.addEventListener('change', (e) => {
      if (!localStorage.getItem(this.themeKey)) {
        this.applyTheme(e.matches ? 'dark' : 'light', true);
      }
    });
  }

  /**
   * Get current theme
   * Priority: localStorage > system preference > default
   */
  getTheme() {
    const saved = localStorage.getItem(this.themeKey);
    if (saved && (saved === 'light' || saved === 'dark')) {
      return saved;
    }
    
    // Fallback to system preference
    if (this.mediaQuery.matches) {
      return 'dark';
    }
    return 'light';
  }

  /**
   * Apply theme to document
   * @param {string} theme - 'light' or 'dark'
   * @param {boolean} transition - Enable smooth transition
   */
  applyTheme(theme, transition = true) {
    // Validate theme
    if (theme !== 'light' && theme !== 'dark') {
      console.warn(`Invalid theme: ${theme}. Using default.`);
      theme = this.defaultTheme;
    }

    // Set data attribute (triggers CSS custom properties)
    this.html.setAttribute('data-theme', theme);
    
    // Update meta theme-color for mobile browsers
    this.updateMetaThemeColor(theme);
    
    // Dispatch custom event for other scripts
    this.html.dispatchEvent(new CustomEvent('themechange', {
      detail: { theme }
    }));

    // Enable transitions after initial load
    if (transition) {
      this.enableTransitions();
    }
  }

  /**
   * Toggle between light and dark
   */
  toggle() {
    const current = this.getTheme();
    const newTheme = current === 'dark' ? 'light' : 'dark';
    this.setTheme(newTheme);
    return newTheme;
  }

  /**
   * Set theme explicitly (saves to localStorage)
   * @param {string} theme - 'light' or 'dark'
   */
  setTheme(theme) {
    // Save preference (overrides system preference)
    localStorage.setItem(this.themeKey, theme);
    
    // Apply theme
    this.applyTheme(theme, true);
  }

  /**
   * Reset to system preference (removes localStorage override)
   */
  resetToSystem() {
    localStorage.removeItem(this.themeKey);
    const systemTheme = this.mediaQuery.matches ? 'dark' : 'light';
    this.applyTheme(systemTheme, true);
  }

  /**
   * Update meta theme-color for mobile browsers
   */
  updateMetaThemeColor(theme) {
    let metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (!metaThemeColor) {
      metaThemeColor = document.createElement('meta');
      metaThemeColor.setAttribute('name', 'theme-color');
      document.head.appendChild(metaThemeColor);
    }
    
    // Use your brand colors
    const colors = {
      dark: '#1b232e',  // Logo Navy Dark
      light: '#ffffff'   // White
    };
    
    metaThemeColor.setAttribute('content', colors[theme] || colors.dark);
  }

  /**
   * Enable smooth transitions (only after initial load)
   */
  enableTransitions() {
    // Add class to enable transitions
    this.html.classList.add('theme-transition');
    
    // Remove after transition completes
    setTimeout(() => {
      this.html.classList.remove('theme-transition');
    }, 300);
  }

  /**
   * Get current theme
   */
  getCurrentTheme() {
    return this.getTheme();
  }
}

// Create global instance
const themeManager = new ThemeManager();

// Make available globally
window.themeManager = themeManager;

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = themeManager;
}


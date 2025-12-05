/**
 * Theme Toggle Button Component
 * 
 * Auto-initializes all theme toggle buttons on page
 * 
 * HTML:
 * <button id="theme-toggle" class="btn btn--ghost" aria-label="Theme wechseln">
 *   <svg class="icon icon--theme-light" aria-hidden="true">...</svg>
 *   <svg class="icon icon--theme-dark" aria-hidden="true">...</svg>
 *   <span class="theme-toggle__text">Dark Mode</span>
 * </button>
 */

class ThemeToggle {
  constructor(button) {
    this.button = button;
    this.iconLight = button.querySelector('.icon--theme-light');
    this.iconDark = button.querySelector('.icon--theme-dark');
    
    this.init();
  }

  init() {
    // Update button state
    this.updateState();
    
    // Click handler
    this.button.addEventListener('click', () => {
      if (typeof themeManager === 'undefined' && typeof window.themeManager === 'undefined') {
        console.error('ThemeManager not available');
        return;
      }
      
      const manager = themeManager || window.themeManager;
      const newTheme = manager.toggle();
      this.updateState();
      
      // Optional: Announce to screen readers
      this.announceThemeChange(newTheme);
    });
    
    // Listen for theme changes (from other sources)
    document.documentElement.addEventListener('themechange', (e) => {
      this.updateState();
    });
  }

  updateState() {
    if (typeof themeManager === 'undefined' && typeof window.themeManager === 'undefined') {
      console.warn('ThemeManager not available');
      return;
    }
    
    const manager = themeManager || window.themeManager;
    const currentTheme = manager.getCurrentTheme();
    const isDark = currentTheme === 'dark';
    
    // Update icons - use block instead of inline for absolute positioning
    if (this.iconLight) {
      this.iconLight.style.display = isDark ? 'none' : 'block';
      this.iconLight.style.opacity = isDark ? '0' : '1';
    }
    if (this.iconDark) {
      this.iconDark.style.display = isDark ? 'block' : 'none';
      this.iconDark.style.opacity = isDark ? '1' : '0';
    }
    
    // Update aria-label
    this.button.setAttribute(
      'aria-label',
      `Zu ${isDark ? 'Light' : 'Dark'} Mode wechseln`
    );
  }

  announceThemeChange(theme) {
    // Create temporary live region for screen readers
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', 'polite');
    announcement.className = 'sr-only';
    announcement.textContent = `Theme zu ${theme === 'dark' ? 'Dark' : 'Light'} Mode geändert`;
    
    document.body.appendChild(announcement);
    
    setTimeout(() => {
      announcement.remove();
    }, 1000);
  }
}

/**
 * Auto-initialize all theme toggle buttons
 */
function initThemeToggles() {
  // Wait for themeManager to be available
  if (typeof themeManager === 'undefined' && typeof window.themeManager === 'undefined') {
    console.warn('ThemeManager not loaded yet, retrying...');
    setTimeout(initThemeToggles, 100);
    return;
  }
  
  const buttons = document.querySelectorAll('#theme-toggle, [data-theme-toggle]');
  
  if (buttons.length === 0) {
    console.warn('No theme toggle buttons found');
    return;
  }
  
  buttons.forEach(button => {
    new ThemeToggle(button);
  });
}

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initThemeToggles);
} else {
  initThemeToggles();
}

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { ThemeToggle, initThemeToggles };
}


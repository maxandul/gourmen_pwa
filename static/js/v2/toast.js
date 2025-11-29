/**
 * Toast Notification System
 * 
 * Usage:
 *   Toast.success('Gespeichert!', 'Deine Änderungen wurden erfolgreich gespeichert.');
 *   Toast.error('Fehler!', 'Bitte versuche es erneut.');
 *   Toast.warning('Achtung!', 'Dieser Vorgang kann nicht rückgängig gemacht werden.');
 *   Toast.info('Info', 'Neue Nachricht verfügbar.');
 *   
 * With action button (Undo pattern):
 *   Toast.info('Event gelöscht', null, {
 *     action: 'Rückgängig',
 *     onAction: () => undoDelete()
 *   });
 */

class ToastManager {
  constructor() {
    this.container = null;
    this.toasts = new Map();
    this.init();
  }

  init() {
    // Create container if it doesn't exist
    if (!document.querySelector('.toast-container')) {
      this.container = document.createElement('div');
      this.container.className = 'toast-container';
      document.body.appendChild(this.container);
    } else {
      this.container = document.querySelector('.toast-container');
    }
  }

  /**
   * Show a toast notification
   * @param {string} type - 'success', 'error', 'warning', or 'info'
   * @param {string} title - Toast title
   * @param {string} message - Toast message (optional)
   * @param {object} options - Additional options
   */
  show(type, title, message = null, options = {}) {
    const {
      duration = 5000,
      action = null,
      onAction = null,
      closeable = true
    } = options;

    const id = this.generateId();
    const toast = this.createToastElement(id, type, title, message, action, closeable);

    this.toasts.set(id, {
      element: toast,
      timeout: null,
      onAction
    });

    this.container.appendChild(toast);

    // Auto-dismiss after duration
    if (duration > 0) {
      const timeout = setTimeout(() => this.dismiss(id), duration);
      this.toasts.get(id).timeout = timeout;
    }

    // Trigger animation
    requestAnimationFrame(() => {
      toast.style.opacity = '1';
      toast.style.transform = 'translateY(0)';
    });

    return id;
  }

  createToastElement(id, type, title, message, action, closeable) {
    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('data-toast-id', id);

    const iconSvg = this.getIcon(type);

    let html = `
      ${iconSvg}
      <div class="toast__content">
        <div class="toast__title">${title}</div>
        ${message ? `<p class="toast__message">${message}</p>` : ''}
        ${action ? `
          <div class="toast__action">
            <button class="btn btn--sm btn--ghost" data-toast-action="${id}">
              ${action}
            </button>
          </div>
        ` : ''}
      </div>
      ${closeable ? `
        <button class="toast__close" aria-label="Schließen" data-toast-close="${id}">
          ×
        </button>
      ` : ''}
    `;

    toast.innerHTML = html;

    // Event listeners
    if (closeable) {
      const closeBtn = toast.querySelector(`[data-toast-close="${id}"]`);
      closeBtn.addEventListener('click', () => this.dismiss(id));
    }

    if (action) {
      const actionBtn = toast.querySelector(`[data-toast-action="${id}"]`);
      actionBtn.addEventListener('click', () => {
        const toastData = this.toasts.get(id);
        if (toastData && toastData.onAction) {
          toastData.onAction();
        }
        this.dismiss(id);
      });
    }

    return toast;
  }

  getIcon(type) {
    const icons = {
      success: '<svg class="toast__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
      error: '<svg class="toast__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
      warning: '<svg class="toast__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
      info: '<svg class="toast__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
    };
    return icons[type] || icons.info;
  }

  dismiss(id) {
    const toastData = this.toasts.get(id);
    if (!toastData) return;

    const { element, timeout } = toastData;

    // Clear timeout
    if (timeout) {
      clearTimeout(timeout);
    }

    // Animate out
    element.style.opacity = '0';
    element.style.transform = 'translateX(100%)';

    setTimeout(() => {
      element.remove();
      this.toasts.delete(id);
    }, 200);
  }

  dismissAll() {
    this.toasts.forEach((_, id) => this.dismiss(id));
  }

  generateId() {
    return `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  // Convenience methods
  success(title, message, options) {
    return this.show('success', title, message, options);
  }

  error(title, message, options) {
    return this.show('error', title, message, options);
  }

  warning(title, message, options) {
    return this.show('warning', title, message, options);
  }

  info(title, message, options) {
    return this.show('info', title, message, options);
  }
}

// Create global instance
const Toast = new ToastManager();

// Export for module systems (optional)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = Toast;
}


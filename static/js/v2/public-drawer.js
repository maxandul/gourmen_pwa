/**
 * Oeffentliche Top-Navigation: Modal-Drawer (< 1024px) fuer Start / Hitlist.
 * Steuert aria-expanded am Hamburger-Button; schliesst bei Link-Klick und Backdrop-Klick.
 */
(function () {
  'use strict';

  var dialog = document.getElementById('public-nav-drawer');
  var btn = document.getElementById('public-nav-menu-btn');
  if (!dialog || !btn || typeof dialog.showModal !== 'function') {
    return;
  }

  function setExpanded(open) {
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  }

  function openDrawer() {
    try {
      dialog.showModal();
      setExpanded(true);
    } catch (e) {
      /* Ungueltiger Zustand oder Dialog nicht nutzbar */
    }
  }

  function closeDrawer() {
    if (!dialog.open) {
      return;
    }
    dialog.close();
    setExpanded(false);
    try {
      btn.focus();
    } catch (e2) {
      /* Fokus optional */
    }
  }

  btn.addEventListener('click', function () {
    if (dialog.open) {
      closeDrawer();
    } else {
      openDrawer();
    }
  });

  dialog.querySelectorAll('[data-drawer-close]').forEach(function (el) {
    el.addEventListener('click', function () {
      closeDrawer();
    });
  });

  dialog.querySelectorAll('.public-drawer__link').forEach(function (a) {
    a.addEventListener('click', closeDrawer);
  });

  dialog.addEventListener('cancel', function () {
    setExpanded(false);
  });

  dialog.addEventListener('close', function () {
    setExpanded(false);
  });

  dialog.addEventListener('click', function (e) {
    if (e.target === dialog) {
      closeDrawer();
    }
  });
})();

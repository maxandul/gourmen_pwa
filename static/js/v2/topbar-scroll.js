/**
 * Topbar Hide-on-Scroll (Mobile + Tablet < 1024px)
 *
 * Versteckt die User-Bar beim Runterscrollen ab einem Schwellwert und
 * holt sie beim Hochscrollen oder ganz oben wieder zurueck. Auf Desktop
 * (>= 1024px) bleibt die Topbar starr fixed.
 *
 * Toggelt body[data-topbar-hidden="true"]. Sticky-Tabs reagieren via
 * CSS-Variable --topbar-offset und ruecken automatisch nach oben.
 *
 * Pausiert (laesst Topbar sichtbar), solange ein modales Element offen
 * ist - sonst springt der Header beim Bedienen eines Dialogs wild.
 *
 * Respektiert prefers-reduced-motion: die CSS-Transition ist dann aus,
 * der Toggle bleibt aber funktional (instant statt smooth).
 */
(function () {
  'use strict';

  var MQ = window.matchMedia('(max-width: 1023px)');

  // Schwellwerte: down erst ab 16px Delta verstecken,
  // up schon ab 4px wieder einblenden (asymmetrisch, mobil-typisch).
  var THRESHOLD_DOWN = 16;
  var THRESHOLD_UP = 4;
  // Im obersten Bereich der Seite Topbar immer zeigen.
  var TOP_RESERVE = 80;

  var lastY = window.scrollY;
  var hidden = false;
  var ticking = false;
  var listenerAttached = false;

  function isModalOpen() {
    // Generische Dialog-Detection (Modal, User-Menu offen, Sidebar-Drawer).
    if (document.querySelector('[role="dialog"][aria-modal="true"]:not([hidden])')) {
      return true;
    }
    if (document.querySelector('details.user-menu[open]')) {
      return true;
    }
    if (document.body.getAttribute('data-sidebar-open') === 'true') {
      return true;
    }
    return false;
  }

  function show() {
    if (!hidden) return;
    document.body.removeAttribute('data-topbar-hidden');
    hidden = false;
  }

  function hide() {
    if (hidden) return;
    document.body.setAttribute('data-topbar-hidden', 'true');
    hidden = true;
  }

  function update() {
    ticking = false;

    if (!MQ.matches) {
      show();
      return;
    }

    var y = window.scrollY;
    var delta = y - lastY;

    // Ganz oben: Topbar immer zeigen, Baseline zuruecksetzen.
    if (y < TOP_RESERVE) {
      show();
      lastY = y;
      return;
    }

    if (isModalOpen()) {
      lastY = y;
      return;
    }

    if (delta > THRESHOLD_DOWN) {
      hide();
      lastY = y;
    } else if (delta < -THRESHOLD_UP) {
      show();
      lastY = y;
    }
  }

  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(update);
  }

  function attachListeners() {
    if (listenerAttached) return;
    window.addEventListener('scroll', onScroll, { passive: true });
    listenerAttached = true;
  }

  function detachListeners() {
    if (!listenerAttached) return;
    window.removeEventListener('scroll', onScroll, { passive: true });
    listenerAttached = false;
  }

  function applyForCurrentViewport() {
    if (MQ.matches) {
      attachListeners();
    } else {
      detachListeners();
      show();
    }
  }

  // Beim Wechsel Mobile <-> Desktop (z. B. Window-Resize) Logik anpassen.
  if (typeof MQ.addEventListener === 'function') {
    MQ.addEventListener('change', applyForCurrentViewport);
  } else if (typeof MQ.addListener === 'function') {
    MQ.addListener(applyForCurrentViewport);
  }

  applyForCurrentViewport();
})();

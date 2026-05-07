/**
 * Horizontaler Scroll-Hinweis (rechter Edge-Fade) fuer breite data-table-Huellen.
 * Markup: .data-table-scroll-outer > .data-table-scroll-inner (table-responsive.data-table-wrap)
 */
(function () {
  'use strict';

  /** @type {Map<Element, () => void>} */
  const registry = new Map();

  /** @type {Map<Element, () => void>} */
  const gglRankCleanups = new Map();

  function syncGglRankStickyWidth(table) {
    const cells = table.querySelectorAll('.ggl-ranking-table__col-rank');
    if (!cells.length) return;
    var maxPx = 0;
    for (var i = 0; i < cells.length; i++) {
      var w = cells[i].getBoundingClientRect().width;
      if (w > maxPx) maxPx = w;
    }
    if (maxPx > 0) {
      table.style.setProperty('--ggl-rank-col-outer', Math.ceil(maxPx) + 'px');
    }
  }

  function setupGglRankSticky(table) {
    function runSync() {
      syncGglRankStickyWidth(table);
    }

    function runSyncRaf() {
      requestAnimationFrame(function () {
        runSync();
        requestAnimationFrame(runSync);
      });
    }

    window.addEventListener('resize', runSync, { passive: true });

    var ro = null;
    if (typeof ResizeObserver !== 'undefined') {
      ro = new ResizeObserver(runSync);
      ro.observe(table);
      var inner = table.closest('.data-table-scroll-inner');
      if (inner) ro.observe(inner);
    }

    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(runSyncRaf);
    }
    runSyncRaf();

    return function cleanup() {
      window.removeEventListener('resize', runSync);
      if (ro) ro.disconnect();
      table.style.removeProperty('--ggl-rank-col-outer');
    };
  }

  function teardownGglRankIn(root) {
    root.querySelectorAll('table.ggl-ranking-table').forEach(function (table) {
      var fn = gglRankCleanups.get(table);
      if (fn) {
        fn();
        gglRankCleanups.delete(table);
      }
    });
  }

  function initGglRankIn(root) {
    root.querySelectorAll('table.ggl-ranking-table').forEach(function (table) {
      var existing = gglRankCleanups.get(table);
      if (existing) existing();
      gglRankCleanups.set(table, setupGglRankSticky(table));
    });
  }

  function teardownIn(root) {
    teardownGglRankIn(root);
    root.querySelectorAll('.data-table-scroll-outer').forEach((outer) => {
      const fn = registry.get(outer);
      if (fn) {
        fn();
        registry.delete(outer);
      }
    });
  }

  function bindPair(inner, outer) {
    const slack = 2;
    function updateFade() {
      const hasOverflow = inner.scrollWidth > inner.clientWidth + slack;
      const atEnd = inner.scrollLeft + inner.clientWidth >= inner.scrollWidth - slack;
      outer.classList.toggle(
        'data-table-scroll-outer--fade-right',
        hasOverflow && !atEnd,
      );
    }

    inner.addEventListener('scroll', updateFade, { passive: true });
    window.addEventListener('resize', updateFade, { passive: true });
    let ro = null;
    if (typeof ResizeObserver !== 'undefined') {
      ro = new ResizeObserver(updateFade);
      ro.observe(inner);
    }

    updateFade();

    return function cleanup() {
      inner.removeEventListener('scroll', updateFade);
      window.removeEventListener('resize', updateFade);
      if (ro) ro.disconnect();
      outer.classList.remove('data-table-scroll-outer--fade-right');
    };
  }

  function initIn(root) {
    teardownIn(root);
    root.querySelectorAll('.data-table-scroll-inner').forEach((inner) => {
      const outer = inner.closest('.data-table-scroll-outer');
      if (!outer) return;
      registry.set(outer, bindPair(inner, outer));
    });
    initGglRankIn(root);
  }

  function bindApis(fn) {
    return function (root) {
      fn(root || document);
    };
  }

  window.gourmenTeardownRestaurantsTableScroll = teardownIn;
  window.gourmenInitRestaurantsTableScroll = bindApis(initIn);
  window.gourmenTeardownDataTableScroll = teardownIn;
  window.gourmenInitDataTableScroll = bindApis(initIn);

  function boot() {
    initIn(document);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();

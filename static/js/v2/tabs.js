/**
 * Tabs Fade Controller
 * Zeigt Fades links/rechts auf dem Container an, wenn overflowed.
 */
(function () {
  const containers = Array.from(document.querySelectorAll('.tabs'));
  if (!containers.length) return;

  const THRESHOLD = 2; // kleine Toleranz für Rundung

  const scrollActiveTabIntoView = (nav) => {
    const active = nav.querySelector('.tabs__tab--active');
    if (!active) return;
    active.scrollIntoView({
      block: 'nearest',
      inline: 'center',
      behavior: 'auto',
    });
  };

  const update = (container, nav) => {
    const maxScroll = nav.scrollWidth - nav.clientWidth;
    if (maxScroll <= 0) {
      container.classList.remove('tabs--fade-left', 'tabs--fade-right');
      return;
    }

    const atStart = nav.scrollLeft <= THRESHOLD;
    const atEnd = nav.scrollLeft >= (maxScroll - THRESHOLD);

    container.classList.toggle('tabs--fade-left', !atStart);
    container.classList.toggle('tabs--fade-right', !atEnd);
  };

  const sameQueryWithoutTab = (a, b) => {
    const paramsA = new URLSearchParams(a.search);
    const paramsB = new URLSearchParams(b.search);
    paramsA.delete('tab');
    paramsB.delete('tab');
    return paramsA.toString() === paramsB.toString();
  };

  const activateTab = (container, tabs, panels, nextIndex) => {
    tabs.forEach((tab, idx) => {
      const isActive = idx === nextIndex;
      tab.classList.toggle('tabs__tab--active', isActive);
      tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });

    panels.forEach((panel, idx) => {
      panel.classList.toggle('tabs__panel--active', idx === nextIndex);
    });
  };

  containers.forEach((container) => {
    const nav = container.querySelector('.tabs__nav');
    if (!nav) return;

    const tabs = Array.from(nav.querySelectorAll('.tabs__tab[href]'));
    const panels = Array.from(container.querySelectorAll('.tabs__panel'));

    if (tabs.length && panels.length && tabs.length === panels.length) {
      tabs.forEach((tab, idx) => {
        tab.addEventListener('click', (event) => {
          if (
            event.defaultPrevented ||
            event.button !== 0 ||
            event.metaKey ||
            event.ctrlKey ||
            event.shiftKey ||
            event.altKey
          ) {
            return;
          }

          const targetUrl = new URL(tab.href, window.location.href);
          const currentUrl = new URL(window.location.href);

          // Nur dann clientseitig umschalten, wenn wir auf derselben Seite bleiben
          // und sich ausschließlich der tab-Parameter ändert.
          if (
            targetUrl.pathname !== currentUrl.pathname ||
            !sameQueryWithoutTab(currentUrl, targetUrl)
          ) {
            return;
          }

          event.preventDefault();
          if (!tab.classList.contains('tabs__tab--active')) {
            activateTab(container, tabs, panels, idx);
            window.history.pushState({}, '', targetUrl.toString());
          }
        });
      });

      window.addEventListener('popstate', () => {
        const currentUrl = new URL(window.location.href);
        const tabValue = currentUrl.searchParams.get('tab');
        if (!tabValue) return;

        const matchIndex = tabs.findIndex((tab) => {
          const tabUrl = new URL(tab.href, window.location.href);
          return tabUrl.searchParams.get('tab') === tabValue;
        });

        if (matchIndex >= 0) {
          activateTab(container, tabs, panels, matchIndex);
        }
      });
    }

    const handler = () => update(container, nav);
    handler();
    requestAnimationFrame(() => scrollActiveTabIntoView(nav));

    nav.addEventListener('scroll', handler, { passive: true });
    window.addEventListener('resize', handler, { passive: true });
  });
})();

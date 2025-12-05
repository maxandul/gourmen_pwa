/**
 * Tabs Fade Controller
 * Zeigt Fades links/rechts auf dem Container an, wenn overflowed.
 */
(function () {
  const containers = Array.from(document.querySelectorAll('.tabs'));
  if (!containers.length) return;

  const THRESHOLD = 2; // kleine Toleranz für Rundung

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

  containers.forEach((container) => {
    const nav = container.querySelector('.tabs__nav');
    if (!nav) return;

    const handler = () => update(container, nav);
    handler();

    nav.addEventListener('scroll', handler, { passive: true });
    window.addEventListener('resize', handler, { passive: true });
  });
})();

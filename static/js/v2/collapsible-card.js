document.addEventListener('DOMContentLoaded', () => {
  const cards = document.querySelectorAll('.card.card--collapsible');
  cards.forEach((card) => {
    const toggle = card.querySelector('.card__toggle');
    const content = card.querySelector('.card__collapsible-content');
    if (!toggle || !content) return;

    const isCollapsed = card.classList.contains('is-collapsed');
    toggle.setAttribute('aria-expanded', String(!isCollapsed));

    toggle.addEventListener('click', () => {
      const collapsed = card.classList.toggle('is-collapsed');
      toggle.setAttribute('aria-expanded', String(!collapsed));
    });
  });
});


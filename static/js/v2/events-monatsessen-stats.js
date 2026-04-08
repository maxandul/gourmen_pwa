document.addEventListener('DOMContentLoaded', () => {
  const dataEl = document.getElementById('events-monatsessen-charts-data');
  if (!dataEl || !window.Chart) return;

  let payload;
  try {
    payload = JSON.parse(dataEl.textContent.trim());
  } catch (e) {
    console.error('events-monatsessen-charts-data parse error', e);
    return;
  }

  const gridColor = 'rgba(0, 0, 0, 0.08)';
  const tickColor = '#64748b';
  const barColors = [
    '#dc693c', '#73c8a8', '#45b7d1', '#96ceb4', '#8a9db1',
    '#f88958', '#2fa885', '#667a91', '#f59e0b', '#4f6477',
    '#ff9f43', '#10ac84', '#ee5a24', '#0984e3', '#bb8fce',
  ];

  const TOP_RESTAURANTS = 10;

  function barChart(canvasId, labels, values, xTitle) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !labels.length) return;

    const colors = labels.map((_, i) => barColors[i % barColors.length]);

    const chart = new Chart(canvas.getContext('2d'), {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: xTitle,
          data: values,
          backgroundColor: colors.map((c) => `${c}cc`),
          borderColor: colors,
          borderWidth: 1,
        }],
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label(ctx) {
                const v = ctx.parsed.x;
                if (xTitle.includes('%')) return `${v} %`;
                if (xTitle.includes('CHF')) return `${v} CHF`;
                return `${v}`;
              },
            },
          },
        },
        scales: {
          x: {
            title: { display: true, text: xTitle, font: { size: 12, weight: '600' } },
            beginAtZero: true,
            grid: { color: gridColor },
            ticks: { color: tickColor },
          },
          y: {
            grid: { display: false },
            ticks: { color: tickColor, font: { size: 11 } },
          },
        },
      },
    });

    const n = labels.length;
    const rowH = 28;
    const minH = 200;
    const h = Math.max(minH, 48 + n * rowH);
    const container = canvas.closest('.events-stats-chart__container');
    if (container) {
      container.style.height = `${h}px`;
    }
    chart.resize();
  }

  /** Balken 1–5 (Gesamtbewertung) */
  function barChartRating(canvasId, labels, values, xTitle) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !labels.length) return;

    const colors = labels.map((_, i) => barColors[i % barColors.length]);

    const chart = new Chart(canvas.getContext('2d'), {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: xTitle,
          data: values,
          backgroundColor: colors.map((c) => `${c}cc`),
          borderColor: colors,
          borderWidth: 1,
        }],
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label(ctx) {
                const v = ctx.parsed.x;
                return `${v} / 5`;
              },
            },
          },
        },
        scales: {
          x: {
            min: 0,
            max: 5,
            title: { display: true, text: xTitle, font: { size: 12, weight: '600' } },
            grid: { color: gridColor },
            ticks: {
              color: tickColor,
              stepSize: 1,
              callback(v) {
                return v;
              },
            },
          },
          y: {
            grid: { display: false },
            ticks: { color: tickColor, font: { size: 11 } },
          },
        },
      },
    });

    const n = labels.length;
    const rowH = 28;
    const minH = 200;
    const h = Math.max(minH, 48 + n * rowH);
    const container = canvas.closest('.events-stats-chart__container');
    if (container) {
      container.style.height = `${h}px`;
    }
    chart.resize();
  }

  function pieChart(canvasId, labels, values) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !labels.length) return;

    const colors = labels.map((_, i) => barColors[i % barColors.length]);

    new Chart(canvas.getContext('2d'), {
      type: 'pie',
      data: {
        labels,
        datasets: [{
          data: values,
          backgroundColor: colors.map((c) => `${c}cc`),
          borderColor: colors,
          borderWidth: 1,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: tickColor, boxWidth: 12, font: { size: 11 } },
          },
        },
      },
    });
  }

  const mp = payload.memberParticipation;
  if (mp && mp.labels && mp.values) {
    barChart('events-stats-chart-members', mp.labels, mp.values, 'Teilnahmequote (%)');
  }

  const oc = payload.organizerCost;
  if (oc && oc.labels && oc.values) {
    barChart('events-stats-chart-organizers', oc.labels, oc.values, 'Ø Anteil (CHF)');
  }

  const or = payload.organizerRatings;
  if (or && or.labels && or.values && or.labels.length) {
    barChartRating(
      'events-stats-chart-organizer-ratings',
      or.labels,
      or.values,
      'Ø Gesamtbewertung (1–5)',
    );
  }

  const k = payload.kitchens;
  if (k && k.labels && k.values && k.labels.length) {
    barChart('events-stats-chart-kitchens', k.labels, k.values, 'Anzahl Monatsessen');
  }

  /* —— Restaurant-Tabelle (sortierbar, Top 10) —— */
  const ratingsBlock = document.getElementById('events-stats-restaurant-ratings-block');
  const rr = payload.restaurantRatings;
  const tbody = document.getElementById('events-stats-restaurant-ratings-tbody');
  const wrap = document.getElementById('events-stats-restaurant-ratings-wrap');
  const emptyEl = document.getElementById('events-stats-restaurant-ratings-empty');
  const caption = document.getElementById('events-stats-restaurant-ratings-caption');
  const captionText = document.getElementById('events-stats-restaurant-ratings-caption-text');

  const SORT_LABELS = {
    restaurant: 'Restaurant',
    overall_avg: 'Gesamt',
    food_avg: 'Essen',
    drinks_avg: 'Getränke',
    service_avg: 'Service',
    count: 'n',
  };

  if (ratingsBlock && tbody && wrap && emptyEl) {
    if (!Array.isArray(rr) || rr.length === 0) {
      emptyEl.hidden = false;
      wrap.hidden = true;
      if (caption) caption.hidden = true;
    } else {
      emptyEl.hidden = true;
      wrap.hidden = false;
      if (caption && captionText) {
        caption.hidden = false;
        const n = rr.length;
        if (n <= TOP_RESTAURANTS) {
          captionText.innerHTML = `Es werden <strong>alle ${n}</strong> Restaurants mit Bewertungen angezeigt.`;
        } else {
          captionText.innerHTML = `Es werden die <strong>ersten ${TOP_RESTAURANTS}</strong> von <strong>${n}</strong> Restaurants angezeigt (nach gewählter Sortierung).`;
        }
      }

      let rows = rr.map((r) => ({ ...r }));
      let sortKey = 'overall_avg';
      let sortDir = 'desc';

      function cmp(a, b, key) {
        const va = a[key];
        const vb = b[key];
        if (key === 'restaurant') {
          return String(va).localeCompare(String(vb), 'de', { sensitivity: 'base' });
        }
        return va - vb;
      }

      function sortRows() {
        rows.sort((a, b) => {
          const c = cmp(a, b, sortKey);
          return sortDir === 'asc' ? c : -c;
        });
      }

      function fmtRating(v) {
        return (Math.round(v * 100) / 100).toFixed(2);
      }

      function escapeHtml(s) {
        const d = document.createElement('div');
        d.textContent = s;
        return d.innerHTML;
      }

      function renderTable() {
        sortRows();
        const slice = rows.slice(0, TOP_RESTAURANTS);
        tbody.replaceChildren();
        const frag = document.createDocumentFragment();
        slice.forEach((row) => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
        <td class="events-stats-restaurant-ratings-table__col-name">${escapeHtml(row.restaurant)}</td>
        <td class="events-stats-restaurant-ratings-table__col-score">${fmtRating(row.overall_avg)}</td>
        <td class="events-stats-restaurant-ratings-table__col-score">${fmtRating(row.food_avg)}</td>
        <td class="events-stats-restaurant-ratings-table__col-score">${fmtRating(row.drinks_avg)}</td>
        <td class="events-stats-restaurant-ratings-table__col-score">${fmtRating(row.service_avg)}</td>
        <td class="events-stats-restaurant-ratings-table__col-count">${row.count}</td>`;
          frag.appendChild(tr);
        });
        tbody.appendChild(frag);
      }

      function updateSortButtons() {
        ratingsBlock.querySelectorAll('.events-stats-sort-btn').forEach((btn) => {
          const key = btn.getAttribute('data-sort-key');
          const active = key === sortKey;
          btn.classList.toggle('events-stats-sort-btn--active', active);
          const base = SORT_LABELS[key] || key;
          const arrow = sortDir === 'asc' ? '↑' : '↓';
          btn.textContent = active ? `${base} ${arrow}` : base;
          btn.setAttribute('aria-sort', active ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none');
        });
      }

      ratingsBlock.querySelectorAll('.events-stats-sort-btn').forEach((btn) => {
        btn.addEventListener('click', () => {
          const key = btn.getAttribute('data-sort-key');
          if (!key) return;
          if (key === sortKey) {
            sortDir = sortDir === 'asc' ? 'desc' : 'asc';
          } else {
            sortKey = key;
            sortDir = key === 'restaurant' ? 'asc' : 'desc';
          }
          renderTable();
          updateSortButtons();
        });
      });

      sortRows();
      renderTable();
      updateSortButtons();
    }
  }
});

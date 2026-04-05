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
                return xTitle.includes('%') ? `${v} %` : `${v} CHF`;
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

  const k = payload.kitchens;
  if (k && k.labels && k.values && k.labels.length) {
    pieChart('events-stats-chart-kitchens', k.labels, k.values);
  }
});

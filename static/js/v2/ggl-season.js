document.addEventListener('DOMContentLoaded', () => {
  const dataScript = document.getElementById('ggl-progression-data');
  const chartCanvas = document.getElementById('ggl-progression-chart');
  const labelsContainer = document.getElementById('ggl-chart-labels');

  if (!dataScript || !chartCanvas || !labelsContainer || !window.Chart) return;

  let payload;
  try {
    payload = JSON.parse(dataScript.textContent.trim());
  } catch (e) {
    console.error('GGL progression data could not be parsed', e);
    return;
  }

  const { labels = [], members = [], data = {}, currentUserId } = payload;
  if (!labels.length || !members.length || !Object.keys(data).length) return;

  // Member colors - themed palette with enough variety
  const memberColors = [
    '#dc693c', '#73c8a8', '#45b7d1', '#96ceb4', '#8a9db1',
    '#f88958', '#2fa885', '#667a91', '#f59e0b', '#4f6477',
    '#ff9f43', '#10ac84', '#ee5a24', '#0984e3', '#bb8fce'
  ];

  // Sort members by last cumulative value desc
  const sortedMembers = members.slice().sort((a, b) => {
    const aData = data[a];
    const bData = data[b];
    const aTotal = aData?.cumulative_points?.[aData.cumulative_points.length - 1] || 0;
    const bTotal = bData?.cumulative_points?.[bData.cumulative_points.length - 1] || 0;
    return bTotal - aTotal;
  });

  const datasets = [];
  let currentUserDataset = null;
  let colorIndex = 0;

  sortedMembers.forEach((memberId) => {
    const memberData = data[memberId];
    if (!memberData || !memberData.member) return;

    const member = memberData.member;
    const isCurrentUser = Number(memberId) === Number(currentUserId);
    const color = memberColors[colorIndex % memberColors.length];
    colorIndex += 1;

    const dataset = {
      label: `${member.spirit_animal} ${member.display_name}`,
      data: memberData.cumulative_points,
      borderColor: color,
      backgroundColor: `${color}20`,
      borderWidth: isCurrentUser ? 3 : 2,
      pointRadius: isCurrentUser ? 8 : 6,
      pointHoverRadius: isCurrentUser ? 10 : 8,
      tension: 0.1,
      spanGaps: false,
      pointBackgroundColor: color,
      pointBorderColor: color,
      pointBorderWidth: 2,
      pointHoverBackgroundColor: color,
      pointHoverBorderColor: color,
    };

    if (isCurrentUser) currentUserDataset = dataset;
    else datasets.push(dataset);
  });

  if (currentUserDataset) datasets.push(currentUserDataset);

  Chart.register(ChartDataLabels);

  const eventCount = labels.length;
  const isMobile = window.innerWidth <= 768;
  const containerWidth = Math.max(isMobile ? 400 : 600, eventCount * (isMobile ? 100 : 150));

  const chart = new Chart(chartCanvas.getContext('2d'), {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      aspectRatio: isMobile && eventCount > 4 ? 0.8 : 1.2,
      interaction: { intersect: false, mode: 'index' },
      onHover(event, elements) {
        if (isMobile) {
          event?.native?.target && (event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default');
        }
      },
      onClick(event) {
        if (!isMobile) return;
        const active = chart.getElementsAtEventForMode(event, 'index', { intersect: false });
        if (!active.length) return;
        event.native?.preventDefault?.();
        const tooltip = chart.tooltip;
        const currentActive = tooltip.getActiveElements();
        if (currentActive.length > 0) {
          tooltip.setActiveElements([], { x: 0, y: 0 });
        } else {
          tooltip.setActiveElements(active, { x: event.x, y: event.y });
        }
        chart.update('none');
      },
      plugins: {
        legend: { display: false },
        layout: { padding: { left: 2, right: 2, top: 20, bottom: 20 } },
        tooltip: {
          enabled: true,
          external: isMobile ? () => false : undefined,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: '#fff',
          bodyColor: '#fff',
          borderColor: '#666',
          borderWidth: 1,
          cornerRadius: 6,
          displayColors: false,
          titleFont: { size: 14, weight: 'bold' },
          bodyFont: { size: 13 },
          padding: 12,
          itemSort: (a, b) => b.parsed.y - a.parsed.y,
          callbacks: {
            title: (ctx) => `Event: ${ctx[0].label}`,
            label: (ctx) => {
              const fullLabel = ctx.dataset.label;
              const cumulative = ctx.parsed.y;
              const idx = ctx.dataIndex;
              let eventPoints = cumulative;
              if (idx > 0) {
                const prev = ctx.dataset.data[idx - 1];
                if (prev !== null && prev !== undefined) eventPoints = cumulative - prev;
              }
              return `${fullLabel} - Punkte: ${cumulative} (+${eventPoints})`;
            },
          },
        },
        datalabels: { display: false },
      },
      scales: {
        x: {
          display: true,
          title: { display: true, text: 'Events', font: { size: 12, weight: 'bold' } },
          grid: { display: true, color: 'rgba(0, 0, 0, 0.1)' },
          ticks: { font: { size: 11 } },
          offset: true,
        },
        y: {
          display: true,
          title: { display: true, text: 'Kumulative Punkte', font: { size: 12, weight: 'bold' } },
          beginAtZero: true,
          grid: { display: true, color: 'rgba(0, 0, 0, 0.1)' },
          ticks: { font: { size: 11 } },
          offset: true,
        },
      },
      elements: {
        point: {
          hoverBackgroundColor: isMobile ? undefined : '#fff',
        },
      },
    },
  });

  createChartLabels(datasets);

  function createChartLabels(ds) {
    labelsContainer.innerHTML = '';
    const sorted = ds.slice().sort((a, b) => {
      const aLast = a.data[a.data.length - 1] || 0;
      const bLast = b.data[b.data.length - 1] || 0;
      return bLast - aLast;
    });
    sorted.forEach((dataset, idx) => {
      const item = document.createElement('div');
      item.className = 'ggl-chart__legend-item';

      const dot = document.createElement('div');
      dot.className = 'ggl-chart__legend-dot';
      dot.style.backgroundColor = dataset.borderColor;

      const rank = document.createElement('span');
      rank.className = 'ggl-chart__legend-rank';
      rank.textContent = `${idx + 1}.`;

      const label = document.createElement('span');
      label.className = 'ggl-chart__legend-label';
      label.textContent = dataset.label;

      item.append(dot, rank, label);
      labelsContainer.appendChild(item);
    });
  }

  setTimeout(() => {
    const scrollContainer = document.querySelector('.ggl-chart__scroll');
    const chartContainer = document.querySelector('.ggl-chart__container');
    if (!scrollContainer || !chartContainer) return;
    const totalWidth = containerWidth + 180;
    chartContainer.style.width = `${totalWidth}px`;
    chartContainer.style.minWidth = `${totalWidth}px`;
    scrollContainer.style.overflowX = 'auto';
    scrollContainer.style.overflowY = 'hidden';
    chart.resize();
  }, 60);
});


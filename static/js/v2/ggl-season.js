document.addEventListener('DOMContentLoaded', () => {
  const dataScript = document.getElementById('ggl-progression-data');
  if (!dataScript || !window.Chart) return;

  let payload;
  try {
    payload = JSON.parse(dataScript.textContent.trim());
  } catch (e) {
    console.error('GGL progression data could not be parsed', e);
    return;
  }

  const { labels = [], members = [], data = {}, currentUserId } = payload;
  if (!labels.length || !members.length || !Object.keys(data).length) return;
  const chartInstances = new Map();
  const rootTheme = document.documentElement.getAttribute('data-theme');
  const isDarkMode = rootTheme === 'dark';
  const gridColor = isDarkMode ? 'rgba(203, 213, 225, 0.34)' : 'rgba(0, 0, 0, 0.1)';
  const tickColor = isDarkMode ? '#cbd5e1' : '#0f172a';
  const tooltipBg = isDarkMode ? 'rgba(15, 23, 42, 0.96)' : 'rgba(15, 23, 42, 0.9)';
  const tooltipBorder = isDarkMode ? 'rgba(148, 163, 184, 0.55)' : 'rgba(100, 116, 139, 0.35)';

  const memberColors = [
    '#dc693c', '#73c8a8', '#45b7d1', '#96ceb4', '#8a9db1',
    '#f88958', '#2fa885', '#667a91', '#f59e0b', '#4f6477',
    '#ff9f43', '#10ac84', '#ee5a24', '#0984e3', '#bb8fce',
  ];

  const sortedMembers = members.slice().sort((a, b) => {
    const aData = data[a];
    const bData = data[b];
    const aTotal = aData?.cumulative_points?.[aData.cumulative_points.length - 1] || 0;
    const bTotal = bData?.cumulative_points?.[bData.cumulative_points.length - 1] || 0;
    return bTotal - aTotal;
  });

  const colorByMemberId = new Map();
  sortedMembers.forEach((memberId, idx) => {
    colorByMemberId.set(memberId, memberColors[idx % memberColors.length]);
  });

  Chart.register(ChartDataLabels);

  function formatChfFromRappen(rappen) {
    return `${(Math.abs(rappen) / 100).toFixed(2)} CHF`;
  }

  /**
   * @param {object} opts
   * @param {string} opts.canvasId
   * @param {string} opts.labelsContainerId
   * @param {'cumulative_points'|'avg_abs_diff_rappen'} opts.seriesKey
   * @param {string} opts.yAxisTitle
   * @param {'points'|'chf'} opts.unit
   * @param {'asc'|'desc'} [opts.rankOrder='desc']
   */
  function initProgressionChart(opts) {
    const chartCanvas = document.getElementById(opts.canvasId);
    const labelsContainer = document.getElementById(opts.labelsContainerId);
    if (!chartCanvas || !labelsContainer) return;

    const datasets = [];
    let currentUserDataset = null;
    let lockedTooltipIndex = null;

    const membersForChart = (() => {
      if (opts.seriesKey !== 'avg_abs_diff_rappen') return sortedMembers;

      return members.slice().sort((a, b) => {
        const aData = data[a];
        const bData = data[b];
        const aSeries = aData?.cumulative_abs_diff_rappen || [];
        const bSeries = bData?.cumulative_abs_diff_rappen || [];
        const aRanks = aData?.ranks || [];
        const bRanks = bData?.ranks || [];

        let aCount = 0;
        let bCount = 0;
        aSeries.forEach((_, idx) => {
          if (aRanks[idx] !== null && aRanks[idx] !== undefined) aCount += 1;
        });
        bSeries.forEach((_, idx) => {
          if (bRanks[idx] !== null && bRanks[idx] !== undefined) bCount += 1;
        });

        const aAvg = aCount > 0 ? aSeries[aSeries.length - 1] / aCount : Number.POSITIVE_INFINITY;
        const bAvg = bCount > 0 ? bSeries[bSeries.length - 1] / bCount : Number.POSITIVE_INFINITY;

        return aAvg - bAvg;
      });
    })();

    membersForChart.forEach((memberId) => {
      const memberData = data[memberId];
      if (!memberData || !memberData.member) return;

      const member = memberData.member;
      const isCurrentUser = Number(memberId) === Number(currentUserId);
      const color = colorByMemberId.get(memberId) || memberColors[0];
      const rawSeries = (() => {
        if (opts.seriesKey === 'avg_abs_diff_rappen') {
          const cumulativeAbs = memberData.cumulative_abs_diff_rappen || [];
          const ranks = memberData.ranks || [];
          let participationCount = 0;
          return cumulativeAbs.map((value, idx) => {
            if (ranks[idx] !== null && ranks[idx] !== undefined) participationCount += 1;
            if (!participationCount) return null;
            return Math.round(value / participationCount);
          });
        }
        return memberData[opts.seriesKey];
      })();
      if (!rawSeries || !rawSeries.length) return;

      const chartValues =
        opts.unit === 'chf'
          ? rawSeries.map((r) => (r == null ? null : r / 100))
          : rawSeries;

      const dataset = {
        label: `${member.spirit_animal} ${member.display_name}`,
        data: chartValues,
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
        _rawRappenSeries: opts.unit === 'chf' ? rawSeries : null,
      };

      if (isCurrentUser) currentUserDataset = dataset;
      else datasets.push(dataset);
    });

    if (currentUserDataset) datasets.push(currentUserDataset);

    const eventCount = labels.length;
    const isMobileLayout = window.innerWidth <= 768;
    const isTouchDevice = () => window.matchMedia('(pointer: coarse)').matches;
    const containerWidth = Math.max(isMobileLayout ? 400 : 600, eventCount * (isMobileLayout ? 100 : 150));

    const chart = new Chart(chartCanvas.getContext('2d'), {
      type: 'line',
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        aspectRatio: isMobileLayout && eventCount > 4 ? 0.8 : 1.2,
        interaction: { intersect: true, mode: 'nearest' },
        onHover(event, elements) {
          if (isTouchDevice()) {
            event?.native?.target && (event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default');
          }
        },
        onClick(event) {
          if (!isTouchDevice()) return;
          const tappedPoint = chart.getElementsAtEventForMode(
            event,
            'nearest',
            { intersect: true },
            true
          );
          if (!tappedPoint.length) return;
          event.native?.preventDefault?.();
          const tappedIndex = tappedPoint[0].index;
          const tappedDatasetIndex = tappedPoint[0].datasetIndex;
          const tappedValue = chart.data.datasets[tappedDatasetIndex]?.data?.[tappedIndex];
          if (tappedValue === null || tappedValue === undefined) return;

          const equalValueElements = chart.data.datasets
            .map((dataset, datasetIndex) => ({
              datasetIndex,
              index: tappedIndex,
              value: dataset?.data?.[tappedIndex],
            }))
            .filter((el) => {
              if (el.value === null || el.value === undefined) return false;
              return Math.abs(Number(el.value) - Number(tappedValue)) < 0.0001;
            })
            .map(({ datasetIndex, index }) => ({ datasetIndex, index }));

          const active = equalValueElements.length ? equalValueElements : [{ datasetIndex: tappedDatasetIndex, index: tappedIndex }];
          const tooltip = chart.tooltip;
          const key = `${tappedIndex}:${Number(tappedValue).toFixed(4)}`;
          const sameIndexTapped = lockedTooltipIndex === key;

          if (sameIndexTapped) {
            lockedTooltipIndex = null;
            tooltip.setActiveElements([], { x: 0, y: 0 });
          } else {
            lockedTooltipIndex = key;
            tooltip.setActiveElements(active, { x: event.x, y: event.y });
          }
          chart.update('none');
        },
        plugins: {
          legend: { display: false },
          layout: { padding: { left: 2, right: 2, top: 20, bottom: 20 } },
          tooltip: {
            enabled: true,
            mode: 'nearest',
            intersect: true,
            backgroundColor: tooltipBg,
            titleColor: '#fff',
            bodyColor: '#fff',
            borderColor: tooltipBorder,
            borderWidth: 1,
            cornerRadius: 6,
            displayColors: false,
            titleFont: { size: 14, weight: 'bold' },
            bodyFont: { size: 13 },
            padding: 12,
            itemSort: (a, b) =>
              opts.rankOrder === 'asc'
                ? a.parsed.y - b.parsed.y
                : b.parsed.y - a.parsed.y,
            callbacks: {
              title: (ctx) => `Event: ${ctx[0].label}`,
              label: (ctx) => {
                const fullLabel = ctx.dataset.label;
                const idx = ctx.dataIndex;
                if (opts.unit === 'points') {
                  const cumulative = ctx.parsed.y;
                  let eventPoints = cumulative;
                  if (idx > 0) {
                    const prev = ctx.dataset.data[idx - 1];
                    if (prev !== null && prev !== undefined) eventPoints = cumulative - prev;
                  }
                  return `${fullLabel} - Punkte: ${cumulative} (+${eventPoints})`;
                }
                const currentRappen = Math.round((ctx.parsed.y || 0) * 100);
                return `${fullLabel} - ØDiff: ${formatChfFromRappen(currentRappen)}`;
              },
            },
          },
          datalabels: { display: false },
        },
        scales: {
          x: {
            display: true,
            title: { display: true, text: 'Events', font: { size: 12, weight: 'bold' } },
            grid: { display: true, color: gridColor },
            ticks: { color: tickColor, font: { size: 11 } },
            offset: true,
          },
          y: {
            display: true,
            title: { display: true, text: opts.yAxisTitle, font: { size: 12, weight: 'bold' } },
            beginAtZero: opts.unit === 'points',
            reverse: opts.rankOrder === 'asc',
            grid: { display: true, color: gridColor },
            ticks: { color: tickColor, font: { size: 11 } },
            offset: true,
          },
        },
        elements: {
          point: {
            hoverBackgroundColor: isTouchDevice() ? undefined : '#fff',
            hitRadius: 16,
          },
        },
      },
    });

    createChartLabels(labelsContainer, datasets, opts.rankOrder || 'desc');

    setTimeout(() => {
      const scrollContainer = chartCanvas.closest('.ggl-chart__scroll');
      const chartContainer = chartCanvas.closest('.ggl-chart__container');
      if (!scrollContainer || !chartContainer) return;
      const totalWidth = containerWidth + 180;
      chartContainer.style.width = `${totalWidth}px`;
      chartContainer.style.minWidth = `${totalWidth}px`;
      scrollContainer.style.overflowX = 'auto';
      scrollContainer.style.overflowY = 'hidden';
      chart.resize();
    }, 60);
    return chart;
  }

  function createChartLabels(labelsContainer, ds, rankOrder) {
    labelsContainer.innerHTML = '';
    const sorted = ds.slice().sort((a, b) => {
      const aLast = a.data[a.data.length - 1] || 0;
      const bLast = b.data[b.data.length - 1] || 0;
      return rankOrder === 'asc' ? aLast - bLast : bLast - aLast;
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

  const progressionChart = initProgressionChart({
    canvasId: 'ggl-progression-chart',
    labelsContainerId: 'ggl-chart-labels',
    seriesKey: 'cumulative_points',
    yAxisTitle: 'Kumulative Punkte',
    unit: 'points',
    rankOrder: 'desc',
  });
  if (progressionChart) chartInstances.set('ggl-progression-chart', progressionChart);

  const diffChart = initProgressionChart({
    canvasId: 'ggl-diff-chart',
    labelsContainerId: 'ggl-diff-chart-labels',
    seriesKey: 'avg_abs_diff_rappen',
    yAxisTitle: 'Ø absolute Differenz (CHF)',
    unit: 'chf',
    rankOrder: 'asc',
  });
  if (diffChart) chartInstances.set('ggl-diff-chart', diffChart);

  const modal = document.getElementById('ggl-chart-fullscreen-modal');
  const modalBody = modal ? modal.querySelector('[data-ggl-modal-body]') : null;
  const expandButtons = Array.from(document.querySelectorAll('.ggl-chart-expand-btn'));
  let activeChartNode = null;
  let activePlaceholder = null;
  let activeChartInstance = null;
  let previousBodyOverflow = '';

  function closeFullscreenModal() {
    if (!modal || !modalBody) return;
    if (activeChartNode && activePlaceholder && activePlaceholder.parentNode) {
      activePlaceholder.parentNode.insertBefore(activeChartNode, activePlaceholder);
      activePlaceholder.remove();
      activeChartNode.classList.remove('ggl-chart--fullscreen');
    }
    modal.setAttribute('data-open', 'false');
    modal.hidden = true;
    document.body.style.overflow = previousBodyOverflow;

    if (activeChartInstance) {
      setTimeout(() => activeChartInstance.resize(), 60);
    }

    activeChartNode = null;
    activePlaceholder = null;
    activeChartInstance = null;
  }

  function openFullscreenModal(button) {
    if (!modal || !modalBody) return;
    const chartTarget = button.getAttribute('data-chart-target');
    const chartCanvasId = button.getAttribute('data-chart-canvas-id');
    const chartNode = chartTarget ? document.getElementById(chartTarget) : null;
    if (!chartNode || !chartNode.parentNode) return;

    if (activeChartNode) {
      closeFullscreenModal();
    }

    activePlaceholder = document.createElement('div');
    activePlaceholder.className = 'ggl-chart-placeholder';
    chartNode.parentNode.insertBefore(activePlaceholder, chartNode);
    modalBody.appendChild(chartNode);
    chartNode.classList.add('ggl-chart--fullscreen');

    activeChartNode = chartNode;
    activeChartInstance = chartCanvasId ? chartInstances.get(chartCanvasId) || null : null;
    previousBodyOverflow = document.body.style.overflow || '';

    modal.hidden = false;
    modal.setAttribute('data-open', 'true');
    if (activeChartInstance) {
      setTimeout(() => activeChartInstance.resize(), 60);
    }
  }

  expandButtons.forEach((button) => {
    button.addEventListener('click', () => openFullscreenModal(button));
  });

  if (modal) {
    modal.querySelectorAll('[data-ggl-chart-modal-close]').forEach((el) => {
      el.addEventListener('click', closeFullscreenModal);
    });
  }

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && modal && modal.getAttribute('data-open') === 'true') {
      closeFullscreenModal();
    }
  });
});

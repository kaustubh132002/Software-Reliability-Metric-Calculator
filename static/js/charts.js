/**
 * Chart.js Visualizations for SEQA Software Reliability Metric Calculator.
 * Renders MTBF Trend, MTTR Trend, Availability Chart, and Failure Rate Graph.
 */

let mtbfChartInstance = null;
let mttrChartInstance = null;
let availabilityChartInstance = null;
let failureRateChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
  if (typeof initialChartsData !== 'undefined' && initialChartsData) {
    initCharts(initialChartsData);
  }
});

function getThemeColors() {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  return {
    textColor: isDark ? '#cbd5e1' : '#475569',
    gridColor: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)',
    cardBg: isDark ? '#111a2e' : '#ffffff',
    primary: '#3b82f6',
    primaryAlpha: 'rgba(59, 130, 246, 0.25)',
    accent: '#06b6d4',
    accentAlpha: 'rgba(6, 182, 212, 0.25)',
    warning: '#f59e0b',
    warningAlpha: 'rgba(245, 158, 11, 0.25)',
    danger: '#ef4444',
    dangerAlpha: 'rgba(239, 68, 68, 0.25)',
    success: '#10b981',
    successAlpha: 'rgba(16, 185, 129, 0.25)'
  };
}

function initCharts(data) {
  if (!data || !data.labels || data.labels.length === 0) return;

  const colors = getThemeColors();
  const labels = data.labels;

  // 1. MTBF Trend Chart (Line)
  const ctxMtbf = document.getElementById('mtbfTrendChart')?.getContext('2d');
  if (ctxMtbf) {
    if (mtbfChartInstance) mtbfChartInstance.destroy();
    mtbfChartInstance = new Chart(ctxMtbf, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'MTBF (Hours)',
          data: data.mtbf,
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37, 99, 235, 0.15)',
          borderWidth: 3,
          tension: 0.35,
          fill: true,
          pointBackgroundColor: '#2563eb',
          pointBorderColor: '#ffffff',
          pointRadius: 5,
          pointHoverRadius: 7
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: colors.textColor, font: { weight: 'bold' } } },
          tooltip: {
            callbacks: {
              label: (ctx) => `MTBF: ${ctx.parsed.y.toLocaleString()} hours`
            }
          }
        },
        scales: {
          x: {
            grid: { color: colors.gridColor },
            ticks: { color: colors.textColor, maxRotation: 45, minRotation: 0 }
          },
          y: {
            grid: { color: colors.gridColor },
            ticks: { color: colors.textColor },
            title: { display: true, text: 'Hours', color: colors.textColor }
          }
        }
      }
    });
  }

  // 2. MTTR Trend Chart (Bar)
  const ctxMttr = document.getElementById('mttrTrendChart')?.getContext('2d');
  if (ctxMttr) {
    if (mttrChartInstance) mttrChartInstance.destroy();
    mttrChartInstance = new Chart(ctxMttr, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'MTTR (Hours)',
          data: data.mttr,
          backgroundColor: '#f59e0b',
          borderColor: '#d97706',
          borderWidth: 1.5,
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: colors.textColor, font: { weight: 'bold' } } },
          tooltip: {
            callbacks: {
              label: (ctx) => `MTTR: ${ctx.parsed.y} hours`
            }
          }
        },
        scales: {
          x: {
            grid: { color: colors.gridColor },
            ticks: { color: colors.textColor }
          },
          y: {
            grid: { color: colors.gridColor },
            ticks: { color: colors.textColor },
            title: { display: true, text: 'Repair Hours', color: colors.textColor }
          }
        }
      }
    });
  }

  // 3. System Availability Chart (Bar + Benchmark line)
  const ctxAvail = document.getElementById('availabilityChart')?.getContext('2d');
  if (ctxAvail) {
    if (availabilityChartInstance) availabilityChartInstance.destroy();
    availabilityChartInstance = new Chart(ctxAvail, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Availability (%)',
          data: data.availability,
          backgroundColor: data.availability.map(val => val >= 99.0 ? 'rgba(16, 185, 129, 0.85)' : 'rgba(239, 68, 68, 0.85)'),
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: colors.textColor, font: { weight: 'bold' } } },
          tooltip: {
            callbacks: {
              label: (ctx) => `Availability: ${ctx.parsed.y}%`
            }
          }
        },
        scales: {
          x: {
            grid: { color: colors.gridColor },
            ticks: { color: colors.textColor }
          },
          y: {
            min: Math.max(0, Math.min(...data.availability) - 5),
            max: 100,
            grid: { color: colors.gridColor },
            ticks: { color: colors.textColor },
            title: { display: true, text: 'Availability %', color: colors.textColor }
          }
        }
      }
    });
  }

  // 4. Failure Rate Graph (λ)
  const ctxFr = document.getElementById('failureRateChart')?.getContext('2d');
  if (ctxFr) {
    if (failureRateChartInstance) failureRateChartInstance.destroy();
    failureRateChartInstance = new Chart(ctxFr, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Failure Rate (λ / hr)',
          data: data.failure_rate,
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239, 68, 68, 0.2)',
          fill: true,
          tension: 0.3,
          borderWidth: 2,
          pointRadius: 4,
          pointBackgroundColor: '#ef4444'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: colors.textColor, font: { weight: 'bold' } } },
          tooltip: {
            callbacks: {
              label: (ctx) => `λ: ${ctx.parsed.y} failures/hr`
            }
          }
        },
        scales: {
          x: {
            grid: { color: colors.gridColor },
            ticks: { color: colors.textColor }
          },
          y: {
            grid: { color: colors.gridColor },
            ticks: { color: colors.textColor },
            title: { display: true, text: 'Failures per Hour', color: colors.textColor }
          }
        }
      }
    });
  }
}

window.updateChartsTheme = function(theme) {
  if (typeof initialChartsData !== 'undefined' && initialChartsData) {
    initCharts(initialChartsData);
  }
};

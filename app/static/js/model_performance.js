/**
 * Model Performance JavaScript for HomeValue AI
 * Visualizes Actual vs. Predicted scatter, residual histogram, and feature importance.
 */
document.addEventListener('DOMContentLoaded', () => {
  let charts = {};
  let cachedMetrics = null;

  function loadMetrics() {
    fetch('/api/model-metrics')
      .then(res => res.json())
      .then(data => {
        cachedMetrics = data;
        renderPerformanceCharts(data);
      })
      .catch(err => {
        console.error('Error fetching model metrics:', err);
      });
  }

  function renderPerformanceCharts(data) {
    const resSummary = data.residual_summary || {};
    const scatterSample = resSummary.scatter_sample || [];
    const histBins = resSummary.histogram || [];
    const featImp = data.feature_importance || [];

    // 1. Actual vs Predicted Chart
    const ctxAvsP = document.getElementById('actualVsPredChart')?.getContext('2d');
    if (ctxAvsP && scatterSample.length > 0) {
      if (charts.avsp) charts.avsp.destroy();

      // Find min and max for the 45-degree reference line
      const allVals = scatterSample.flatMap(p => [p.actual, p.predicted]);
      const minVal = Math.min(...allVals);
      const maxVal = Math.max(...allVals);

      charts.avsp = new Chart(ctxAvsP, {
        type: 'scatter',
        data: {
          datasets: [
            {
              label: 'Test Observations',
              data: scatterSample.map(p => ({ x: p.actual, y: p.predicted })),
              backgroundColor: 'rgba(79, 70, 229, 0.65)',
              borderColor: '#4F46E5',
              pointRadius: 4,
              pointHoverRadius: 6
            },
            {
              type: 'line',
              label: 'Ideal 45° Fit Line',
              data: [
                { x: minVal, y: minVal },
                { x: maxVal, y: maxVal }
              ],
              borderColor: '#EF4444',
              borderWidth: 2,
              borderDash: [5, 5],
              pointRadius: 0,
              fill: false
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'top' },
            tooltip: {
              callbacks: {
                label: (ctx) => {
                  if (ctx.datasetIndex === 1) return ' Perfect fit line';
                  return ` Actual: ${window.HomeValueApp.formatCurrency(ctx.raw.x)} | Predicted: ${window.HomeValueApp.formatCurrency(ctx.raw.y)}`;
                }
              }
            }
          },
          scales: {
            x: {
              title: { display: true, text: 'Actual Sale Price ($)', font: { size: 11 } },
              ticks: { callback: (val) => window.HomeValueApp.formatCurrency(val) },
              grid: { color: '#F3F4F6' }
            },
            y: {
              title: { display: true, text: 'Predicted Sale Price ($)', font: { size: 11 } },
              ticks: { callback: (val) => window.HomeValueApp.formatCurrency(val) },
              grid: { color: '#F3F4F6' }
            }
          }
        }
      });
    }

    // 2. Residual Distribution Histogram
    const ctxRes = document.getElementById('residualChart')?.getContext('2d');
    if (ctxRes && histBins.length > 0) {
      if (charts.res) charts.res.destroy();

      charts.res = new Chart(ctxRes, {
        type: 'bar',
        data: {
          labels: histBins.map(b => b.bin_label),
          datasets: [{
            label: 'Error Frequency',
            data: histBins.map(b => b.count),
            backgroundColor: 'rgba(239, 68, 68, 0.75)',
            borderColor: '#EF4444',
            borderWidth: 1,
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: (ctx) => ` ${ctx.raw} observations in this error band` } }
          },
          scales: {
            y: { beginAtZero: true, grid: { color: '#F3F4F6' } },
            x: { grid: { display: false }, ticks: { maxRotation: 45, minRotation: 45, font: { size: 10 } } }
          }
        }
      });
    }

    // 3. Feature Importance Horizontal Bar Chart
    const ctxFeat = document.getElementById('featureImportanceChart')?.getContext('2d');
    if (ctxFeat && featImp.length > 0) {
      if (charts.feat) charts.feat.destroy();

      const subtitleEl = document.getElementById('featureImportanceSubtitle');
      if (subtitleEl && featImp[0]?.technique) {
        subtitleEl.textContent = `${featImp[0].technique} extracted from ${data.active_model_name}`;
      }

      charts.feat = new Chart(ctxFeat, {
        type: 'bar',
        data: {
          labels: featImp.map(f => f.feature),
          datasets: [{
            label: 'Normalized Importance Weight (%)',
            data: featImp.map(f => f.importance),
            backgroundColor: featImp.map((_, i) => i < 3 ? 'rgba(20, 184, 166, 0.9)' : 'rgba(79, 70, 229, 0.75)'),
            borderRadius: 4
          }]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: (ctx) => ` ${ctx.raw}% relative predictive power` } }
          },
          scales: {
            x: { title: { display: true, text: 'Importance Weight (%)' }, beginAtZero: true, grid: { color: '#F3F4F6' } },
            y: { grid: { display: false } }
          }
        }
      });
    }
  }

  loadMetrics();
});

/**
 * Market Analytics JavaScript for HomeValue AI
 * Orchestrates dynamic market analytics, filtering, and 6 Chart.js canvases.
 */
document.addEventListener('DOMContentLoaded', () => {
  let charts = {};
  let cachedAnalytics = null;

  function loadAnalytics() {
    const zipcode = document.getElementById('analyticsZipcode')?.value || 'all';
    const minBeds = document.getElementById('analyticsMinBeds')?.value || '';
    const maxBeds = document.getElementById('analyticsMaxBeds')?.value || '';
    const minPrice = document.getElementById('analyticsMinPrice')?.value || '';
    const maxPrice = document.getElementById('analyticsMaxPrice')?.value || '';

    let url = `/api/analytics?zipcode=${encodeURIComponent(zipcode)}`;
    if (minBeds) url += `&min_bedrooms=${encodeURIComponent(minBeds)}`;
    if (maxBeds) url += `&max_bedrooms=${encodeURIComponent(maxBeds)}`;
    if (minPrice) url += `&min_price=${encodeURIComponent(minPrice)}`;
    if (maxPrice) url += `&max_price=${encodeURIComponent(maxPrice)}`;

    fetch(url)
      .then(res => res.json())
      .then(data => {
        cachedAnalytics = data;
        renderKPIs(data);
        renderCharts(data);
      })
      .catch(err => {
        console.error('Analytics load error:', err);
        window.HomeValueApp?.showToast('Failed to load market analytics', 'danger');
      });
  }

  function renderKPIs(data) {
    const totalEl = document.getElementById('analyticTotalProperties');
    const avgEl = document.getElementById('analyticAvgPrice');
    const medianEl = document.getElementById('analyticMedianPrice');
    const sqftEl = document.getElementById('analyticAvgSqft');
    const priceSqftEl = document.getElementById('analyticAvgPriceSqft');

    if (totalEl) totalEl.textContent = Number(data.total_properties).toLocaleString();
    if (avgEl) avgEl.textContent = window.HomeValueApp.formatCurrency(data.summary.avg_price);
    if (medianEl) medianEl.textContent = `Median: ${window.HomeValueApp.formatCurrency(data.summary.median_price)}`;
    if (sqftEl) sqftEl.textContent = `${Number(data.summary.avg_sqft).toLocaleString()} sq ft`;
    if (priceSqftEl) priceSqftEl.textContent = `${window.HomeValueApp.formatCurrency(data.summary.avg_price_per_sqft)} / sq ft`;
  }

  function renderCharts(data) {
    // 1. Price Distribution Histogram
    const ctxDist = document.getElementById('marketPriceDistChart')?.getContext('2d');
    if (ctxDist) {
      if (charts.dist) charts.dist.destroy();
      charts.dist = new Chart(ctxDist, {
        type: 'bar',
        data: {
          labels: data.price_histogram.map(b => b.label),
          datasets: [{
            label: 'Sales Volume',
            data: data.price_histogram.map(b => b.count),
            backgroundColor: 'rgba(79, 70, 229, 0.75)',
            borderColor: '#4F46E5',
            borderWidth: 1,
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: (ctx) => ` ${ctx.raw} recorded sales` } }
          },
          scales: {
            y: { beginAtZero: true, grid: { color: '#F3F4F6' } },
            x: { grid: { display: false }, ticks: { maxRotation: 45, minRotation: 45, font: { size: 10 } } }
          }
        }
      });
    }

    // 2. Scatter Plot: Price vs Area
    const ctxScatter = document.getElementById('marketScatterChart')?.getContext('2d');
    if (ctxScatter) {
      if (charts.scatter) charts.scatter.destroy();
      charts.scatter = new Chart(ctxScatter, {
        type: 'scatter',
        data: {
          datasets: [{
            label: 'Sales Records',
            data: data.scatter_sample.map(p => ({ x: p.sqft_living, y: p.price, beds: p.bedrooms })),
            backgroundColor: 'rgba(14, 165, 233, 0.6)',
            borderColor: '#0284C7',
            pointRadius: 4,
            pointHoverRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (ctx) => ` ${ctx.raw.x.toLocaleString()} sq ft • ${ctx.raw.beds}bd: ${window.HomeValueApp.formatCurrency(ctx.raw.y)}`
              }
            }
          },
          scales: {
            x: { title: { display: true, text: 'Interior Living Area (sq ft)', font: { size: 11 } }, grid: { color: '#F3F4F6' } },
            y: { ticks: { callback: (val) => window.HomeValueApp.formatCurrency(val) }, grid: { color: '#F3F4F6' } }
          }
        }
      });
    }

    // 3. Price by Bedrooms
    const ctxBeds = document.getElementById('marketBedroomsChart')?.getContext('2d');
    if (ctxBeds) {
      if (charts.beds) charts.beds.destroy();
      charts.beds = new Chart(ctxBeds, {
        type: 'bar',
        data: {
          labels: data.bedrooms_data.map(b => `${b.bedrooms} Bedrooms`),
          datasets: [{
            label: 'Average Price',
            data: data.bedrooms_data.map(b => b.avg_price),
            backgroundColor: 'rgba(16, 185, 129, 0.75)',
            borderColor: '#10B981',
            borderWidth: 1,
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: (ctx) => ` Avg: ${window.HomeValueApp.formatCurrency(ctx.raw)}` } }
          },
          scales: {
            y: { ticks: { callback: (val) => window.HomeValueApp.formatCurrency(val) }, grid: { color: '#F3F4F6' } },
            x: { grid: { display: false } }
          }
        }
      });
    }

    // 4. Price by Bathrooms
    const ctxBaths = document.getElementById('marketBathroomsChart')?.getContext('2d');
    if (ctxBaths) {
      if (charts.baths) charts.baths.destroy();
      charts.baths = new Chart(ctxBaths, {
        type: 'bar',
        data: {
          labels: data.bathrooms_data.map(b => `${b.bathrooms} Baths`),
          datasets: [{
            label: 'Average Price',
            data: data.bathrooms_data.map(b => b.avg_price),
            backgroundColor: 'rgba(20, 184, 166, 0.75)',
            borderColor: '#14B8A6',
            borderWidth: 1,
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: (ctx) => ` Avg: ${window.HomeValueApp.formatCurrency(ctx.raw)}` } }
          },
          scales: {
            y: { ticks: { callback: (val) => window.HomeValueApp.formatCurrency(val) }, grid: { color: '#F3F4F6' } },
            x: { grid: { display: false } }
          }
        }
      });
    }

    // 5. Top Zipcodes Comparison
    const ctxZip = document.getElementById('marketZipcodesChart')?.getContext('2d');
    if (ctxZip) {
      if (charts.zip) charts.zip.destroy();
      charts.zip = new Chart(ctxZip, {
        type: 'bar',
        data: {
          labels: data.zipcode_data.map(z => z.zipcode),
          datasets: [{
            label: 'Avg Sale Price',
            data: data.zipcode_data.map(z => z.avg_price),
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
            tooltip: { callbacks: { label: (ctx) => ` Avg: ${window.HomeValueApp.formatCurrency(ctx.raw)}` } }
          },
          scales: {
            y: { ticks: { callback: (val) => window.HomeValueApp.formatCurrency(val) }, grid: { color: '#F3F4F6' } },
            x: { grid: { display: false } }
          }
        }
      });
    }

    // 6. Feature Correlation Horizontal Bar Chart
    const ctxCorr = document.getElementById('marketCorrelationChart')?.getContext('2d');
    if (ctxCorr) {
      if (charts.corr) charts.corr.destroy();
      charts.corr = new Chart(ctxCorr, {
        type: 'bar',
        data: {
          labels: data.correlation_data.map(c => c.label),
          datasets: [{
            label: 'Correlation with Price (r)',
            data: data.correlation_data.map(c => c.correlation),
            backgroundColor: data.correlation_data.map(c => c.correlation >= 0.5 ? 'rgba(79, 70, 229, 0.85)' : 'rgba(165, 180, 252, 0.85)'),
            borderRadius: 4
          }]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: (ctx) => ` Pearson r = ${ctx.raw}` } }
          },
          scales: {
            x: { min: -0.2, max: 1.0, grid: { color: '#F3F4F6' } },
            y: { grid: { display: false } }
          }
        }
      });
    }
  }

  // Filter handlers
  document.getElementById('applyAnalyticsFilterBtn')?.addEventListener('click', loadAnalytics);
  document.getElementById('resetAnalyticsFilterBtn')?.addEventListener('click', () => {
    document.getElementById('analyticsZipcode').value = 'all';
    document.getElementById('analyticsMinBeds').value = '';
    document.getElementById('analyticsMaxBeds').value = '';
    document.getElementById('analyticsMinPrice').value = '';
    document.getElementById('analyticsMaxPrice').value = '';
    loadAnalytics();
  });

  window.addEventListener('currencyChanged', () => {
    if (cachedAnalytics) {
      renderKPIs(cachedAnalytics);
      renderCharts(cachedAnalytics);
    }
  });

  loadAnalytics();
});

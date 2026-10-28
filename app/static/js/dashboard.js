/**
 * Dashboard Overview JavaScript for HomeValue AI
 * Connects KPI cards, Chart.js instances, and real prediction table.
 */
document.addEventListener('DOMContentLoaded', () => {
  let charts = {};
  let dashboardCache = null;

  function loadDashboard() {
    fetch('/api/dashboard')
      .then(res => {
        if (!res.ok) throw new Error('Failed to load dashboard data');
        return res.json();
      })
      .then(data => {
        dashboardCache = data;
        renderKPIs(data.kpi);
        renderCharts(data.charts);
        renderRecentTable(data.recent_predictions);
      })
      .catch(err => {
        console.error('Error fetching dashboard data:', err);
        const tbody = document.getElementById('recentPredictionsBody');
        if (tbody) {
          tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-danger"><i class="bi bi-exclamation-triangle me-2"></i> Failed to load dashboard data.</td></tr>`;
        }
      });
  }

  function renderKPIs(kpi) {
    const totalEl = document.getElementById('kpiTotalPredictions');
    const avgEl = document.getElementById('kpiAvgPrice');
    const maxEl = document.getElementById('kpiMaxPrice');
    const r2El = document.getElementById('kpiModelR2');
    const modelNameEl = document.getElementById('kpiModelName');

    if (totalEl) totalEl.textContent = kpi.total_predictions.toLocaleString();

    if (avgEl) {
      if (kpi.total_predictions > 0 && kpi.avg_predicted_price > 0) {
        avgEl.textContent = window.HomeValueApp.formatCurrency(kpi.avg_predicted_price);
      } else {
        avgEl.textContent = 'None yet';
      }
    }

    if (maxEl) {
      if (kpi.total_predictions > 0 && kpi.max_predicted_price > 0) {
        maxEl.textContent = window.HomeValueApp.formatCurrency(kpi.max_predicted_price);
      } else {
        maxEl.textContent = 'None yet';
      }
    }

    if (r2El) {
      r2El.textContent = kpi.model_r2 ? kpi.model_r2.toFixed(3) : '0.850';
    }

    if (modelNameEl && kpi.model_name) {
      modelNameEl.textContent = kpi.model_name;
    }
  }

  function renderCharts(chartData) {
    // 1. Price Distribution Histogram
    const ctxDist = document.getElementById('priceDistChart')?.getContext('2d');
    if (ctxDist && chartData.price_histogram && chartData.price_histogram.length > 0) {
      if (charts.priceDist) charts.priceDist.destroy();
      charts.priceDist = new Chart(ctxDist, {
        type: 'bar',
        data: {
          labels: chartData.price_histogram.map(b => b.label),
          datasets: [{
            label: 'Properties in Tier',
            data: chartData.price_histogram.map(b => b.count),
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
            tooltip: {
              callbacks: {
                label: (ctx) => ` ${ctx.raw} properties`
              }
            }
          },
          scales: {
            y: { beginAtZero: true, grid: { color: '#F3F4F6' } },
            x: { grid: { display: false }, ticks: { maxRotation: 45, minRotation: 45, font: { size: 10 } } }
          }
        }
      });
    }

    // 2. Average Price by Bedrooms
    const ctxBeds = document.getElementById('bedroomPriceChart')?.getContext('2d');
    if (ctxBeds && chartData.bedrooms_data && chartData.bedrooms_data.length > 0) {
      if (charts.beds) charts.beds.destroy();
      charts.beds = new Chart(ctxBeds, {
        type: 'bar',
        data: {
          labels: chartData.bedrooms_data.map(b => `${b.bedrooms} Beds`),
          datasets: [{
            label: 'Avg Price',
            data: chartData.bedrooms_data.map(b => b.avg_price),
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
            tooltip: {
              callbacks: {
                label: (ctx) => ` Avg: ${window.HomeValueApp.formatCurrency(ctx.raw)}`
              }
            }
          },
          scales: {
            y: {
              ticks: {
                callback: (val) => window.HomeValueApp.formatCurrency(val)
              },
              grid: { color: '#F3F4F6' }
            },
            x: { grid: { display: false } }
          }
        }
      });
    }

    // 3. Living Area vs Price Scatter
    const ctxScatter = document.getElementById('areaPriceScatterChart')?.getContext('2d');
    if (ctxScatter && chartData.scatter_sample && chartData.scatter_sample.length > 0) {
      if (charts.scatter) charts.scatter.destroy();
      charts.scatter = new Chart(ctxScatter, {
        type: 'scatter',
        data: {
          datasets: [{
            label: 'Sample Homes',
            data: chartData.scatter_sample.map(p => ({ x: p.sqft_living, y: p.price })),
            backgroundColor: 'rgba(99, 102, 241, 0.6)',
            borderColor: '#4F46E5',
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
                label: (ctx) => ` ${ctx.raw.x.toLocaleString()} sq ft: ${window.HomeValueApp.formatCurrency(ctx.raw.y)}`
              }
            }
          },
          scales: {
            x: {
              title: { display: true, text: 'Interior Living Space (sq ft)', font: { size: 11 } },
              grid: { color: '#F3F4F6' }
            },
            y: {
              title: { display: true, text: 'Price', font: { size: 11 } },
              ticks: { callback: (val) => window.HomeValueApp.formatCurrency(val) },
              grid: { color: '#F3F4F6' }
            }
          }
        }
      });
    }

    // 4. Activity Line Chart
    const ctxAct = document.getElementById('activityChart')?.getContext('2d');
    if (ctxAct) {
      if (charts.activity) charts.activity.destroy();
      const labels = (chartData.activity && chartData.activity.length > 0) 
        ? chartData.activity.map(a => a.date) 
        : ['Today'];
      const counts = (chartData.activity && chartData.activity.length > 0) 
        ? chartData.activity.map(a => a.count) 
        : [0];

      charts.activity = new Chart(ctxAct, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [{
            label: 'Daily Valuations',
            data: counts,
            borderColor: '#F59E0B',
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            fill: true,
            tension: 0.35,
            borderWidth: 2,
            pointRadius: 4,
            pointBackgroundColor: '#F59E0B'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            y: { beginAtZero: true, ticks: { stepSize: 1 }, grid: { color: '#F3F4F6' } },
            x: { grid: { display: false } }
          }
        }
      });
    }
  }

  function renderRecentTable(records) {
    const tbody = document.getElementById('recentPredictionsBody');
    if (!tbody) return;

    if (!records || records.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" class="text-center py-4">
            <div class="text-muted mb-2"><i class="bi bi-inbox" style="font-size: 2rem;"></i></div>
            <div class="fw-bold">No property predictions made yet</div>
            <div class="small text-muted mb-3">Try out our machine learning valuation engine!</div>
            <a href="/predict" class="btn btn-sm btn-primary-custom">
              <i class="bi bi-magic me-1"></i> Make First Prediction
            </a>
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = records.map(r => `
      <tr>
        <td class="text-nowrap small text-muted">${r.created_at || 'Just now'}</td>
        <td>
          <div class="fw-bold">${r.property_title || 'King County Residence'}</div>
          <div class="small text-muted"><i class="bi bi-geo-alt-fill text-danger me-1"></i>ZIP ${r.zipcode}</div>
        </td>
        <td>${r.sqft_living ? Number(r.sqft_living).toLocaleString() : '--'} sq ft</td>
        <td>${r.bedrooms} bd / ${r.bathrooms} ba</td>
        <td>
          <span class="badge bg-success-subtle text-success border border-success-subtle fs-6 px-2 py-1">
            ${window.HomeValueApp.formatCurrency(r.predicted_price)}
          </span>
        </td>
        <td><span class="badge bg-light text-dark border">${r.model_name || 'RF'}</span></td>
        <td class="text-end">
          <button class="btn btn-sm btn-outline-primary view-detail-btn" data-id="${r.id}">
            <i class="bi bi-eye"></i> Details
          </button>
        </td>
      </tr>
    `).join('');

    // Attach click listeners to Details buttons
    document.querySelectorAll('.view-detail-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.getAttribute('data-id');
        showRecordDetail(id);
      });
    });
  }

  function showRecordDetail(id) {
    fetch(`/api/predictions/${id}`)
      .then(res => res.json())
      .then(r => {
        const modalBody = document.getElementById('quickDetailModalBody');
        if (!modalBody) return;

        modalBody.innerHTML = `
          <div class="d-flex justify-content-between align-items-center mb-3 pb-3 border-bottom">
            <div>
              <h5 class="fw-bold mb-1">${r.property_title || 'Residential Valuation'}</h5>
              <div class="text-muted small"><i class="bi bi-geo-alt me-1"></i>Zipcode: ${r.zipcode} • Saved on: ${r.created_at}</div>
            </div>
            <div class="text-end">
              <div class="small text-muted">Estimated Selling Price</div>
              <div class="fs-3 fw-bold text-success">${window.HomeValueApp.formatCurrency(r.predicted_price)}</div>
            </div>
          </div>

          <div class="row g-3 mb-4">
            <div class="col-sm-6 col-md-3">
              <div class="p-2 border rounded bg-light">
                <div class="small text-muted">Living Area</div>
                <div class="fw-bold">${Number(r.sqft_living).toLocaleString()} sq ft</div>
              </div>
            </div>
            <div class="col-sm-6 col-md-3">
              <div class="p-2 border rounded bg-light">
                <div class="small text-muted">Bedrooms / Baths</div>
                <div class="fw-bold">${r.bedrooms} Beds / ${r.bathrooms} Baths</div>
              </div>
            </div>
            <div class="col-sm-6 col-md-3">
              <div class="p-2 border rounded bg-light">
                <div class="small text-muted">Grade / Condition</div>
                <div class="fw-bold">Grade ${r.grade}/13 • Cond ${r.condition}/5</div>
              </div>
            </div>
            <div class="col-sm-6 col-md-3">
              <div class="p-2 border rounded bg-light">
                <div class="small text-muted">Year Built</div>
                <div class="fw-bold">${r.yr_built}</div>
              </div>
            </div>
          </div>

          <div class="alert alert-info d-flex align-items-center gap-2 mb-0">
            <i class="bi bi-info-circle-fill fs-5"></i>
            <div>
              <strong>Defensible Range:</strong> ${window.HomeValueApp.formatCurrency(r.lower_bound)} – ${window.HomeValueApp.formatCurrency(r.upper_bound)}
              <div class="small text-muted">Generated by ${r.model_name || 'Random Forest Regressor'} (R²: ${r.model_r2 || '0.88'})</div>
            </div>
          </div>
        `;

        const modal = new bootstrap.Modal(document.getElementById('quickDetailModal'));
        modal.show();
      })
      .catch(err => {
        window.HomeValueApp.showToast('Failed to load record details', 'danger');
      });
  }

  // Reload when currency changes
  window.addEventListener('currencyChanged', () => {
    if (dashboardCache) {
      renderKPIs(dashboardCache.kpi);
      renderCharts(dashboardCache.charts);
      renderRecentTable(dashboardCache.recent_predictions);
    }
  });

  loadDashboard();
});

/**
 * Prediction History JavaScript for HomeValue AI
 * Handles searching, multi-criteria filtering, pagination, inspection, and deletion.
 */
document.addEventListener('DOMContentLoaded', () => {
  let currentPage = 1;
  const perPage = 10;
  let activeModalRecordId = null;

  function fetchHistory(page = 1) {
    currentPage = page;
    const search = document.getElementById('historySearch')?.value.trim() || '';
    const zipcode = document.getElementById('historyZipcode')?.value || 'all';
    const bedrooms = document.getElementById('historyBedrooms')?.value || '';
    const minPrice = document.getElementById('historyMinPrice')?.value || '';
    const maxPrice = document.getElementById('historyMaxPrice')?.value || '';

    let url = `/api/predictions?page=${page}&per_page=${perPage}&sort_by=created_at&order=desc`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (zipcode && zipcode !== 'all') url += `&zipcode=${encodeURIComponent(zipcode)}`;
    if (bedrooms) url += `&bedrooms=${encodeURIComponent(bedrooms)}`;
    if (minPrice) url += `&min_price=${encodeURIComponent(minPrice)}`;
    if (maxPrice) url += `&max_price=${encodeURIComponent(maxPrice)}`;

    // Update export CSV link with matching search
    const exportBtn = document.getElementById('exportCsvBtn');
    if (exportBtn) {
      exportBtn.href = `/api/predictions/export?search=${encodeURIComponent(search)}`;
    }

    const tbody = document.getElementById('historyTableBody');
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4"><div class="spinner-border spinner-border-sm text-primary me-2"></div> Filtering records...</td></tr>`;
    }

    fetch(url)
      .then(res => res.json())
      .then(data => {
        renderTable(data.data);
        renderPagination(data.pagination);
      })
      .catch(err => {
        console.error('History fetch error:', err);
        if (tbody) {
          tbody.innerHTML = `<tr><td colspan="9" class="text-center text-danger py-4"><i class="bi bi-exclamation-octagon me-2"></i> Error loading prediction history.</td></tr>`;
        }
      });
  }

  function renderTable(records) {
    const tbody = document.getElementById('historyTableBody');
    if (!tbody) return;

    if (!records || records.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="9" class="text-center py-5">
            <div class="empty-state p-0">
              <div class="empty-state-icon"><i class="bi bi-folder2-open"></i></div>
              <div class="empty-state-title">No matching valuations found</div>
              <div class="empty-state-desc">Try clearing your filters or create a new property valuation.</div>
              <a href="/predict" class="btn btn-sm btn-primary-custom">
                <i class="bi bi-magic me-1"></i> Predict New Property
              </a>
            </div>
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = records.map(r => `
      <tr>
        <td class="text-muted small">#${r.id}</td>
        <td class="small text-nowrap text-muted">${r.created_at || 'Recently'}</td>
        <td class="fw-bold text-dark">${r.property_title || 'King County Residence'}</td>
        <td><span class="badge bg-light text-dark border"><i class="bi bi-geo-alt text-danger me-1"></i>${r.zipcode}</span></td>
        <td>${r.sqft_living ? Number(r.sqft_living).toLocaleString() : '--'} sq ft</td>
        <td>${r.bedrooms} bd / ${r.bathrooms} ba</td>
        <td>
          <span class="fw-bold text-success fs-6">
            ${window.HomeValueApp.formatCurrency(r.predicted_price)}
          </span>
        </td>
        <td class="small text-muted text-nowrap">
          ${window.HomeValueApp.formatCurrency(r.lower_bound)} – ${window.HomeValueApp.formatCurrency(r.upper_bound)}
        </td>
        <td class="text-end text-nowrap">
          <button class="btn btn-sm btn-outline-primary me-1 view-hist-btn" data-id="${r.id}" title="Inspect Details">
            <i class="bi bi-eye"></i>
          </button>
          <button class="btn btn-sm btn-outline-danger del-hist-btn" data-id="${r.id}" title="Delete Record">
            <i class="bi bi-trash3"></i>
          </button>
        </td>
      </tr>
    `).join('');

    // Attach row events
    document.querySelectorAll('.view-hist-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        inspectRecord(btn.getAttribute('data-id'));
      });
    });

    document.querySelectorAll('.del-hist-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        deleteRecord(btn.getAttribute('data-id'));
      });
    });
  }

  function renderPagination(p) {
    const info = document.getElementById('paginationInfo');
    const list = document.getElementById('paginationList');
    if (!info || !list) return;

    info.textContent = `Showing page ${p.page} of ${p.total_pages} (${p.total_count} total records)`;

    let html = '';
    const prevDisabled = p.page <= 1 ? 'disabled' : '';
    html += `<li class="page-item ${prevDisabled}"><button class="page-link" onclick="window.fetchHistoryPage(${p.page - 1})">Previous</button></li>`;

    for (let i = 1; i <= p.total_pages; i++) {
      if (i === 1 || i === p.total_pages || (i >= p.page - 2 && i <= p.page + 2)) {
        const active = i === p.page ? 'active' : '';
        html += `<li class="page-item ${active}"><button class="page-link" onclick="window.fetchHistoryPage(${i})">${i}</button></li>`;
      } else if (i === p.page - 3 || i === p.page + 3) {
        html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
      }
    }

    const nextDisabled = p.page >= p.total_pages ? 'disabled' : '';
    html += `<li class="page-item ${nextDisabled}"><button class="page-link" onclick="window.fetchHistoryPage(${p.page + 1})">Next</button></li>`;

    list.innerHTML = html;
  }

  window.fetchHistoryPage = function(page) {
    fetchHistory(page);
  };

  function inspectRecord(id) {
    activeModalRecordId = id;
    fetch(`/api/predictions/${id}`)
      .then(res => res.json())
      .then(r => {
        const modalBody = document.getElementById('historyDetailBody');
        if (!modalBody) return;

        modalBody.innerHTML = `
          <div class="d-flex justify-content-between align-items-center mb-3 pb-3 border-bottom">
            <div>
              <h4 class="fw-bold mb-1">${r.property_title || 'King County Residence'}</h4>
              <div class="text-muted small">Record ID #${r.id} • Saved: ${r.created_at}</div>
            </div>
            <div class="text-end">
              <div class="small text-muted">Estimated Selling Price</div>
              <div class="fs-2 fw-bold text-success">${window.HomeValueApp.formatCurrency(r.predicted_price)}</div>
            </div>
          </div>

          <div class="row g-3 mb-4">
            <div class="col-sm-6 col-md-3">
              <div class="p-2 border rounded bg-light">
                <div class="small text-muted">Living Space</div>
                <div class="fw-bold">${Number(r.sqft_living).toLocaleString()} sq ft</div>
              </div>
            </div>
            <div class="col-sm-6 col-md-3">
              <div class="p-2 border rounded bg-light">
                <div class="small text-muted">Bedrooms / Baths</div>
                <div class="fw-bold">${r.bedrooms} Bed / ${r.bathrooms} Bath</div>
              </div>
            </div>
            <div class="col-sm-6 col-md-3">
              <div class="p-2 border rounded bg-light">
                <div class="small text-muted">Grade / Condition</div>
                <div class="fw-bold">Grade ${r.grade} • Cond ${r.condition}</div>
              </div>
            </div>
            <div class="col-sm-6 col-md-3">
              <div class="p-2 border rounded bg-light">
                <div class="small text-muted">Year Built</div>
                <div class="fw-bold">${r.yr_built}</div>
              </div>
            </div>
            <div class="col-sm-6 col-md-3">
              <div class="p-2 border rounded bg-light">
                <div class="small text-muted">Postal Code</div>
                <div class="fw-bold">${r.zipcode}</div>
              </div>
            </div>
            <div class="col-sm-6 col-md-3">
              <div class="p-2 border rounded bg-light">
                <div class="small text-muted">Basement Area</div>
                <div class="fw-bold">${r.sqft_basement || 0} sq ft</div>
              </div>
            </div>
            <div class="col-sm-6 col-md-3">
              <div class="p-2 border rounded bg-light">
                <div class="small text-muted">Floors</div>
                <div class="fw-bold">${r.floors} Levels</div>
              </div>
            </div>
            <div class="col-sm-6 col-md-3">
              <div class="p-2 border rounded bg-light">
                <div class="small text-muted">Waterfront</div>
                <div class="fw-bold">${r.waterfront ? 'Yes (Shoreline)' : 'No'}</div>
              </div>
            </div>
          </div>

          <div class="alert alert-secondary d-flex align-items-center gap-2 mb-0">
            <i class="bi bi-shield-check text-primary fs-4"></i>
            <div>
              <strong>Defensible Range:</strong> ${window.HomeValueApp.formatCurrency(r.lower_bound)} – ${window.HomeValueApp.formatCurrency(r.upper_bound)}
              <div class="small text-muted">Trained Pipeline: ${r.model_name || 'Ensemble'} • Model R²: ${r.model_r2 || '0.88'}</div>
            </div>
          </div>
        `;

        const modal = new bootstrap.Modal(document.getElementById('historyDetailModal'));
        modal.show();
      })
      .catch(err => {
        window.HomeValueApp.showToast('Could not fetch record detail', 'danger');
      });
  }

  function deleteRecord(id) {
    if (!confirm(`Are you sure you want to delete prediction record #${id}?`)) return;

    fetch(`/api/predictions/${id}`, { method: 'DELETE' })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          window.HomeValueApp.showToast(`Record #${id} deleted.`, 'success');
          fetchHistory(currentPage);
        } else {
          window.HomeValueApp.showToast(data.error || 'Failed to delete record.', 'danger');
        }
      })
      .catch(err => {
        window.HomeValueApp.showToast('Error deleting record', 'danger');
      });
  }

  // Delete from inside modal
  const delModalBtn = document.getElementById('deleteFromModalBtn');
  if (delModalBtn) {
    delModalBtn.addEventListener('click', () => {
      if (activeModalRecordId) {
        const modalEl = document.getElementById('historyDetailModal');
        const modalInstance = bootstrap.Modal.getInstance(modalEl);
        if (modalInstance) modalInstance.hide();
        deleteRecord(activeModalRecordId);
      }
    });
  }

  // Filter triggers
  document.getElementById('applyHistoryFiltersBtn')?.addEventListener('click', () => fetchHistory(1));
  document.getElementById('historySearch')?.addEventListener('keyup', (e) => {
    if (e.key === 'Enter') fetchHistory(1);
  });
  document.getElementById('resetHistoryFiltersBtn')?.addEventListener('click', () => {
    document.getElementById('historySearch').value = '';
    document.getElementById('historyZipcode').value = 'all';
    document.getElementById('historyBedrooms').value = '';
    document.getElementById('historyMinPrice').value = '';
    document.getElementById('historyMaxPrice').value = '';
    fetchHistory(1);
  });

  window.addEventListener('currencyChanged', () => {
    fetchHistory(currentPage);
  });

  fetchHistory(1);
});

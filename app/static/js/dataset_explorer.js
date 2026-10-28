/**
 * Dataset Explorer JavaScript for HomeValue AI
 * Handles CSV uploads, dataset profiling, preview inspection, and controlled model retraining.
 */
document.addEventListener('DOMContentLoaded', () => {

  function loadDatasetSummary() {
    fetch('/api/dataset/summary')
      .then(res => res.json())
      .then(data => {
        renderSummaryKPIs(data);
        renderColumnsProfile(data.columns);
        renderPreviewTable(data.preview_columns, data.preview_rows);
      })
      .catch(err => {
        console.error('Error fetching dataset summary:', err);
        window.HomeValueApp?.showToast('Failed to load dataset details', 'danger');
      });
  }

  function renderSummaryKPIs(data) {
    const rowEl = document.getElementById('dsRowCount');
    const colEl = document.getElementById('dsColCount');
    const dupEl = document.getElementById('dsDupCount');
    const statusEl = document.getElementById('dsCompatStatus');
    const fileEl = document.getElementById('dsFileName');

    if (rowEl) rowEl.textContent = data.row_count ? Number(data.row_count).toLocaleString() : '0';
    if (colEl) colEl.textContent = data.col_count || '0';
    if (dupEl) dupEl.textContent = data.duplicate_count !== undefined ? Number(data.duplicate_count).toLocaleString() : '0';
    if (fileEl) fileEl.textContent = data.file_name || 'Active CSV';

    if (statusEl) {
      if (data.is_compatible) {
        statusEl.innerHTML = '<span class="text-success fw-bold"><i class="bi bi-check-circle-fill me-1"></i> Compatible</span>';
      } else {
        statusEl.innerHTML = '<span class="text-warning fw-bold"><i class="bi bi-exclamation-triangle-fill me-1"></i> Incomplete</span>';
      }
    }
  }

  function renderColumnsProfile(columns) {
    const tbody = document.getElementById('columnsProfileBody');
    if (!tbody || !columns) return;

    tbody.innerHTML = columns.map(c => {
      let roleBadge = '<span class="badge bg-light text-muted border">Ignored</span>';
      if (c.is_target) {
        roleBadge = '<span class="badge bg-danger-subtle text-danger border border-danger-subtle fw-bold">Target (y)</span>';
      } else if (c.is_supported) {
        roleBadge = '<span class="badge bg-primary-subtle text-primary border border-primary-subtle fw-bold">Model Feature (X)</span>';
      }

      const minMax = c.stats && c.stats.min !== undefined ? `${c.stats.min} / ${c.stats.max}` : '--';
      const meanMedian = c.stats && c.stats.mean !== undefined ? `${c.stats.mean} / ${c.stats.median}` : '--';

      return `
        <tr>
          <td class="fw-bold font-monospace">${c.name}</td>
          <td><span class="badge bg-secondary-subtle text-secondary">${c.dtype}</span></td>
          <td>${c.missing_count} (${c.missing_pct}%)</td>
          <td class="small text-muted">${minMax}</td>
          <td class="small text-muted">${meanMedian}</td>
          <td>${roleBadge}</td>
        </tr>
      `;
    }).join('');
  }

  function renderPreviewTable(cols, rows) {
    const thead = document.getElementById('previewHead');
    const tbody = document.getElementById('previewBody');
    if (!thead || !tbody || !cols || !rows) return;

    thead.innerHTML = `<tr>${cols.map(c => `<th>${c}</th>`).join('')}</tr>`;
    tbody.innerHTML = rows.map(r => `
      <tr>${cols.map(c => `<td>${r[c] !== undefined ? r[c] : ''}</td>`).join('')}</tr>
    `).join('');
  }

  // Upload Form Handler
  const uploadForm = document.getElementById('datasetUploadForm');
  if (uploadForm) {
    uploadForm.addEventListener('submit', (e) => {
      e.preventDefault();

      const fileInput = document.getElementById('csvFileInput');
      if (!fileInput.files.length) {
        window.HomeValueApp?.showToast('Please select a CSV file to upload.', 'warning');
        return;
      }

      const file = fileInput.files[0];
      if (!file.name.toLowerCase().endsWith('.csv')) {
        window.HomeValueApp?.showToast('Only .csv files are supported.', 'warning');
        return;
      }

      const formData = new FormData(uploadForm);
      const uploadBtn = document.getElementById('uploadBtn');
      if (uploadBtn) {
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Uploading & Profiling...';
      }

      fetch('/api/dataset/upload', {
        method: 'POST',
        body: formData
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          window.HomeValueApp?.showToast(data.message, 'success');
          loadDatasetSummary();
          uploadForm.reset();
        } else {
          window.HomeValueApp?.showToast(data.error || 'Upload validation failed.', 'danger');
          if (data.summary) {
            renderSummaryKPIs(data.summary);
            renderColumnsProfile(data.summary.columns);
          }
        }
      })
      .catch(err => {
        console.error('Upload error:', err);
        window.HomeValueApp?.showToast('Failed to upload dataset file.', 'danger');
      })
      .finally(() => {
        if (uploadBtn) {
          uploadBtn.disabled = false;
          uploadBtn.innerHTML = '<i class="bi bi-upload"></i> Upload & Inspect Schema';
        }
      });
    });
  }

  // Retrain Trigger Handlers
  const openModalBtn = document.getElementById('openRetrainModalBtn');
  const startTrainingBtn = document.getElementById('startTrainingNowBtn');
  const algorithmSelect = document.getElementById('algorithmSelect');
  const confirmAlgoLabel = document.getElementById('confirmAlgorithmLabel');

  if (openModalBtn) {
    openModalBtn.addEventListener('click', () => {
      const selectedText = algorithmSelect.options[algorithmSelect.selectedIndex].text;
      if (confirmAlgoLabel) confirmAlgoLabel.textContent = selectedText;
      const modal = new bootstrap.Modal(document.getElementById('retrainConfirmModal'));
      modal.show();
    });
  }

  if (startTrainingBtn) {
    startTrainingBtn.addEventListener('click', () => {
      const modalEl = document.getElementById('retrainConfirmModal');
      const modalInstance = bootstrap.Modal.getInstance(modalEl);
      if (modalInstance) modalInstance.hide();

      const modelType = algorithmSelect.value;
      window.HomeValueApp?.showToast('Training initiated! Please wait while models are evaluated...', 'info');

      startTrainingBtn.disabled = true;
      if (openModalBtn) {
        openModalBtn.disabled = true;
        openModalBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Training in progress...';
      }

      fetch('/api/model/retrain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_type: modelType })
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          window.HomeValueApp?.showToast(data.message, 'success');
          window.HomeValueApp?.fetchHealth();
        } else {
          window.HomeValueApp?.showToast(data.error || 'Retraining failed.', 'danger');
        }
      })
      .catch(err => {
        console.error('Retrain error:', err);
        window.HomeValueApp?.showToast('Error occurred during model training.', 'danger');
      })
      .finally(() => {
        startTrainingBtn.disabled = false;
        if (openModalBtn) {
          openModalBtn.disabled = false;
          openModalBtn.innerHTML = '<i class="bi bi-play-circle-fill"></i> Initiate Model Retraining';
        }
      });
    });
  }

  loadDatasetSummary();
});

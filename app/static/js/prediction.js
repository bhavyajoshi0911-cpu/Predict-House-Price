/**
 * Prediction Page JavaScript for HomeValue AI
 * Implements real-time live specs card, quick presets, AJAX inference, and defensible results.
 */

// Presets data definitions
const PRESETS = {
  starter: {
    property_title: "Seattle Starter Bungalow",
    zipcode: "98178",
    sqft_living: 1180,
    sqft_lot: 5650,
    bedrooms: "2",
    bathrooms: "1.0",
    floors: "1.0",
    grade: "6",
    condition: "3",
    yr_built: 1955,
    sqft_basement: 0,
    view: "0",
    waterfront: false
  },
  suburban: {
    property_title: "Redmond Suburban Residence",
    zipcode: "98052",
    sqft_living: 2650,
    sqft_lot: 8200,
    bedrooms: "4",
    bathrooms: "2.5",
    floors: "2.0",
    grade: "8",
    condition: "4",
    yr_built: 2004,
    sqft_basement: 450,
    view: "1",
    waterfront: false
  },
  luxury: {
    property_title: "Bellevue Waterfront Luxury Estate",
    zipcode: "98004",
    sqft_living: 4800,
    sqft_lot: 22000,
    bedrooms: "5",
    bathrooms: "4.0",
    floors: "2.0",
    grade: "10",
    condition: "5",
    yr_built: 2014,
    sqft_basement: 1200,
    view: "4",
    waterfront: true
  },
  craftsman: {
    property_title: "Green Lake Craftsman Home",
    zipcode: "98103",
    sqft_living: 2150,
    sqft_lot: 5000,
    bedrooms: "3",
    bathrooms: "2.0",
    floors: "2.0",
    grade: "7",
    condition: "4",
    yr_built: 1998,
    sqft_basement: 300,
    view: "0",
    waterfront: false
  }
};

let lastPredictionResult = null;

function applyPreset(name) {
  const p = PRESETS[name];
  if (!p) return;

  document.getElementById('property_title').value = p.property_title;
  document.getElementById('zipcode').value = p.zipcode;
  document.getElementById('sqft_living').value = p.sqft_living;
  document.getElementById('sqft_lot').value = p.sqft_lot;
  document.getElementById('bedrooms').value = p.bedrooms;
  document.getElementById('bathrooms').value = p.bathrooms;
  document.getElementById('floors').value = p.floors;
  document.getElementById('grade').value = p.grade;
  document.getElementById('condition').value = p.condition;
  document.getElementById('yr_built').value = p.yr_built;
  document.getElementById('sqft_basement').value = p.sqft_basement;
  document.getElementById('view').value = p.view;
  document.getElementById('waterfront').checked = p.waterfront;

  updateLivePreview();
  window.HomeValueApp?.showToast(`Loaded "${p.property_title}" preset.`, 'info');
}

function updateLivePreview() {
  const title = document.getElementById('property_title').value || 'King County Home';
  const zipcode = document.getElementById('zipcode').value;
  const sqft = document.getElementById('sqft_living').value || '0';
  const beds = document.getElementById('bedrooms').value;
  const baths = document.getElementById('bathrooms').value;
  const floors = document.getElementById('floors').value;
  const grade = document.getElementById('grade').value;
  const yrBuilt = document.getElementById('yr_built').value;

  const liveTitle = document.getElementById('livePropertyTitle');
  const liveLocation = document.getElementById('liveLocationSubtitle');
  const chipSqft = document.getElementById('chipSqft');
  const chipBeds = document.getElementById('chipBeds');
  const chipBaths = document.getElementById('chipBaths');
  const chipFloors = document.getElementById('chipFloors');
  const chipGrade = document.getElementById('chipGrade');
  const chipBuilt = document.getElementById('chipBuilt');

  if (liveTitle) liveTitle.textContent = title;
  if (liveLocation) liveLocation.textContent = `King County, Washington (ZIP ${zipcode})`;
  if (chipSqft) chipSqft.textContent = Number(sqft).toLocaleString();
  if (chipBeds) chipBeds.textContent = beds;
  if (chipBaths) chipBaths.textContent = baths;
  if (chipFloors) chipFloors.textContent = floors;
  if (chipGrade) chipGrade.textContent = grade;
  if (chipBuilt) chipBuilt.textContent = yrBuilt;
}

function resetForm() {
  document.getElementById('predictionForm').reset();
  applyPreset('craftsman');
  document.getElementById('postValuationState').style.display = 'none';
  document.getElementById('preValuationState').style.display = 'block';
  lastPredictionResult = null;
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('predictionForm');
  const spinner = document.getElementById('predictSpinner');

  // Attach live update listeners to inputs
  const inputIds = ['property_title', 'zipcode', 'sqft_living', 'sqft_lot', 'bedrooms', 'bathrooms', 'floors', 'grade', 'condition', 'yr_built', 'sqft_basement', 'view', 'waterfront'];
  inputIds.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('input', updateLivePreview);
      el.addEventListener('change', updateLivePreview);
    }
  });

  updateLivePreview();

  // Form submission
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();

      const sqftLiving = parseFloat(document.getElementById('sqft_living').value);
      if (isNaN(sqftLiving) || sqftLiving < 200 || sqftLiving > 30000) {
        window.HomeValueApp?.showToast('Living area must be between 200 and 30,000 sq ft.', 'warning');
        return;
      }

      // Collect payload
      const payload = {
        property_title: document.getElementById('property_title').value.trim() || 'Residential Valuation',
        zipcode: document.getElementById('zipcode').value,
        sqft_living: sqftLiving,
        sqft_lot: parseFloat(document.getElementById('sqft_lot').value) || sqftLiving * 3,
        bedrooms: parseInt(document.getElementById('bedrooms').value),
        bathrooms: parseFloat(document.getElementById('bathrooms').value),
        floors: parseFloat(document.getElementById('floors').value),
        grade: parseInt(document.getElementById('grade').value),
        condition: parseInt(document.getElementById('condition').value),
        yr_built: parseInt(document.getElementById('yr_built').value),
        sqft_basement: parseFloat(document.getElementById('sqft_basement').value) || 0,
        view: parseInt(document.getElementById('view').value) || 0,
        waterfront: document.getElementById('waterfront').checked ? 1 : 0
      };

      // Show spinner
      if (spinner) spinner.style.display = 'flex';

      fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      .then(res => {
        if (!res.ok) {
          return res.json().then(errData => { throw new Error(errData.error || 'Prediction request failed'); });
        }
        return res.json();
      })
      .then(result => {
        lastPredictionResult = result;
        displayPredictionResult(result);
        window.HomeValueApp?.showToast('Valuation computed successfully!', 'success');
      })
      .catch(err => {
        console.error('Prediction error:', err);
        window.HomeValueApp?.showToast(err.message, 'danger');
      })
      .finally(() => {
        if (spinner) spinner.style.display = 'none';
      });
    });
  }

  function displayPredictionResult(res) {
    const preState = document.getElementById('preValuationState');
    const postState = document.getElementById('postValuationState');

    if (preState) preState.style.display = 'none';
    if (postState) postState.style.display = 'block';

    const heroPrice = document.getElementById('resultHeroPrice');
    const priceRange = document.getElementById('resultPriceRange');
    const pricePerSqft = document.getElementById('resultPricePerSqft');
    const r2El = document.getElementById('resultModelR2');
    const maeEl = document.getElementById('resultModelMae');
    const timestampEl = document.getElementById('resultTimestamp');
    const driversList = document.getElementById('valuationDriversList');
    const uncertaintyText = document.getElementById('uncertaintyMethodText');

    if (heroPrice) heroPrice.textContent = window.HomeValueApp.formatCurrency(res.predicted_price);
    if (priceRange) {
      priceRange.textContent = `${window.HomeValueApp.formatCurrency(res.lower_bound)} – ${window.HomeValueApp.formatCurrency(res.upper_bound)}`;
    }
    if (pricePerSqft) {
      const formattedPerSqft = window.HomeValueApp.formatCurrency(res.price_per_sqft);
      pricePerSqft.textContent = `${formattedPerSqft} / sq ft`;
    }
    if (r2El) r2El.textContent = res.model_info.r2_score;
    if (maeEl) maeEl.textContent = window.HomeValueApp.formatCurrency(res.model_info.mae);
    if (timestampEl) timestampEl.textContent = new Date().toLocaleTimeString();

    if (uncertaintyText && res.model_info.uncertainty_method) {
      uncertaintyText.textContent = res.model_info.uncertainty_method;
    }

    if (driversList && res.valuation_drivers) {
      driversList.innerHTML = res.valuation_drivers.map(d => {
        const badgeColor = d.impact.includes('Positive') ? 'text-success' : (d.impact === 'Negative' ? 'text-danger' : 'text-secondary');
        const icon = d.impact.includes('Positive') ? 'bi-arrow-up-circle-fill' : (d.impact === 'Negative' ? 'bi-arrow-down-circle-fill' : 'bi-dash-circle-fill');
        return `
          <div class="mb-2 pb-1 border-bottom border-secondary border-opacity-10">
            <div class="d-flex align-items-center gap-1 fw-bold ${badgeColor}">
              <i class="bi ${icon}"></i> <span>${d.factor}</span>
            </div>
            <div class="text-secondary small ms-3">${d.description}</div>
          </div>
        `;
      }).join('');
    }

    // Scroll to results if on mobile
    if (window.innerWidth < 992) {
      postState.scrollIntoView({ behavior: 'smooth' });
    }
  }

  // Handle currency toggling dynamically
  window.addEventListener('currencyChanged', () => {
    if (lastPredictionResult) {
      displayPredictionResult(lastPredictionResult);
    }
  });
});

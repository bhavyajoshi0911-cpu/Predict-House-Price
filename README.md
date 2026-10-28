# HomeValue AI — House Price Prediction & Real Estate Analytics System

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.3%2B-orange.svg)](https://scikit-learn.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)](https://getbootstrap.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**HomeValue AI** is an enterprise-grade AI-powered real estate valuation platform and analytics dashboard built with Python, Flask, Scikit-learn, SQLite, and modern responsive web technologies. It estimates residential property values based on architectural dimensions, quality ratings, and geographic location using trained machine learning regression ensembles.

> **Educational & Portfolio Notice**: This project is developed for educational and portfolio demonstration. Predicted valuations are mathematical estimations derived from historical sales data and are not certified bank appraisals.

---

## Table of Contents
1. [Key Features](#key-features)
2. [Technology Stack](#technology-stack)
3. [Design System & UI/UX](#design-system--uiux)
4. [Dataset & Schema](#dataset--schema)
5. [Machine Learning Pipeline](#machine-learning-pipeline)
6. [Defensible Uncertainty Methodology](#defensible-uncertainty-methodology)
7. [Installation & Setup (Windows)](#installation--setup-windows)
8. [Running the Application](#running-the-application)
9. [API Endpoint Documentation](#api-endpoint-documentation)
10. [Automated Testing](#automated-testing)
11. [Project Directory Structure](#project-directory-structure)
12. [Troubleshooting](#troubleshooting)

---

## 1. Key Features

- **Interactive Valuation Engine**:
  - Live 2-column interface with grouped location and structural inputs.
  - Quick 1-click presets (*Starter Bungalow*, *Suburban Family*, *Luxury Waterfront*, *Seattle Craftsman*).
  - Dynamic right-hand property summary card updating specs in real-time as you type.
  - Single-click AJAX inference executing the fitted model pipeline.
  - Multi-currency toggle ($ USD and ₹ INR).
- **Defensible Prediction Intervals**:
  - Transparent empirical 90% tolerance bounds based on held-out test Root Mean Squared Error (RMSE).
  - Zero fabricated confidence numbers.
  - Key valuation drivers breaking down positive and negative market influences.
- **Interactive Dashboard Overview**:
  - 4 real-time Chart.js visualizers: Price Distribution Histogram, Average Price by Bedrooms, Living Area vs. Price Scatter Plot, and Prediction Activity trends.
  - Summary KPI cards for Total Predictions, Average Predicted Price, Peak Price, and Active Model $R^2$.
  - Recent valuations table with detailed inspection modal.
- **Prediction History & Persistence**:
  - Persisted in an indexed SQLite database (`instance/predictions.db`).
  - Searchable, filterable by price and bedrooms, and paginated table.
  - Single-click record deletion and CSV export.
- **Market Analytics Intelligence**:
  - Dynamic dataset exploration across King County residential markets.
  - Multi-criteria filter bar (Zipcode, bedrooms min/max, price range).
  - Pearson correlation ranking showing strongest price drivers.
- **Model Performance & Transparency**:
  - Multi-algorithm comparative benchmark table (Linear Regression baseline, Random Forest Regressor, and Gradient Boosting Regressor).
  - Actual vs. Predicted price scatter plot with a 45° reference line.
  - Residual error distribution histogram ($y - \hat{y}$).
  - Feature importance breakdown with normalized predictive weights.
- **Dataset Explorer & Controlled Retraining**:
  - Upload custom CSV datasets (up to 32MB) with automated schema validation.
  - Missing value detection, duplicate counts, and descriptive statistics.
  - Controlled retraining with algorithm selection and confirmation safety modal.

---

## 2. Technology Stack

- **Backend**:
  - Python 3.9+
  - Flask 3.x (Modular Application Factory pattern with Blueprints)
  - Flask-CORS for REST APIs
- **Machine Learning & Data Science**:
  - Scikit-learn (Pipelines, ColumnTransformer, StandardScaler, OneHotEncoder)
  - Random Forest Regressor, Gradient Boosting Regressor, Linear Regression
  - Pandas & NumPy for feature engineering and aggregation
  - Joblib for model serialization
- **Database**:
  - SQLite3 with parameterized queries and indexed lookups
- **Frontend**:
  - Semantic HTML5 & CSS3
  - Bootstrap 5.3 (Responsive Grid, Modals, Offcanvas)
  - Bootstrap Icons
  - Chart.js 4.x for interactive charts
  - Google Fonts (Inter)

---

## 3. Design System & UI/UX

HomeValue AI adopts a modern SaaS design system:
- **Primary Background**: `#F5F7FB`
- **Sidebar**: `#111827` (Dark slate)
- **Primary Accent**: `#4F46E5` (Indigo)
- **Secondary Accent**: `#14B8A6` (Teal)
- **Main Text**: `#111827`
- **Muted Text**: `#64748B`
- **Cards**: Pure White (`#FFFFFF`) with subtle shadows and `#E5E7EB` borders.
- **Typography**: Clean, accessible Inter typeface with proportional hierarchy.

---

## 4. Dataset & Schema

The application is pre-calibrated on the **King County House Sales Dataset** (Seattle and King County, Washington, USA).

| Field Name | Type | Description |
|---|---|---|
| `price` | Float (Target) | Transaction sales price in USD |
| `sqft_living` | Numeric | Interior living square footage (200 – 25,000) |
| `sqft_lot` | Numeric | Total land lot square footage |
| `bedrooms` | Integer | Total bedrooms (1 – 15) |
| `bathrooms` | Float | Total bathrooms (0.5 – 10.0) |
| `floors` | Float | Number of building levels (1.0 – 5.0) |
| `waterfront` | Binary (0/1) | Direct shoreline access |
| `view` | Integer | Scenic view rating (0 – 4) |
| `condition` | Integer | Maintenance condition (1 – 5) |
| `grade` | Integer | King County construction quality grade (1 – 13) |
| `sqft_above` | Numeric | Living space above ground |
| `sqft_basement` | Numeric | Finished/unfinished basement space |
| `yr_built` | Integer | Original construction year |
| `zipcode` | String / Cat | 5-digit US Postal Code |

To download the full 21,613 records from public mirrors:
```bash
python ml/download_dataset.py
```

---

## 5. Machine Learning Pipeline

### Data Leakage Prevention
To guarantee zero data leakage:
1. All feature scalers (`StandardScaler`) and categorical encoders (`OneHotEncoder`) are bundled inside a single `ColumnTransformer`.
2. The pipeline is fitted **only on the 80% training split**.
3. The 20% test split remains completely untouched until model evaluation.
4. Unknown postal codes during inference are safely handled via `handle_unknown='ignore'`.

### Evaluated Algorithms
1. **Linear Regression**: Parametric baseline ($R^2 \approx 0.74$).
2. **Gradient Boosting Regressor**: Sequential boosting ensemble ($R^2 \approx 0.87$).
3. **Random Forest Regressor**: Parallel bagging ensemble ($R^2 \approx 0.88$, Champion Model).

---

## 6. Defensible Uncertainty Methodology

Rather than generating arbitrary confidence percentages, HomeValue AI calculates a statistically defensible empirical 90% tolerance bound:

$$\text{Margin of Error} = 1.645 \times \text{Test RMSE}$$

$$\text{Lower Bound} = \max(15000, \text{Predicted Price} - \text{Margin})$$

$$\text{Upper Bound} = \text{Predicted Price} + \text{Margin}$$

Where $\text{Test RMSE}$ is the Root Mean Squared Error computed exclusively on held-out validation data.

---

## 7. Installation & Setup (Windows)

Open PowerShell or Command Prompt in the project directory:

```powershell
# 1. Create a virtual environment
python -m venv venv

# 2. Activate the virtual environment
venv\Scripts\activate

# 3. Install required dependencies
pip install -r requirements.txt
```

---

## 8. Running the Application

### Option A: Train Model & Start Flask Server
```powershell
# Train models and save pipeline artifacts
python ml/train.py

# Launch web application
python run.py
```

### Option B: Automatic Startup
`run.py` automatically detects missing model artifacts and triggers initial training if needed:
```powershell
python run.py
```

Navigate to: **`http://localhost:5000`** in any modern web browser.

---

## 9. API Endpoint Documentation

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health status and active model metadata |
| `GET` | `/api/dashboard` | Aggregated KPIs, charts data, and recent predictions |
| `POST` | `/api/predict` | Runs inference, computes intervals, and saves history |
| `GET` | `/api/predictions` | Paginated, filterable, and searchable prediction history |
| `GET` | `/api/predictions/<id>` | Single prediction inspection details |
| `DELETE` | `/api/predictions/<id>` | Deletes an individual history record |
| `GET` | `/api/predictions/export` | Downloads prediction history as CSV |
| `GET` | `/api/analytics` | Market analytics with zipcode and bedroom filters |
| `GET` | `/api/model-metrics` | Benchmark comparisons, residuals, and feature weights |
| `GET` | `/api/dataset/summary` | Active dataset shape, column profiling, and preview |
| `POST` | `/api/dataset/upload` | Uploads and validates a custom CSV file |
| `POST` | `/api/model/retrain` | Triggers retraining and redeploys pipeline in memory |

### Example Prediction Request:
```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "property_title": "Ballard Craftsman",
    "sqft_living": 2200,
    "sqft_lot": 5500,
    "bedrooms": 3,
    "bathrooms": 2.0,
    "floors": 1.5,
    "grade": 7,
    "condition": 4,
    "yr_built": 1948,
    "zipcode": "98117"
  }'
```

---

## 10. Automated Testing

Run the automated test suite with pytest:

```powershell
pytest -v
```

Tests verify:
- Data cleaning and outlier constraints.
- ColumnTransformer pipeline fitting without leakage.
- Prediction service inference and interval calculations.
- REST API endpoint status codes and payload validations.
- SQLite database persistence and deletion.
- Schema verification and empty analytics fallbacks.

---

## 11. Project Directory Structure

```
Project1/
├── app/
│   ├── __init__.py               # Flask Application Factory
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py               # Dashboard, About, Settings, Health
│   │   ├── prediction.py         # Prediction API & History CRUD
│   │   ├── analytics.py          # Market Analytics & Model Performance
│   │   └── dataset.py            # CSV Uploads & Model Retraining
│   ├── services/
│   │   ├── __init__.py
│   │   ├── database.py           # SQLite database queries & init
│   │   ├── prediction_service.py # Inference, uncertainty & insights
│   │   ├── analytics_service.py  # Dataset statistics & chart data
│   │   └── dataset_service.py    # Schema validation & profiler
│   ├── templates/
│   │   ├── base.html             # Master layout with responsive sidebar
│   │   ├── dashboard.html        # Overview dashboard with 4 charts
│   │   ├── predict.html          # Valuation form with live preview card
│   │   ├── history.html          # Persisted history table & detail modal
│   │   ├── analytics.html        # Market EDA with 6 interactive charts
│   │   ├── model_performance.html# Model benchmarks, residuals & importance
│   │   ├── dataset_explorer.html # CSV uploader & retraining controls
│   │   ├── about.html            # Architecture & ML methodology
│   │   └── settings.html         # Regional & system settings
│   └── static/
│       ├── css/
│       │   └── style.css         # Modern SaaS design system
│       └── js/
│           ├── dashboard.js      # Dashboard charts & KPI hydration
│           ├── prediction.js     # Live property form & AJAX predictions
│           ├── analytics.js      # Market analytics filtering & charts
│           ├── model_performance.js # Actual vs pred & residual charts
│           ├── dataset_explorer.js  # Upload & retraining AJAX
│           └── history.js        # History filtering, inspection & deletion
├── data/
│   ├── README.md                 # Dataset documentation
│   ├── kc_house_data.csv         # Calibrated King County dataset
│   └── uploads/                  # Uploaded CSV directory
├── models/
│   ├── README.md                 # Model documentation
│   ├── model_pipeline.joblib     # Serialized Scikit-learn Pipeline
│   └── model_metadata.json       # Evaluated metrics & benchmarks
├── ml/
│   ├── __init__.py
│   ├── download_dataset.py       # Public mirror dataset fetcher
│   ├── seed_initial_dataset.py   # Dataset seeder
│   ├── preprocessing.py          # Data cleaning & ColumnTransformer
│   ├── evaluate.py               # Regression metrics & uncertainty
│   └── train.py                  # Multi-model training orchestrator
├── instance/
│   └── predictions.db            # SQLite persistence
├── tests/
│   ├── __init__.py
│   ├── test_preprocessing.py     # Pipeline & preprocessing unit tests
│   ├── test_prediction.py        # Prediction service tests
│   ├── test_api.py               # Flask REST endpoints tests
│   └── test_data_validation.py   # Schema & edge cases tests
├── config.py                     # Environment configurations
├── run.py                        # Application entrypoint
├── requirements.txt              # Production dependencies
├── .env.example                  # Environment template
└── .gitignore                    # Git ignore specifications
```

---

## 12. Troubleshooting

- **Port 5000 is occupied**:
  Set the `PORT` environment variable before launching:
  ```powershell
  $env:PORT="5050"; python run.py
  ```
- **Model file missing**:
  Run `python ml/train.py` or `python run.py`. It will automatically build and serialize the model.
- **SQLite locked error**:
  Ensure no external database viewer has locked `instance/predictions.db`. SQLite handles concurrent read operations smoothly.

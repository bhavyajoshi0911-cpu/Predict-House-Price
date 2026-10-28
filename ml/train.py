"""
Training script for HomeValue AI.
Trains and compares:
1. Linear Regression (Baseline)
2. Random Forest Regressor
3. Gradient Boosting Regressor

Selects the best performing pipeline on held-out test data,
saves the fitted pipeline to models/model_pipeline.joblib,
and writes comprehensive evaluation metadata to models/model_metadata.json.
"""
import os
import sys
import json
import logging
import datetime
from pathlib import Path
import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

# Add parent directory to sys.path so ml modules import cleanly
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml.preprocessing import (
    clean_data,
    build_pipeline,
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    TARGET_COLUMN
)
from ml.evaluate import (
    calculate_regression_metrics,
    extract_feature_importance,
    calculate_residual_summary
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def train_and_save_models(
    dataset_path: str = None,
    output_model_path: str = None,
    output_metadata_path: str = None,
    preferred_model: str = "auto"
) -> dict:
    """
    Executes the end-to-end ML training pipeline:
    Loads dataset -> Cleans -> Train/Test split -> Trains 3 models -> Evaluates on held-out test set
    -> Selects best model -> Saves pipeline and metadata.
    """
    if dataset_path is None:
        dataset_path = str(BASE_DIR / "data" / "kc_house_data.csv")
    if output_model_path is None:
        output_model_path = str(BASE_DIR / "models" / "model_pipeline.joblib")
    if output_metadata_path is None:
        output_metadata_path = str(BASE_DIR / "models" / "model_metadata.json")

    Path(output_model_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_metadata_path).parent.mkdir(parents=True, exist_ok=True)

    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file not found at: {dataset_path}")

    logger.info(f"Loading housing dataset from {dataset_path}...")
    raw_df = pd.read_csv(dataset_path)
    logger.info(f"Raw dataset shape: {raw_df.shape} ({len(raw_df)} rows, {len(raw_df.columns)} columns)")

    # Data cleaning and sanity validation
    clean_df = clean_data(raw_df, target_col=TARGET_COLUMN)
    logger.info(f"Cleaned dataset shape: {clean_df.shape}")

    # Verify required feature columns exist
    present_num = [c for c in NUMERICAL_FEATURES if c in clean_df.columns]
    present_cat = [c for c in CATEGORICAL_FEATURES if c in clean_df.columns]

    if len(present_num) == 0:
        raise ValueError("None of the required numerical features were found in the dataset.")

    X = clean_df[present_num + present_cat]
    y = clean_df[TARGET_COLUMN]

    # Train/test split with fixed random seed (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )
    logger.info(f"Split dataset into Train: {len(X_train)} samples, Test: {len(X_test)} samples")

    # Define candidate models
    candidate_configs = [
        {
            'name': 'Linear Regression (Baseline)',
            'short_name': 'LinearRegression',
            'model': LinearRegression()
        },
        {
            'name': 'Random Forest Regressor',
            'short_name': 'RandomForest',
            'model': RandomForestRegressor(
                n_estimators=100,
                max_depth=16,
                min_samples_split=4,
                random_state=42,
                n_jobs=-1
            )
        },
        {
            'name': 'Gradient Boosting Regressor',
            'short_name': 'GradientBoosting',
            'model': GradientBoostingRegressor(
                n_estimators=120,
                learning_rate=0.08,
                max_depth=5,
                subsample=0.85,
                random_state=42
            )
        }
    ]

    model_results = []
    trained_pipelines = {}

    for config in candidate_configs:
        name = config['name']
        short_name = config['short_name']
        logger.info(f"Training candidate model: {name}...")

        pipeline = build_pipeline(
            config['model'],
            numerical_features=present_num,
            categorical_features=present_cat
        )

        pipeline.fit(X_train, y_train)
        trained_pipelines[short_name] = (name, pipeline)

        # Evaluate on held-out test data
        y_pred = pipeline.predict(X_test)
        metrics = calculate_regression_metrics(y_test, y_pred)

        logger.info(f"Results for {name}: R2={metrics['r2']:.4f}, MAE=${metrics['mae']:,.2f}, RMSE=${metrics['rmse']:,.2f}")

        model_results.append({
            'name': name,
            'short_name': short_name,
            'metrics': metrics
        })

    # Select champion model
    if preferred_model != "auto" and preferred_model in trained_pipelines:
        best_short_name = preferred_model
        best_name, best_pipeline = trained_pipelines[best_short_name]
    else:
        # Choose model with highest R2 score on held-out test data
        best_candidate = max(model_results, key=lambda x: x['metrics']['r2'])
        best_short_name = best_candidate['short_name']
        best_name, best_pipeline = trained_pipelines[best_short_name]

    logger.info(f"Champion model selected: {best_name} (Highest test R2 score)")

    # Mark is_best flag in model comparisons
    comparison_table = []
    for res in model_results:
        comparison_table.append({
            'name': res['name'],
            'short_name': res['short_name'],
            'r2': res['metrics']['r2'],
            'mae': res['metrics']['mae'],
            'rmse': res['metrics']['rmse'],
            'mse': res['metrics']['mse'],
            'mape': res['metrics']['mape'],
            'is_best': (res['short_name'] == best_short_name)
        })

    # Extract feature importance and residuals for the champion pipeline
    y_test_pred = best_pipeline.predict(X_test)
    active_metrics = calculate_regression_metrics(y_test, y_test_pred)
    feature_importance = extract_feature_importance(best_pipeline, top_n=12)
    residual_info = calculate_residual_summary(y_test, y_test_pred, sample_size=50)

    # Calculate dataset statistics for UI helpers
    supported_zipcodes = sorted(list(clean_df['zipcode'].dropna().unique())) if 'zipcode' in clean_df.columns else []
    summary_ranges = {}
    for col in present_num:
        summary_ranges[col] = {
            'min': float(clean_df[col].min()),
            'max': float(clean_df[col].max()),
            'median': float(clean_df[col].median()),
            'mean': float(clean_df[col].mean())
        }

    # Save champion model pipeline with joblib
    joblib.dump(best_pipeline, output_model_path)
    logger.info(f"Fitted pipeline successfully saved to: {output_model_path}")

    # Build comprehensive metadata dictionary
    metadata = {
        'active_model_name': best_name,
        'active_model_type': best_short_name,
        'trained_at': datetime.datetime.now().isoformat(),
        'dataset_name': Path(dataset_path).name,
        'dataset_path': str(dataset_path),
        'dataset_total_rows': int(len(clean_df)),
        'train_samples': int(len(X_train)),
        'test_samples': int(len(X_test)),
        'features_used': present_num + present_cat,
        'numerical_features': present_num,
        'categorical_features': present_cat,
        'metrics': active_metrics,
        'model_comparisons': comparison_table,
        'feature_importance': feature_importance,
        'residual_summary': residual_info,
        'supported_zipcodes': supported_zipcodes,
        'summary_ranges': summary_ranges
    }

    with open(output_metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Model metadata successfully saved to: {output_metadata_path}")
    return metadata

if __name__ == '__main__':
    train_and_save_models()

"""
Model evaluation, uncertainty estimation, and interpretability functions for HomeValue AI.
Provides defensible metrics and statistical prediction intervals.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from typing import Dict, Any, List, Tuple
from ml.preprocessing import get_transformed_feature_names, NUMERICAL_FEATURES

def calculate_regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Computes standard regression evaluation metrics on held-out test data.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    mae = float(mean_absolute_error(y_true, y_pred))
    mse = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_true, y_pred))

    # Mean Absolute Percentage Error (avoiding zero division)
    non_zero = y_true > 0
    mape = float(np.mean(np.abs((y_true[non_zero] - y_pred[non_zero]) / y_true[non_zero])) * 100) if np.any(non_zero) else 0.0

    return {
        'mae': round(mae, 2),
        'mse': round(mse, 2),
        'rmse': round(rmse, 2),
        'r2': round(r2, 4),
        'mape': round(mape, 2)
    }

def calculate_prediction_interval(predicted_price: float, test_rmse: float, confidence_level: float = 0.90) -> Dict[str, Any]:
    """
    Calculates defensible uncertainty prediction interval.
    Method: Empirical prediction interval based on held-out test set Root Mean Squared Error (RMSE).
    For 90% confidence, Z = 1.645; for 95%, Z = 1.96.
    """
    z_table = {
        0.80: 1.282,
        0.90: 1.645,
        0.95: 1.960,
        0.99: 2.576
    }
    z_val = z_table.get(confidence_level, 1.645)
    margin = z_val * test_rmse

    lower_bound = max(15000.0, round(predicted_price - margin, -2))
    upper_bound = max(lower_bound + 1000.0, round(predicted_price + margin, -2))

    return {
        'lower_bound': lower_bound,
        'upper_bound': upper_bound,
        'margin_of_error': round(margin, 2),
        'confidence_level': f"{int(confidence_level * 100)}%",
        'method': f"Defensible empirical prediction interval ({int(confidence_level * 100)}% interval based on ±{z_val} × test RMSE)."
    }

def extract_feature_importance(pipeline, top_n: int = 12) -> List[Dict[str, Any]]:
    """
    Extracts feature importances or linear coefficients from the fitted pipeline.
    Maps importances back to readable human features.
    """
    try:
        model = pipeline.named_steps['model']
        preprocessor = pipeline.named_steps['preprocessor']
        feature_names = get_transformed_feature_names(preprocessor)

        importances = None
        technique = "Native Gini / Variance Reduction Importance"

        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importances = np.abs(model.coef_)
            technique = "Standardized Absolute Linear Regression Coefficients"

        if importances is None or len(importances) != len(feature_names):
            return []

        # Normalize to percentage
        total = np.sum(importances)
        if total > 0:
            norm_importances = (importances / total) * 100.0
        else:
            norm_importances = importances

        # Aggregate one-hot features back to high-level parent features if desired,
        # or list top individual features with nice labels
        results = []
        for name, weight, raw in zip(feature_names, norm_importances, importances):
            clean_name = name.replace('num__', '').replace('cat__', '').replace('zipcode_', 'Zip ')
            results.append({
                'feature': clean_name,
                'raw_feature': name,
                'importance': round(float(weight), 2),
                'technique': technique
            })

        # Sort descending by importance
        results.sort(key=lambda x: x['importance'], reverse=True)
        return results[:top_n]
    except Exception as e:
        return []

def calculate_residual_summary(y_true: np.ndarray, y_pred: np.ndarray, sample_size: int = 60) -> Dict[str, Any]:
    """
    Computes residual distribution and sample test points for Actual vs. Predicted charts.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    residuals = y_true - y_pred

    # Histogram of residuals
    counts, bin_edges = np.histogram(residuals, bins=10)
    histogram_bins = []
    for i in range(len(counts)):
        midpoint = (bin_edges[i] + bin_edges[i+1]) / 2.0
        histogram_bins.append({
            'bin_label': f"${int(bin_edges[i]/1000)}k to ${int(bin_edges[i+1]/1000)}k",
            'bin_start': round(float(bin_edges[i]), 0),
            'bin_end': round(float(bin_edges[i+1]), 0),
            'count': int(counts[i])
        })

    # Sample points for Actual vs Predicted scatter plot (stratified/evenly spaced)
    n = len(y_true)
    indices = np.linspace(0, n - 1, min(sample_size, n), dtype=int)
    scatter_points = []
    for idx in indices:
        scatter_points.append({
            'actual': round(float(y_true[idx]), 0),
            'predicted': round(float(y_pred[idx]), 0),
            'error': round(float(residuals[idx]), 0)
        })

    return {
        'histogram': histogram_bins,
        'scatter_sample': scatter_points,
        'stats': {
            'min_residual': round(float(np.min(residuals)), 2),
            'max_residual': round(float(np.max(residuals)), 2),
            'mean_residual': round(float(np.mean(residuals)), 2),
            'std_residual': round(float(np.std(residuals)), 2)
        }
    }

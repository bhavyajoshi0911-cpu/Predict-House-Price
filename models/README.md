# Model Artifacts Directory

This directory stores trained scikit-learn pipelines and model metadata serialized for the HomeValue AI application.

## Files
- `model_pipeline.joblib`: The serialized production Pipeline containing both the fitted `ColumnTransformer` (standard scaling + one-hot encoding) and the trained regression estimator (e.g., Random Forest or Gradient Boosting).
- `model_metadata.json`: Contains evaluation metrics calculated on the held-out test set ($R^2$, MAE, RMSE, MSE, MAPE), 3-model comparative benchmarks, feature importance weights, residual distributions, and dataset statistics.

## Reproducibility
To retrain and update models on the current dataset at any time:
```bash
python ml/train.py
```
Or use the **Dataset Explorer** in the web dashboard.

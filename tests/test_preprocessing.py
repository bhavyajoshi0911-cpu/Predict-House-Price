"""
Unit tests for data preprocessing and pipeline factories.
"""
import pytest
import pandas as pd
import numpy as np
from ml.preprocessing import (
    clean_data,
    build_preprocessor,
    build_pipeline,
    prepare_input_dataframe,
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    TARGET_COLUMN
)
from sklearn.linear_model import LinearRegression

def test_clean_data_removes_duplicates_and_invalids():
    raw_data = {
        'id': [1, 2, 2, 3, 4],
        'price': [300000.0, 450000.0, 450000.0, -1000.0, 500000.0],
        'bedrooms': [3, 4, 4, 3, 20],  # 20 bedrooms is unrealistic
        'bathrooms': [2.0, 2.5, 2.5, 2.0, 2.0],
        'sqft_living': [1800, 2400, 2400, 1500, 1800],
        'sqft_lot': [5000, 6000, 6000, 4000, 5000],
        'floors': [1.0, 2.0, 2.0, 1.0, 1.0],
        'grade': [7, 8, 8, 7, 7],
        'condition': [3, 4, 4, 3, 3],
        'yr_built': [1990, 2005, 2005, 1980, 1990],
        'zipcode': ['98103', '98052', '98052', '98103', '98103']
    }
    df = pd.DataFrame(raw_data)
    cleaned = clean_data(df, target_col='price')

    # Duplicate id 2 should be removed
    assert len(cleaned[cleaned['id'] == 2]) == 1
    # Negative price (-1000) should be dropped
    assert len(cleaned[cleaned['price'] < 0]) == 0
    # 20 bedrooms should be dropped
    assert len(cleaned[cleaned['bedrooms'] == 20]) == 0
    assert len(cleaned) == 2

def test_build_preprocessor_and_pipeline():
    X = pd.DataFrame({
        'sqft_living': [1500, 2200, 3100, 1800],
        'sqft_lot': [5000, 7000, 10000, 6000],
        'bedrooms': [2, 3, 4, 3],
        'bathrooms': [1.5, 2.0, 2.5, 2.0],
        'floors': [1.0, 2.0, 2.0, 1.0],
        'waterfront': [0, 0, 1, 0],
        'view': [0, 1, 3, 0],
        'condition': [3, 4, 4, 3],
        'grade': [7, 8, 10, 7],
        'sqft_above': [1500, 1800, 2500, 1800],
        'sqft_basement': [0, 400, 600, 0],
        'yr_built': [1970, 1995, 2010, 1985],
        'zipcode': ['98103', '98052', '98004', '98115']
    })
    y = np.array([350000, 550000, 1200000, 480000])

    pipeline = build_pipeline(
        LinearRegression(),
        numerical_features=NUMERICAL_FEATURES,
        categorical_features=CATEGORICAL_FEATURES
    )

    # Fit pipeline
    pipeline.fit(X, y)
    preds = pipeline.predict(X)
    assert len(preds) == 4
    assert np.all(preds > 0)

def test_prepare_input_dataframe_handles_defaults():
    sample_input = {
        'sqft_living': 2200,
        'bedrooms': 3,
        'bathrooms': 2.0,
        'zipcode': '98103'
    }
    df = prepare_input_dataframe(sample_input)
    assert df.shape == (1, 13)
    assert df['sqft_living'].iloc[0] == 2200
    assert df['sqft_above'].iloc[0] == 2200  # Automatically derived
    assert df['zipcode'].iloc[0] == '98103'

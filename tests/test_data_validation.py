"""
Tests for schema validation, CSV inspection, and edge cases.
"""
import pytest
import os
import tempfile
import pandas as pd
from app.services.dataset_service import DatasetService
from app.services.analytics_service import AnalyticsService

def test_dataset_summary_valid_csv():
    temp_dir = tempfile.mkdtemp()
    csv_path = os.path.join(temp_dir, "test_valid.csv")
    
    df = pd.DataFrame({
        'bedrooms': [3, 4, 2],
        'bathrooms': [2.0, 2.5, 1.0],
        'sqft_living': [2000, 2500, 1200],
        'price': [450000, 600000, 280000],
        'zipcode': ['98103', '98052', '98178']
    })
    df.to_csv(csv_path, index=False)

    service = DatasetService(dataset_path=csv_path, upload_folder=temp_dir)
    summary = service.get_dataset_summary(csv_path)

    assert summary['exists'] is True
    assert summary['row_count'] == 3
    assert summary['col_count'] == 5
    assert summary['is_compatible'] is True

def test_dataset_summary_incompatible_csv():
    temp_dir = tempfile.mkdtemp()
    csv_path = os.path.join(temp_dir, "test_bad.csv")
    
    df = pd.DataFrame({
        'random_col': [1, 2, 3],
        'other_col': ['a', 'b', 'c']
    })
    df.to_csv(csv_path, index=False)

    service = DatasetService(dataset_path=csv_path, upload_folder=temp_dir)
    summary = service.get_dataset_summary(csv_path)

    assert summary['is_compatible'] is False
    assert len(summary['missing_essentials']) > 0

def test_analytics_with_empty_or_unmatched_filters():
    temp_dir = tempfile.mkdtemp()
    csv_path = os.path.join(temp_dir, "test_analytics.csv")
    
    df = pd.DataFrame({
        'bedrooms': [3, 4],
        'bathrooms': [2.0, 2.5],
        'sqft_living': [2000, 2500],
        'price': [450000, 600000],
        'zipcode': ['98103', '98052']
    })
    df.to_csv(csv_path, index=False)

    analytics = AnalyticsService(dataset_path=csv_path)
    # Filter for non-existent zipcode
    res = analytics.get_market_analytics(zipcode='99999')
    assert res['total_properties'] == 0
    assert res['summary']['avg_price'] == 0

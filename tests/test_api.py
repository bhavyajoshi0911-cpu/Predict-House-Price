"""
Integration tests for Flask REST endpoints and HTML routes.
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from app import create_app
from ml.train import train_and_save_models

@pytest.fixture(scope="module")
def client():
    app = create_app('testing')
    
    # Train test model if not present
    if not os.path.exists(app.config['MODEL_PATH']):
        train_and_save_models(
            dataset_path=app.config['DATASET_PATH'],
            output_model_path=app.config['MODEL_PATH'],
            output_metadata_path=app.config['METADATA_PATH'],
            preferred_model="LinearRegression"
        )
        app.prediction_service.load_model()

    with app.test_client() as test_client:
        with app.app_context():
            yield test_client

def test_health_endpoint(client):
    res = client.get('/api/health')
    assert res.status_code == 200
    data = res.get_json()
    assert 'status' in data
    assert 'model_loaded' in data

def test_html_pages_render(client):
    endpoints = ['/', '/predict', '/history', '/analytics', '/model-performance', '/dataset-explorer', '/about', '/settings']
    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 200, f"Page {ep} failed to render"

def test_api_predict_flow(client):
    payload = {
        'property_title': 'Ballard Craftsman',
        'sqft_living': 2250,
        'sqft_lot': 5000,
        'bedrooms': 3,
        'bathrooms': 2.0,
        'floors': 1.5,
        'grade': 7,
        'condition': 4,
        'yr_built': 1930,
        'zipcode': '98117'
    }
    res = client.post('/api/predict', data=json.dumps(payload), content_type='application/json')
    assert res.status_code == 200
    data = res.get_json()
    assert data['predicted_price'] > 50000
    assert 'formatted_price' in data
    assert 'lower_bound' in data
    assert data['id'] is not None
    pred_id = data['id']

    # Retrieve history
    hist_res = client.get('/api/predictions')
    assert hist_res.status_code == 200
    hist_data = hist_res.get_json()
    assert hist_data['pagination']['total_count'] >= 1

    # Detail
    detail_res = client.get(f'/api/predictions/{pred_id}')
    assert detail_res.status_code == 200

    # Delete
    del_res = client.delete(f'/api/predictions/{pred_id}')
    assert del_res.status_code == 200

def test_api_predict_validation_errors(client):
    # Missing payload
    res = client.post('/api/predict', data=json.dumps({}), content_type='application/json')
    assert res.status_code in [400, 422]

    # Non-json
    res_raw = client.post('/api/predict', data="not json")
    assert res_raw.status_code == 400

def test_api_analytics_endpoint(client):
    res = client.get('/api/analytics')
    assert res.status_code == 200
    data = res.get_json()
    assert 'summary' in data
    assert 'price_histogram' in data
    assert 'bedrooms_data' in data

def test_api_model_metrics_endpoint(client):
    res = client.get('/api/model-metrics')
    assert res.status_code == 200
    data = res.get_json()
    assert 'metrics' in data
    assert 'model_comparisons' in data

def test_api_export_endpoint(client):
    res = client.get('/api/predictions/export')
    assert res.status_code == 200
    assert 'text/csv' in res.content_type

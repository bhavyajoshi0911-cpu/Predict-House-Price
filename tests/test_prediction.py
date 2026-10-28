"""
Unit tests for PredictionService and valuation logic.
"""
import pytest
import os
import tempfile
from pathlib import Path
from app.services.prediction_service import PredictionService
from app.services.database import init_db
from ml.train import train_and_save_models

@pytest.fixture(scope="module")
def setup_test_service():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_predictions.db")
    model_path = os.path.join(temp_dir, "test_model.joblib")
    meta_path = os.path.join(temp_dir, "test_meta.json")
    dataset_path = str(Path(__file__).resolve().parent.parent / "data" / "kc_house_data.csv")

    init_db(db_path)
    train_and_save_models(
        dataset_path=dataset_path,
        output_model_path=model_path,
        output_metadata_path=meta_path,
        preferred_model="LinearRegression"
    )

    service = PredictionService(
        model_path=model_path,
        metadata_path=meta_path,
        db_path=db_path
    )
    return service

def test_prediction_service_is_ready(setup_test_service):
    service = setup_test_service
    assert service.is_ready() is True
    meta = service.get_metadata()
    assert 'active_model_name' in meta
    assert meta['metrics']['r2'] is not None

def test_prediction_service_successful_prediction(setup_test_service):
    service = setup_test_service
    prop = {
        'sqft_living': 2100,
        'sqft_lot': 6000,
        'bedrooms': 3,
        'bathrooms': 2.0,
        'floors': 1.0,
        'grade': 7,
        'condition': 3,
        'yr_built': 1995,
        'zipcode': '98103'
    }
    result = service.predict(prop, save_to_history=True)
    assert result['predicted_price'] > 50000
    assert result['lower_bound'] < result['predicted_price']
    assert result['upper_bound'] > result['predicted_price']
    assert result['price_per_sqft'] > 0
    assert len(result['valuation_drivers']) > 0
    assert result['id'] is not None

def test_prediction_service_rejects_invalid_inputs(setup_test_service):
    service = setup_test_service
    # Negative living area
    with pytest.raises(ValueError):
        service.predict({'sqft_living': -500, 'bedrooms': 3})

    # Zero bedrooms
    with pytest.raises(ValueError):
        service.predict({'sqft_living': 1500, 'bedrooms': 0})

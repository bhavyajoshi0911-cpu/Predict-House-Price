"""
Prediction service for HomeValue AI.
Loads the fitted scikit-learn pipeline once into memory, performs validation,
runs inference, calculates defensible uncertainty bounds, extracts property insights,
and records predictions to the SQLite database.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import joblib
import pandas as pd
import numpy as np

from ml.preprocessing import (
    prepare_input_dataframe,
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    DEFAULT_FEATURE_VALUES
)
from ml.evaluate import calculate_prediction_interval
from app.services.database import save_prediction

logger = logging.getLogger(__name__)

class PredictionService:
    def __init__(self, model_path: str, metadata_path: str, db_path: str):
        self.model_path = model_path
        self.metadata_path = metadata_path
        self.db_path = db_path
        self.pipeline = None
        self.metadata = None
        self.load_model()

    def load_model(self):
        """Loads or reloads the serialized pipeline and metadata from disk."""
        if os.path.exists(self.model_path):
            try:
                self.pipeline = joblib.load(self.model_path)
                logger.info(f"Loaded ML pipeline successfully from {self.model_path}")
            except Exception as e:
                logger.error(f"Failed to load model pipeline from {self.model_path}: {e}")
                self.pipeline = None
        else:
            logger.warning(f"Model file not found at {self.model_path}. Please run ml/train.py first.")
            self.pipeline = None

        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                logger.info(f"Loaded model metadata from {self.metadata_path}")
            except Exception as e:
                logger.error(f"Failed to load metadata from {self.metadata_path}: {e}")
                self.metadata = None
        else:
            self.metadata = None

    def is_ready(self) -> bool:
        """Returns True if the pipeline is loaded and ready for predictions."""
        return self.pipeline is not None

    def get_metadata(self) -> Dict[str, Any]:
        """Returns active model metadata or fallback default structure."""
        if self.metadata:
            return self.metadata
        return {
            'active_model_name': 'No Trained Model Loaded',
            'active_model_type': 'None',
            'trained_at': None,
            'metrics': {'r2': 0.0, 'mae': 0.0, 'rmse': 0.0, 'mse': 0.0},
            'model_comparisons': [],
            'feature_importance': [],
            'supported_zipcodes': [],
            'summary_ranges': {}
        }

    def validate_inputs(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validates user property inputs.
        Rejects negative or physically impossible values.
        """
        cleaned = {}
        try:
            # sqft_living
            sqft_living = float(data.get('sqft_living', 0))
            if sqft_living < 200 or sqft_living > 30000:
                return False, "Living area must be between 200 and 30,000 sq ft.", {}
            cleaned['sqft_living'] = sqft_living

            # bedrooms
            bedrooms = int(float(data.get('bedrooms', 0)))
            if bedrooms < 1 or bedrooms > 15:
                return False, "Number of bedrooms must be between 1 and 15.", {}
            cleaned['bedrooms'] = bedrooms

            # bathrooms
            bathrooms = float(data.get('bathrooms', 0))
            if bathrooms < 0.5 or bathrooms > 12:
                return False, "Number of bathrooms must be between 0.5 and 12.", {}
            cleaned['bathrooms'] = bathrooms

            # sqft_lot
            sqft_lot = float(data.get('sqft_lot', sqft_living * 3))
            if sqft_lot < 200:
                sqft_lot = sqft_living
            cleaned['sqft_lot'] = sqft_lot

            # floors
            floors = float(data.get('floors', 1.0))
            if floors < 1.0 or floors > 5.0:
                floors = 1.0
            cleaned['floors'] = floors

            # grade
            grade = int(float(data.get('grade', 7)))
            if grade < 1 or grade > 13:
                grade = 7
            cleaned['grade'] = grade

            # condition
            condition = int(float(data.get('condition', 3)))
            if condition < 1 or condition > 5:
                condition = 3
            cleaned['condition'] = condition

            # yr_built
            yr_built = int(float(data.get('yr_built', 1990)))
            if yr_built < 1850 or yr_built > 2030:
                yr_built = 1990
            cleaned['yr_built'] = yr_built

            # waterfront & view
            cleaned['waterfront'] = 1 if int(float(data.get('waterfront', 0))) == 1 else 0
            cleaned['view'] = int(float(data.get('view', 0)))
            if cleaned['view'] < 0 or cleaned['view'] > 4:
                cleaned['view'] = 0

            # sqft_above & sqft_basement
            sqft_basement = float(data.get('sqft_basement', 0))
            sqft_basement = max(0, sqft_basement)
            sqft_above = float(data.get('sqft_above', max(0, sqft_living - sqft_basement)))
            if sqft_above + sqft_basement != sqft_living:
                sqft_above = max(0, sqft_living - sqft_basement)
            cleaned['sqft_above'] = sqft_above
            cleaned['sqft_basement'] = sqft_basement

            # zipcode
            zipcode = str(data.get('zipcode', '98103')).strip().replace('.0', '')
            if not zipcode:
                zipcode = '98103'
            cleaned['zipcode'] = zipcode

            # optional property title
            cleaned['property_title'] = str(data.get('property_title', '')).strip()

            return True, None, cleaned
        except (ValueError, TypeError) as e:
            return False, f"Invalid numeric input: {str(e)}", {}

    def predict(self, property_data: Dict[str, Any], save_to_history: bool = True) -> Dict[str, Any]:
        """
        Runs model prediction on the property features, calculates uncertainty,
        evaluates key drivers, and persists the record to SQLite.
        """
        if not self.is_ready():
            raise RuntimeError("Machine learning model is not loaded. Please train or upload a model first.")

        # Validate inputs
        is_valid, err_msg, cleaned_data = self.validate_inputs(property_data)
        if not is_valid:
            raise ValueError(err_msg)

        # Convert to DataFrame matching training format
        input_df = prepare_input_dataframe(cleaned_data)

        # Run model inference
        raw_pred = self.pipeline.predict(input_df)[0]
        predicted_price = max(25000.0, round(float(raw_pred), -2))

        # Retrieve model metadata & evaluation metrics
        meta = self.get_metadata()
        model_name = meta.get('active_model_name', 'Random Forest Regressor')
        metrics = meta.get('metrics', {})
        test_rmse = float(metrics.get('rmse', 85000.0))
        model_r2 = float(metrics.get('r2', 0.85))
        model_mae = float(metrics.get('mae', 60000.0))

        # Calculate defensible prediction bounds
        uncertainty = calculate_prediction_interval(predicted_price, test_rmse, confidence_level=0.90)
        lower_bound = uncertainty['lower_bound']
        upper_bound = uncertainty['upper_bound']

        # Price per square foot
        price_per_sqft = round(predicted_price / max(1.0, cleaned_data['sqft_living']), 2)

        # Generate interpretability drivers
        drivers = self._analyze_property_drivers(cleaned_data, predicted_price, price_per_sqft)

        # Prepare record for persistence
        record = {
            **cleaned_data,
            'predicted_price': predicted_price,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'model_name': model_name,
            'model_r2': model_r2,
            'model_mae': model_mae
        }

        pred_id = None
        if save_to_history:
            try:
                pred_id = save_prediction(self.db_path, record)
            except Exception as e:
                logger.error(f"Failed to save prediction record to database: {e}")

        return {
            'id': pred_id,
            'predicted_price': predicted_price,
            'formatted_price': f"${predicted_price:,.0f}",
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'formatted_range': f"${lower_bound:,.0f} – ${upper_bound:,.0f}",
            'price_per_sqft': price_per_sqft,
            'currency': 'USD',
            'model_info': {
                'name': model_name,
                'r2_score': model_r2,
                'mae': model_mae,
                'rmse': test_rmse,
                'uncertainty_method': uncertainty['method'],
                'confidence_level': uncertainty['confidence_level']
            },
            'valuation_drivers': drivers,
            'inputs_used': cleaned_data
        }

    def _analyze_property_drivers(self, data: Dict[str, Any], predicted_price: float, price_per_sqft: float) -> List[Dict[str, Any]]:
        """Identifies key property characteristics and their valuation influence."""
        drivers = []

        # Living space factor
        sqft = data['sqft_living']
        if sqft > 3000:
            drivers.append({
                'factor': 'Generous Living Space',
                'impact': 'Positive',
                'description': f"{sqft:,.0f} sq ft interior living area is in the upper quartile for this market."
            })
        elif sqft < 1200:
            drivers.append({
                'factor': 'Compact Floorplan',
                'impact': 'Neutral',
                'description': f"{sqft:,.0f} sq ft interior is optimized for starter/low-maintenance living."
            })
        else:
            drivers.append({
                'factor': 'Typical Living Area',
                'impact': 'Neutral',
                'description': f"{sqft:,.0f} sq ft interior aligns with median family housing."
            })

        # Construction grade factor
        grade = data.get('grade', 7)
        if grade >= 9:
            drivers.append({
                'factor': f'High Construction Grade ({grade}/13)',
                'impact': 'Positive',
                'description': 'Superior architectural design, custom woodwork, and premium materials.'
            })
        elif grade <= 6:
            drivers.append({
                'factor': f'Basic Construction Grade ({grade}/13)',
                'impact': 'Negative',
                'description': 'Standard builder-grade construction with simple finishes.'
            })

        # Waterfront / View factor
        if data.get('waterfront', 0) == 1:
            drivers.append({
                'factor': 'Direct Waterfront Access',
                'impact': 'Strong Positive',
                'description': 'Waterfront shoreline location delivers a substantial market premium.'
            })
        elif data.get('view', 0) >= 2:
            drivers.append({
                'factor': f"Scenic View Rating ({data['view']}/4)",
                'impact': 'Positive',
                'description': 'Elevated or panoramic scenic outlook adds notable market appeal.'
            })

        # Age and condition
        age = 2026 - data.get('yr_built', 1990)
        cond = data.get('condition', 3)
        if age < 15:
            drivers.append({
                'factor': 'Modern Construction Age',
                'impact': 'Positive',
                'description': f"Built in {data.get('yr_built')}, requiring minimal immediate capital repairs."
            })
        elif cond >= 4:
            drivers.append({
                'factor': f'Excellent Maintenance Condition ({cond}/5)',
                'impact': 'Positive',
                'description': 'Well-maintained structural condition counterbalances property age.'
            })

        return drivers

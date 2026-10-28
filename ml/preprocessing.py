"""
Data preprocessing and pipeline definitions for HomeValue AI.
Ensures zero data leakage: preprocessors are fitted strictly on training data.
"""
import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from typing import List, Tuple, Dict, Any

NUMERICAL_FEATURES = [
    'sqft_living',
    'sqft_lot',
    'bedrooms',
    'bathrooms',
    'floors',
    'waterfront',
    'view',
    'condition',
    'grade',
    'sqft_above',
    'sqft_basement',
    'yr_built'
]

CATEGORICAL_FEATURES = [
    'zipcode'
]

TARGET_COLUMN = 'price'

# Default values for property estimation inputs
DEFAULT_FEATURE_VALUES = {
    'sqft_living': 2000,
    'sqft_lot': 7500,
    'bedrooms': 3,
    'bathrooms': 2.0,
    'floors': 1.0,
    'waterfront': 0,
    'view': 0,
    'condition': 3,
    'grade': 7,
    'sqft_above': 2000,
    'sqft_basement': 0,
    'yr_built': 1990,
    'zipcode': '98103'
}

def clean_data(df: pd.DataFrame, target_col: str = TARGET_COLUMN) -> pd.DataFrame:
    """
    Cleans raw housing data:
    - Removes duplicate records
    - Validates target price exists and is positive
    - Removes unrealistic outliers/impossible property configurations
    - Normalizes types (zipcode as string)
    """
    df = df.copy()

    # Drop duplicate property sales
    if 'id' in df.columns:
        df = df.drop_duplicates(subset=['id'], keep='last')
    else:
        df = df.drop_duplicates()

    # Ensure target column exists
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset.")

    # Remove non-numeric or missing target values
    df[target_col] = pd.to_numeric(df[target_col], errors='coerce')
    df = df.dropna(subset=[target_col])
    df = df[df[target_col] > 10000]  # Minimum realistic home price

    # Validate and normalize numerical columns
    for col in NUMERICAL_FEATURES:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Basic physical sanity constraints
    if 'bedrooms' in df.columns:
        df = df[(df['bedrooms'] >= 1) & (df['bedrooms'] <= 15)]
    if 'bathrooms' in df.columns:
        df = df[(df['bathrooms'] >= 0.5) & (df['bathrooms'] <= 10)]
    if 'sqft_living' in df.columns:
        df = df[(df['sqft_living'] >= 200) & (df['sqft_living'] <= 25000)]
    if 'sqft_lot' in df.columns:
        df = df[df['sqft_lot'] >= 200]
    if 'floors' in df.columns:
        df = df[(df['floors'] >= 1) & (df['floors'] <= 5)]
    if 'grade' in df.columns:
        df = df[(df['grade'] >= 1) & (df['grade'] <= 13)]
    if 'condition' in df.columns:
        df = df[(df['condition'] >= 1) & (df['condition'] <= 5)]
    if 'yr_built' in df.columns:
        df = df[(df['yr_built'] >= 1800) & (df['yr_built'] <= 2030)]

    # Format zipcode as string
    if 'zipcode' in df.columns:
        df['zipcode'] = df['zipcode'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)

    # Derive sqft_above / sqft_basement if missing
    if 'sqft_living' in df.columns:
        if 'sqft_above' not in df.columns and 'sqft_basement' in df.columns:
            df['sqft_above'] = df['sqft_living'] - df['sqft_basement']
        elif 'sqft_above' in df.columns and 'sqft_basement' not in df.columns:
            df['sqft_basement'] = (df['sqft_living'] - df['sqft_above']).clip(lower=0)
        elif 'sqft_above' not in df.columns and 'sqft_basement' not in df.columns:
            df['sqft_above'] = df['sqft_living']
            df['sqft_basement'] = 0

    return df

def build_preprocessor(numerical_features: List[str] = None, categorical_features: List[str] = None) -> ColumnTransformer:
    """
    Creates a scikit-learn ColumnTransformer for numerical scaling and categorical encoding.
    Fitted only on training data inside a Pipeline to prevent data leakage.
    """
    if numerical_features is None:
        numerical_features = NUMERICAL_FEATURES
    if categorical_features is None:
        categorical_features = CATEGORICAL_FEATURES

    numerical_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    categorical_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numerical_pipeline, numerical_features),
            ('cat', categorical_pipeline, categorical_features)
        ],
        remainder='drop'
    )

    return preprocessor

def build_pipeline(model: Any, numerical_features: List[str] = None, categorical_features: List[str] = None) -> Pipeline:
    """
    Builds an end-to-end scikit-learn Pipeline with preprocessing and model estimation.
    """
    preprocessor = build_preprocessor(numerical_features, categorical_features)
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('model', model)
    ])
    return pipeline

def get_transformed_feature_names(fitted_preprocessor: ColumnTransformer) -> List[str]:
    """
    Extracts explicit feature names after ColumnTransformer and OneHotEncoder transformation.
    """
    feature_names = []
    for name, trans, cols in fitted_preprocessor.transformers_:
        if name == 'remainder':
            continue
        if hasattr(trans, 'named_steps'):
            last_step = list(trans.named_steps.values())[-1]
            if hasattr(last_step, 'get_feature_names_out'):
                names = last_step.get_feature_names_out(cols)
                feature_names.extend(names)
            else:
                feature_names.extend(cols)
        else:
            feature_names.extend(cols)
    return [str(f) for f in feature_names]

def prepare_input_dataframe(data: Dict[str, Any]) -> pd.DataFrame:
    """
    Prepares and validates a single inference input dictionary into a model-ready pandas DataFrame.
    """
    record = {}
    for col in NUMERICAL_FEATURES:
        val = data.get(col)
        if val is None or val == '':
            val = DEFAULT_FEATURE_VALUES.get(col, 0)
        record[col] = float(val)

    # Check if sqft_above or sqft_basement were explicitly provided in data
    has_custom_above = 'sqft_above' in data and data['sqft_above'] not in (None, '')
    has_custom_basement = 'sqft_basement' in data and data['sqft_basement'] not in (None, '')

    if not has_custom_above:
        basement_val = record.get('sqft_basement', 0) if has_custom_basement else 0
        record['sqft_above'] = max(0, record['sqft_living'] - basement_val)
    elif record.get('sqft_above', 0) > record.get('sqft_living', 0):
        record['sqft_above'] = record['sqft_living']

    if not has_custom_basement:
        record['sqft_basement'] = max(0, record['sqft_living'] - record['sqft_above'])

    # Normalize zipcode
    zipcode_val = str(data.get('zipcode', DEFAULT_FEATURE_VALUES['zipcode'])).strip().replace('.0', '')
    record['zipcode'] = zipcode_val

    return pd.DataFrame([record])

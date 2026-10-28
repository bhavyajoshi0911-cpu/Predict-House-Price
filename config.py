import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'homevalue-ai-default-dev-secret-key-2026')
    DATABASE_PATH = os.environ.get('DATABASE_PATH', str(BASE_DIR / 'instance' / 'predictions.db'))
    DATASET_PATH = os.environ.get('DATASET_PATH', str(BASE_DIR / 'data' / 'kc_house_data.csv'))
    MODEL_PATH = os.environ.get('MODEL_PATH', str(BASE_DIR / 'models' / 'model_pipeline.joblib'))
    METADATA_PATH = os.environ.get('METADATA_PATH', str(BASE_DIR / 'models' / 'model_metadata.json'))
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', str(BASE_DIR / 'data' / 'uploads'))
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32 MB max upload
    ALLOWED_EXTENSIONS = {'csv'}
    DEFAULT_CURRENCY = os.environ.get('DEFAULT_CURRENCY', 'USD')
    USD_TO_INR_RATE = float(os.environ.get('USD_TO_INR_RATE', 83.5))
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    DATABASE_PATH = str(BASE_DIR / 'instance' / 'test_predictions.db')
    MODEL_PATH = str(BASE_DIR / 'models' / 'test_model_pipeline.joblib')
    METADATA_PATH = str(BASE_DIR / 'models' / 'test_model_metadata.json')

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

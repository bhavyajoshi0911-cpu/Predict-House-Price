"""
Flask Application Factory for HomeValue AI.
"""
import os
import logging
from flask import Flask, render_template, jsonify
from flask_cors import CORS

from config import config_by_name
from app.services.database import init_db
from app.services.prediction_service import PredictionService
from app.services.analytics_service import AnalyticsService
from app.services.dataset_service import DatasetService

def create_app(config_name: str = 'development') -> Flask:
    """Creates and configures an instance of the HomeValue AI Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    cfg = config_by_name.get(config_name, config_by_name['default'])
    app.config.from_object(cfg)

    # Enable CORS for REST endpoints
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    # Ensure required runtime directories exist
    os.makedirs(os.path.dirname(app.config['DATABASE_PATH']), exist_ok=True)
    os.makedirs(os.path.dirname(app.config['MODEL_PATH']), exist_ok=True)
    os.makedirs(os.path.dirname(app.config['DATASET_PATH']), exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize SQLite database schema
    init_db(app.config['DATABASE_PATH'])

    # Initialize singletons for services
    app.prediction_service = PredictionService(
        model_path=app.config['MODEL_PATH'],
        metadata_path=app.config['METADATA_PATH'],
        db_path=app.config['DATABASE_PATH']
    )
    app.analytics_service = AnalyticsService(
        dataset_path=app.config['DATASET_PATH']
    )
    app.dataset_service = DatasetService(
        dataset_path=app.config['DATASET_PATH'],
        upload_folder=app.config['UPLOAD_FOLDER']
    )

    # Register Blueprints
    from app.routes.main import main_bp
    from app.routes.prediction import prediction_bp
    from app.routes.analytics import analytics_bp
    from app.routes.dataset import dataset_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(dataset_bp)

    # Register Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('base.html', not_found=True), 404

    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({'error': 'Uploaded file exceeds the maximum permitted size limit (32MB).'}), 413

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {error}")
        return jsonify({'error': 'Internal server error occurred. Please try again.'}), 500

    return app

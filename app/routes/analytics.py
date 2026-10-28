"""
Market analytics and model performance routes for HomeValue AI.
"""
from flask import Blueprint, render_template, request, jsonify, current_app

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
def analytics_page():
    """Renders the interactive market analytics page."""
    meta = current_app.prediction_service.get_metadata()
    zipcodes = meta.get('supported_zipcodes', [])
    return render_template('analytics.html', active_page='analytics', zipcodes=zipcodes)

@analytics_bp.route('/model-performance')
def model_performance_page():
    """Renders the machine learning model performance evaluation page."""
    meta = current_app.prediction_service.get_metadata()
    return render_template('model_performance.html', active_page='model_performance', metadata=meta)

@analytics_bp.route('/api/analytics', methods=['GET'])
def api_get_analytics():
    """
    GET /api/analytics
    Returns dynamic market analytics with optional filtering by zipcode, bedrooms, price range.
    """
    zipcode = request.args.get('zipcode', '').strip() or None
    min_bedrooms = request.args.get('min_bedrooms', type=int)
    max_bedrooms = request.args.get('max_bedrooms', type=int)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)

    analytics_service = current_app.analytics_service
    data = analytics_service.get_market_analytics(
        zipcode=zipcode,
        min_bedrooms=min_bedrooms,
        max_bedrooms=max_bedrooms,
        min_price=min_price,
        max_price=max_price
    )
    return jsonify(data), 200

@analytics_bp.route('/api/model-metrics', methods=['GET'])
def api_get_model_metrics():
    """
    GET /api/model-metrics
    Returns active model evaluation metrics, 3-model benchmark comparisons,
    actual vs. predicted scatter sample, residual distributions, and feature importances.
    """
    prediction_service = current_app.prediction_service
    meta = prediction_service.get_metadata()
    return jsonify(meta), 200

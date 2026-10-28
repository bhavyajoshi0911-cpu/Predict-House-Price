"""
Main UI and dashboard routes for HomeValue AI.
"""
from flask import Blueprint, render_template, jsonify, current_app, request
import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def dashboard():
    """Renders the HomeValue AI dashboard overview page."""
    return render_template('dashboard.html', active_page='dashboard')

@main_bp.route('/about')
def about():
    """Renders the educational portfolio and project documentation page."""
    return render_template('about.html', active_page='about')

@main_bp.route('/settings')
def settings():
    """Renders the application configuration and preferences page."""
    return render_template('settings.html', active_page='settings')

@main_bp.route('/api/health')
def health():
    """Health check endpoint indicating model readiness and system status."""
    prediction_service = current_app.prediction_service
    is_ready = prediction_service.is_ready()
    meta = prediction_service.get_metadata()
    return jsonify({
        'status': 'healthy' if is_ready else 'degraded',
        'model_loaded': is_ready,
        'active_model': meta.get('active_model_name'),
        'trained_at': meta.get('trained_at'),
        'r2_score': meta.get('metrics', {}).get('r2', 0),
        'timestamp': datetime.datetime.now().isoformat()
    }), 200

@main_bp.route('/api/dashboard')
def dashboard_data():
    """
    Returns unified data for the Dashboard Overview:
    - Summary KPI cards (total predictions, avg price, max price, model R2)
    - Recent predictions table
    - Chart data (price distribution, avg price by bedrooms, area vs price, recent activity)
    """
    db_path = current_app.config['DATABASE_PATH']
    from app.services.database import get_history_summary_stats, get_predictions

    # Retrieve real prediction history stats
    history_stats = get_history_summary_stats(db_path)
    recent_records, total_count = get_predictions(db_path, per_page=6, sort_by='created_at', order='desc')

    # Retrieve model metadata for R2 and active model info
    pred_service = current_app.prediction_service
    meta = pred_service.get_metadata()
    model_r2 = meta.get('metrics', {}).get('r2', 0.0)
    model_name = meta.get('active_model_name', 'Random Forest Regressor')

    # Retrieve dataset analytics for base market context charts
    analytics_service = current_app.analytics_service
    market_data = analytics_service.get_market_analytics()

    # Extract dashboard charts
    price_histogram = market_data.get('price_histogram', [])
    bedrooms_chart = market_data.get('bedrooms_data', [])
    scatter_chart = market_data.get('scatter_sample', [])[:60]

    # Activity chart: aggregate recent predictions by date
    all_preds, _ = get_predictions(db_path, per_page=100)
    activity_map = {}
    for p in all_preds:
        date_str = str(p['created_at'])[:10]
        activity_map[date_str] = activity_map.get(date_str, 0) + 1

    # Format activity chart
    sorted_dates = sorted(activity_map.keys())[-7:]
    activity_chart = [{
        'date': d,
        'count': activity_map[d]
    } for d in sorted_dates]

    return jsonify({
        'kpi': {
            'total_predictions': history_stats['total_predictions'],
            'avg_predicted_price': history_stats['avg_price'],
            'max_predicted_price': history_stats['max_price'],
            'model_r2': model_r2,
            'model_name': model_name
        },
        'recent_predictions': recent_records,
        'charts': {
            'price_histogram': price_histogram,
            'bedrooms_data': bedrooms_chart,
            'scatter_sample': scatter_chart,
            'activity': activity_chart
        }
    }), 200

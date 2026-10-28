"""
Prediction endpoints and history routes for HomeValue AI.
"""
import io
import csv
from flask import Blueprint, render_template, request, jsonify, current_app, Response
from app.services.database import (
    get_predictions,
    get_prediction_by_id,
    delete_prediction
)

prediction_bp = Blueprint('prediction', __name__)

@prediction_bp.route('/predict')
def predict_page():
    """Renders the house price prediction page."""
    meta = current_app.prediction_service.get_metadata()
    zipcodes = meta.get('supported_zipcodes', [])
    return render_template('predict.html', active_page='predict', zipcodes=zipcodes, metadata=meta)

@prediction_bp.route('/history')
def history_page():
    """Renders the prediction history page."""
    meta = current_app.prediction_service.get_metadata()
    zipcodes = meta.get('supported_zipcodes', [])
    return render_template('history.html', active_page='history', zipcodes=zipcodes)

@prediction_bp.route('/api/predict', methods=['POST'])
def api_predict():
    """
    POST /api/predict
    Validates property specifications, executes the machine learning pipeline,
    computes defensible prediction bounds, and records history.
    """
    if not request.is_json:
        return jsonify({'error': 'Request payload must be JSON.'}), 400

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No property data provided.'}), 400

    try:
        pred_service = current_app.prediction_service
        result = pred_service.predict(data, save_to_history=True)
        return jsonify(result), 200
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 422
    except RuntimeError as re:
        return jsonify({'error': str(re)}), 503
    except Exception as e:
        current_app.logger.error(f"Prediction failed with unexpected error: {e}")
        return jsonify({'error': 'Internal prediction error. Please check feature inputs.'}), 500

@prediction_bp.route('/api/predictions', methods=['GET'])
def api_get_predictions():
    """
    GET /api/predictions
    Returns searchable, filterable, sortable, paginated prediction records.
    """
    db_path = current_app.config['DATABASE_PATH']
    search = request.args.get('search', '').strip() or None
    
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    bedrooms = request.args.get('bedrooms', type=int)
    zipcode = request.args.get('zipcode', '').strip() or None
    if zipcode == 'all':
        zipcode = None

    sort_by = request.args.get('sort_by', 'created_at')
    order = request.args.get('order', 'desc')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    per_page = min(max(1, per_page), 100)

    records, total_count = get_predictions(
        db_path=db_path,
        search=search,
        min_price=min_price,
        max_price=max_price,
        bedrooms=bedrooms,
        zipcode=zipcode,
        sort_by=sort_by,
        order=order,
        page=page,
        per_page=per_page
    )

    total_pages = max(1, (total_count + per_page - 1) // per_page)

    return jsonify({
        'data': records,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_count': total_count,
            'total_pages': total_pages
        }
    }), 200

@prediction_bp.route('/api/predictions/<int:pred_id>', methods=['GET'])
def api_get_prediction_detail(pred_id: int):
    """GET /api/predictions/<id> - Fetches detail for a single prediction."""
    db_path = current_app.config['DATABASE_PATH']
    record = get_prediction_by_id(db_path, pred_id)
    if not record:
        return jsonify({'error': 'Prediction record not found.'}), 404
    return jsonify(record), 200

@prediction_bp.route('/api/predictions/<int:pred_id>', methods=['DELETE'])
def api_delete_prediction(pred_id: int):
    """DELETE /api/predictions/<id> - Deletes a history record."""
    db_path = current_app.config['DATABASE_PATH']
    deleted = delete_prediction(db_path, pred_id)
    if not deleted:
        return jsonify({'error': 'Prediction record not found or already deleted.'}), 404
    return jsonify({'success': True, 'message': 'Prediction record deleted successfully.'}), 200

@prediction_bp.route('/api/predictions/export', methods=['GET'])
def api_export_predictions():
    """GET /api/predictions/export - Exports filtered prediction records as CSV."""
    db_path = current_app.config['DATABASE_PATH']
    search = request.args.get('search', '').strip() or None
    records, _ = get_predictions(db_path, search=search, per_page=1000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'ID', 'Date', 'Property Title', 'Living Area (sqft)', 'Lot Area (sqft)',
        'Bedrooms', 'Bathrooms', 'Floors', 'Condition', 'Grade',
        'Year Built', 'Zipcode', 'Predicted Price ($)', 'Lower Bound ($)',
        'Upper Bound ($)', 'Model Used'
    ])

    for r in records:
        writer.writerow([
            r['id'], r['created_at'], r['property_title'], r['sqft_living'],
            r['sqft_lot'], r['bedrooms'], r['bathrooms'], r['floors'],
            r['condition'], r['grade'], r['yr_built'], r['zipcode'],
            r['predicted_price'], r['lower_bound'], r['upper_bound'],
            r['model_name']
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=homevalue_ai_predictions.csv"}
    )

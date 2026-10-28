"""
Dataset explorer and model retraining routes for HomeValue AI.
"""
from flask import Blueprint, render_template, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os

dataset_bp = Blueprint('dataset', __name__)

@dataset_bp.route('/dataset-explorer')
def dataset_explorer_page():
    """Renders the dataset explorer interface."""
    return render_template('dataset_explorer.html', active_page='dataset_explorer')

@dataset_bp.route('/api/dataset/summary', methods=['GET'])
def api_get_dataset_summary():
    """
    GET /api/dataset/summary
    Returns row/column counts, missing values, duplicates, preview rows, and stats.
    """
    dataset_service = current_app.dataset_service
    summary = dataset_service.get_dataset_summary()
    return jsonify(summary), 200

@dataset_bp.route('/api/dataset/upload', methods=['POST'])
def api_upload_dataset():
    """
    POST /api/dataset/upload
    Handles CSV file upload, schema validation, and saves to uploads folder.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part found in upload request.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for upload.'}), 400

    filename = secure_filename(file.filename)
    dataset_service = current_app.dataset_service
    success, message, summary = dataset_service.validate_and_save_upload(file, filename)

    if not success:
        return jsonify({'error': message, 'summary': summary}), 422

    # If user checked 'set as active dataset'
    set_active = request.form.get('set_active', 'false').lower() == 'true'
    if set_active:
        dataset_service.activate_uploaded_dataset(filename)

    return jsonify({
        'success': True,
        'message': message,
        'filename': filename,
        'summary': summary
    }), 200

@dataset_bp.route('/api/dataset/validate', methods=['POST'])
def api_validate_dataset():
    """
    POST /api/dataset/validate
    Validates a dataset's schema and column compatibility.
    """
    dataset_service = current_app.dataset_service
    data = request.get_json() or {}
    filename = data.get('filename')

    target_path = None
    if filename:
        target_path = os.path.join(dataset_service.upload_folder, secure_filename(filename))

    summary = dataset_service.get_dataset_summary(target_path)
    return jsonify(summary), 200

@dataset_bp.route('/api/model/retrain', methods=['POST'])
def api_retrain_model():
    """
    POST /api/model/retrain
    Executes training on the active dataset with the selected model algorithm.
    Reloads the fitted pipeline immediately into memory upon completion.
    """
    data = request.get_json() or {}
    model_type = data.get('model_type', 'auto')
    uploaded_file = data.get('filename')

    dataset_service = current_app.dataset_service
    pred_service = current_app.prediction_service

    target_dataset = None
    if uploaded_file:
        target_dataset = os.path.join(dataset_service.upload_folder, secure_filename(uploaded_file))
        if not os.path.exists(target_dataset):
            return jsonify({'error': f"Target dataset file {uploaded_file} does not exist."}), 404

    try:
        current_app.logger.info(f"Triggering model retraining with algorithm: {model_type}...")
        new_metadata = dataset_service.trigger_retraining(
            dataset_path=target_dataset,
            model_type=model_type
        )

        # Reload newly trained model into the running prediction service
        pred_service.load_model()

        return jsonify({
            'success': True,
            'message': f"Model '{new_metadata['active_model_name']}' trained and deployed successfully!",
            'metadata': new_metadata
        }), 200
    except Exception as e:
        current_app.logger.error(f"Retraining failed: {e}")
        return jsonify({'error': f"Model retraining failed: {str(e)}"}), 500

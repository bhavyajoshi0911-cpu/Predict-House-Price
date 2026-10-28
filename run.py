"""
Entrypoint to run the HomeValue AI web application.
"""
import os
import sys
from pathlib import Path

# Ensure root workspace directory is in python path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import create_app

# Check if model exists, if not, train initial baseline
model_path = ROOT_DIR / "models" / "model_pipeline.joblib"
dataset_path = ROOT_DIR / "data" / "kc_house_data.csv"

if not model_path.exists() and dataset_path.exists():
    print("=" * 60)
    print("HomeValue AI: First-time initialization detected.")
    print("Training baseline ML models on King County dataset...")
    print("=" * 60)
    try:
        from ml.train import train_and_save_models
        train_and_save_models(
            dataset_path=str(dataset_path),
            output_model_path=str(model_path),
            output_metadata_path=str(ROOT_DIR / "models" / "model_metadata.json")
        )
        print("Initial model training completed successfully!")
    except Exception as e:
        print(f"Warning: Initial training encountered: {e}")

env = os.environ.get('FLASK_ENV', 'development')
app = create_app(env)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"HomeValue AI is running at: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=app.config.get('DEBUG', True))

"""
Dataset explorer and CSV validation service for HomeValue AI.
Handles CSV uploads, schema checks, descriptive statistics, and model retraining.
"""
import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np

from ml.preprocessing import NUMERICAL_FEATURES, CATEGORICAL_FEATURES, TARGET_COLUMN
from ml.train import train_and_save_models

logger = logging.getLogger(__name__)

class DatasetService:
    def __init__(self, dataset_path: str, upload_folder: str):
        self.dataset_path = dataset_path
        self.upload_folder = upload_folder
        Path(self.upload_folder).mkdir(parents=True, exist_ok=True)

    def get_dataset_summary(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Parses a CSV dataset and extracts summary statistics,
        column profiles, preview rows, and schema compliance.
        """
        target_path = file_path or self.dataset_path
        if not os.path.exists(target_path):
            return {
                'exists': False,
                'file_name': Path(target_path).name,
                'error': f"File not found: {target_path}"
            }

        try:
            df = pd.read_csv(target_path)
            row_count, col_count = df.shape
            duplicate_count = int(df.duplicated().sum())

            # Columns profiling
            columns_info = []
            for col in df.columns:
                missing_count = int(df[col].isna().sum())
                missing_pct = round((missing_count / max(1, row_count)) * 100, 1)
                dtype_str = str(df[col].dtype)
                
                stat_dict = {}
                if pd.api.types.is_numeric_dtype(df[col]):
                    non_na = df[col].dropna()
                    if len(non_na) > 0:
                        stat_dict = {
                            'min': round(float(non_na.min()), 2),
                            'max': round(float(non_na.max()), 2),
                            'mean': round(float(non_na.mean()), 2),
                            'median': round(float(non_na.median()), 2)
                        }

                is_supported = col in NUMERICAL_FEATURES or col in CATEGORICAL_FEATURES or col == TARGET_COLUMN
                is_target = col == TARGET_COLUMN or col.lower() in ['price', 'sale_price', 'saleprice', 'value']

                columns_info.append({
                    'name': col,
                    'dtype': dtype_str,
                    'missing_count': missing_count,
                    'missing_pct': missing_pct,
                    'is_supported': is_supported,
                    'is_target': is_target,
                    'stats': stat_dict
                })

            # First 8 preview rows (converted cleanly to dict)
            preview_df = df.head(8).fillna('')
            preview_rows = preview_df.to_dict(orient='records')
            preview_columns = list(df.columns)

            # Check core required schema compatibility
            required_essentials = ['bedrooms', 'bathrooms', 'sqft_living']
            missing_essentials = [req for req in required_essentials if req not in df.columns]
            has_price = any(c.lower() in ['price', 'sale_price', 'saleprice', 'value'] for c in df.columns)

            is_compatible = len(missing_essentials) == 0 and has_price

            return {
                'exists': True,
                'file_name': Path(target_path).name,
                'file_size_bytes': os.path.getsize(target_path),
                'row_count': row_count,
                'col_count': col_count,
                'duplicate_count': duplicate_count,
                'columns': columns_info,
                'preview_columns': preview_columns,
                'preview_rows': preview_rows,
                'is_compatible': is_compatible,
                'missing_essentials': missing_essentials,
                'has_price': has_price
            }
        except Exception as e:
            logger.error(f"Error summarizing dataset {target_path}: {e}")
            return {
                'exists': True,
                'file_name': Path(target_path).name,
                'error': f"Failed to parse CSV file: {str(e)}"
            }

    def validate_and_save_upload(self, file_storage, filename: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Saves uploaded CSV file safely and verifies its schema.
        """
        if not filename.lower().endswith('.csv'):
            return False, "Only CSV (.csv) files are permitted.", {}

        safe_filename = Path(filename).name
        dest_path = os.path.join(self.upload_folder, safe_filename)

        try:
            file_storage.save(dest_path)
            summary = self.get_dataset_summary(dest_path)
            if not summary.get('is_compatible'):
                missing = ", ".join(summary.get('missing_essentials', []))
                return False, f"Dataset lacks required housing columns: {missing}", summary
            return True, "Dataset successfully uploaded and validated.", summary
        except Exception as e:
            logger.error(f"Error handling upload: {e}")
            return False, f"Failed to save upload: {str(e)}", {}

    def activate_uploaded_dataset(self, uploaded_filename: str) -> bool:
        """Copies an uploaded dataset to become the active dataset."""
        source = os.path.join(self.upload_folder, uploaded_filename)
        if not os.path.exists(source):
            return False
        shutil.copyfile(source, self.dataset_path)
        return True

    def trigger_retraining(self, dataset_path: Optional[str] = None, model_type: str = "auto") -> Dict[str, Any]:
        """Runs the training pipeline and returns new evaluation metadata."""
        active_dataset = dataset_path or self.dataset_path
        metadata = train_and_save_models(
            dataset_path=active_dataset,
            preferred_model=model_type
        )
        return metadata

"""
SQLite database management for HomeValue AI prediction history.
Uses safe parameterized queries and connection context managers.
"""
import sqlite3
import datetime
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Creates a connection to the SQLite database with row factory enabled."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str):
    """Initializes the database schema if not already present."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                property_title TEXT,
                sqft_living REAL NOT NULL,
                sqft_lot REAL,
                bedrooms INTEGER NOT NULL,
                bathrooms REAL NOT NULL,
                floors REAL,
                waterfront INTEGER DEFAULT 0,
                view INTEGER DEFAULT 0,
                condition INTEGER DEFAULT 3,
                grade INTEGER DEFAULT 7,
                sqft_above REAL,
                sqft_basement REAL DEFAULT 0,
                yr_built INTEGER,
                zipcode TEXT NOT NULL,
                predicted_price REAL NOT NULL,
                lower_bound REAL,
                upper_bound REAL,
                model_name TEXT,
                model_r2 REAL,
                model_mae REAL,
                inputs_json TEXT
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pred_created_at ON predictions(created_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pred_price ON predictions(predicted_price);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pred_zipcode ON predictions(zipcode);")
        conn.commit()
    logger.info(f"Database initialized at {db_path}")

def save_prediction(db_path: str, prediction_data: Dict[str, Any]) -> int:
    """
    Saves a new property price prediction record.
    Returns the new record ID.
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    title = prediction_data.get('property_title') or f"{prediction_data.get('bedrooms', 3)} Bed Home in {prediction_data.get('zipcode', 'King County')}"
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO predictions (
                created_at, property_title, sqft_living, sqft_lot, bedrooms,
                bathrooms, floors, waterfront, view, condition, grade,
                sqft_above, sqft_basement, yr_built, zipcode,
                predicted_price, lower_bound, upper_bound,
                model_name, model_r2, model_mae, inputs_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            now,
            title,
            float(prediction_data.get('sqft_living', 0)),
            float(prediction_data.get('sqft_lot', 0)),
            int(prediction_data.get('bedrooms', 3)),
            float(prediction_data.get('bathrooms', 2.0)),
            float(prediction_data.get('floors', 1.0)),
            int(prediction_data.get('waterfront', 0)),
            int(prediction_data.get('view', 0)),
            int(prediction_data.get('condition', 3)),
            int(prediction_data.get('grade', 7)),
            float(prediction_data.get('sqft_above', prediction_data.get('sqft_living', 0))),
            float(prediction_data.get('sqft_basement', 0)),
            int(prediction_data.get('yr_built', 1990)),
            str(prediction_data.get('zipcode', '98103')),
            float(prediction_data.get('predicted_price', 0)),
            float(prediction_data.get('lower_bound', 0)),
            float(prediction_data.get('upper_bound', 0)),
            str(prediction_data.get('model_name', 'Random Forest Regressor')),
            float(prediction_data.get('model_r2', 0)),
            float(prediction_data.get('model_mae', 0)),
            json.dumps(prediction_data)
        ))
        conn.commit()
        return cursor.lastrowid

def get_predictions(
    db_path: str,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    bedrooms: Optional[int] = None,
    zipcode: Optional[str] = None,
    sort_by: str = 'created_at',
    order: str = 'desc',
    page: int = 1,
    per_page: int = 10
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Retrieves filtered, sorted, paginated predictions.
    Returns (records_list, total_count).
    """
    allowed_sort_fields = {
        'id': 'id',
        'created_at': 'created_at',
        'predicted_price': 'predicted_price',
        'sqft_living': 'sqft_living',
        'bedrooms': 'bedrooms'
    }
    sort_column = allowed_sort_fields.get(sort_by, 'created_at')
    sort_order = 'ASC' if order.lower() == 'asc' else 'DESC'

    query = "SELECT * FROM predictions WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM predictions WHERE 1=1"
    params = []

    if search:
        search_like = f"%{search}%"
        query += " AND (property_title LIKE ? OR zipcode LIKE ?)"
        count_query += " AND (property_title LIKE ? OR zipcode LIKE ?)"
        params.extend([search_like, search_like])

    if min_price is not None:
        query += " AND predicted_price >= ?"
        count_query += " AND predicted_price >= ?"
        params.append(min_price)

    if max_price is not None:
        query += " AND predicted_price <= ?"
        count_query += " AND predicted_price <= ?"
        params.append(max_price)

    if bedrooms is not None:
        query += " AND bedrooms = ?"
        count_query += " AND bedrooms = ?"
        params.append(bedrooms)

    if zipcode:
        query += " AND zipcode = ?"
        count_query += " AND zipcode = ?"
        params.append(str(zipcode))

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]

        # Get paginated records
        offset = max(0, (page - 1) * per_page)
        query += f" ORDER BY {sort_column} {sort_order} LIMIT ? OFFSET ?"
        exec_params = list(params) + [per_page, offset]
        
        cursor.execute(query, exec_params)
        rows = [dict(row) for row in cursor.fetchall()]

    return rows, total_count

def get_prediction_by_id(db_path: str, pred_id: int) -> Optional[Dict[str, Any]]:
    """Fetches a single prediction by ID."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM predictions WHERE id = ?", (pred_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def delete_prediction(db_path: str, pred_id: int) -> bool:
    """Deletes a single prediction by ID."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM predictions WHERE id = ?", (pred_id,))
        conn.commit()
        return cursor.rowcount > 0

def get_history_summary_stats(db_path: str) -> Dict[str, Any]:
    """Calculates summary statistics across all recorded predictions."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total_predictions,
                AVG(predicted_price) as avg_price,
                MAX(predicted_price) as max_price,
                MIN(predicted_price) as min_price,
                AVG(sqft_living) as avg_sqft
            FROM predictions
        """)
        row = cursor.fetchone()
        if not row or row['total_predictions'] == 0:
            return {
                'total_predictions': 0,
                'avg_price': 0,
                'max_price': 0,
                'min_price': 0,
                'avg_sqft': 0
            }
        return {
            'total_predictions': int(row['total_predictions']),
            'avg_price': round(float(row['avg_price'] or 0), 2),
            'max_price': round(float(row['max_price'] or 0), 2),
            'min_price': round(float(row['min_price'] or 0), 2),
            'avg_sqft': round(float(row['avg_sqft'] or 0), 1)
        }

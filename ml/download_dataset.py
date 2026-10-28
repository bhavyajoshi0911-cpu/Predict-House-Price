"""
Utility script to download the official King County House Sales dataset
from reliable public mirrors (e.g., GitHub open-data repositories or OpenML).
"""
import os
import sys
import urllib.request
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MIRRORS = [
    "https://raw.githubusercontent.com/selva86/datasets/master/kc_house_data.csv",
    "https://raw.githubusercontent.com/zackthoutt/datacamp-deep-learning/master/kc_house_data.csv",
]

def download_dataset(destination_path: str = None) -> bool:
    if destination_path is None:
        base_dir = Path(__file__).resolve().parent.parent
        destination_path = str(base_dir / "data" / "kc_house_data.csv")

    dest_file = Path(destination_path)
    dest_file.parent.mkdir(parents=True, exist_ok=True)

    if dest_file.exists() and dest_file.stat().st_size > 100000:
        logger.info(f"Dataset already exists at {destination_path} ({dest_file.stat().st_size:,} bytes).")
        return True

    logger.info("Attempting to download King County Housing dataset...")
    for mirror_url in MIRRORS:
        try:
            logger.info(f"Trying mirror: {mirror_url}")
            urllib.request.urlretrieve(mirror_url, destination_path)
            if dest_file.exists() and dest_file.stat().st_size > 50000:
                logger.info(f"Successfully downloaded to {destination_path} ({dest_file.stat().st_size:,} bytes).")
                return True
        except Exception as e:
            logger.warning(f"Mirror {mirror_url} failed: {e}")

    # Fallback to OpenML if scikit-learn is installed
    try:
        from sklearn.datasets import fetch_openml
        logger.info("Trying OpenML fallback (house_sales)...")
        data = fetch_openml(name="house_sales", version=1, as_frame=True)
        df = data.frame
        df.to_csv(destination_path, index=False)
        logger.info(f"Successfully fetched from OpenML and saved to {destination_path}")
        return True
    except Exception as e:
        logger.warning(f"OpenML fallback failed: {e}")

    logger.error("Could not automatically download dataset from mirrors.")
    return False

if __name__ == "__main__":
    success = download_dataset()
    sys.exit(0 if success else 1)

"""
Analytics service for HomeValue AI.
Computes real dataset market statistics, correlations, distributions,
and aggregates prediction history for dashboards and interactive charts.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path
        self._cached_df = None
        self._cached_mtime = 0

    def _get_dataset(self) -> Optional[pd.DataFrame]:
        """Loads and caches the cleaned dataset based on file modification timestamp."""
        if not os.path.exists(self.dataset_path):
            return None

        current_mtime = os.path.getmtime(self.dataset_path)
        if self._cached_df is None or current_mtime != self._cached_mtime:
            try:
                df = pd.read_csv(self.dataset_path)
                # Quick normalization of columns
                if 'price' in df.columns:
                    df['price'] = pd.to_numeric(df['price'], errors='coerce')
                if 'sqft_living' in df.columns:
                    df['sqft_living'] = pd.to_numeric(df['sqft_living'], errors='coerce')
                if 'bedrooms' in df.columns:
                    df['bedrooms'] = pd.to_numeric(df['bedrooms'], errors='coerce')
                if 'bathrooms' in df.columns:
                    df['bathrooms'] = pd.to_numeric(df['bathrooms'], errors='coerce')
                if 'zipcode' in df.columns:
                    df['zipcode'] = df['zipcode'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
                df = df.dropna(subset=['price'])
                self._cached_df = df
                self._cached_mtime = current_mtime
            except Exception as e:
                logger.error(f"Error loading dataset in AnalyticsService: {e}")
                return None

        return self._cached_df

    def get_market_analytics(
        self,
        zipcode: Optional[str] = None,
        min_bedrooms: Optional[int] = None,
        max_bedrooms: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Computes comprehensive market analytics from the active dataset.
        Supports dynamic filtering.
        """
        df = self._get_dataset()
        if df is None or len(df) == 0:
            return self._empty_analytics_response()

        filtered_df = df.copy()

        # Apply user filters
        if zipcode and str(zipcode).lower() != 'all':
            filtered_df = filtered_df[filtered_df['zipcode'] == str(zipcode)]
        if min_bedrooms is not None:
            filtered_df = filtered_df[filtered_df['bedrooms'] >= min_bedrooms]
        if max_bedrooms is not None:
            filtered_df = filtered_df[filtered_df['bedrooms'] <= max_bedrooms]
        if min_price is not None:
            filtered_df = filtered_df[filtered_df['price'] >= min_price]
        if max_price is not None:
            filtered_df = filtered_df[filtered_df['price'] <= max_price]

        if len(filtered_df) == 0:
            return self._empty_analytics_response(total_properties=0)

        # 1. Summary KPIs
        total_properties = len(filtered_df)
        avg_price = round(float(filtered_df['price'].mean()), 2)
        median_price = round(float(filtered_df['price'].median()), 2)
        min_val = round(float(filtered_df['price'].min()), 2)
        max_val = round(float(filtered_df['price'].max()), 2)
        avg_sqft = round(float(filtered_df['sqft_living'].mean()), 1) if 'sqft_living' in filtered_df else 0
        avg_price_per_sqft = round(avg_price / max(1.0, avg_sqft), 2) if avg_sqft > 0 else 0

        # 2. Price Distribution Histogram (10 bins)
        prices = filtered_df['price'].values
        counts, bin_edges = np.histogram(prices, bins=10)
        price_histogram = []
        for i in range(len(counts)):
            price_histogram.append({
                'label': f"${int(bin_edges[i]/1000)}k–${int(bin_edges[i+1]/1000)}k",
                'min': round(float(bin_edges[i]), 0),
                'max': round(float(bin_edges[i+1]), 0),
                'count': int(counts[i])
            })

        # 3. Average Price by Bedrooms
        bedrooms_data = []
        if 'bedrooms' in filtered_df.columns:
            bed_grp = filtered_df.groupby('bedrooms')['price'].agg(['mean', 'median', 'count']).reset_index()
            bed_grp = bed_grp.sort_values('bedrooms')
            for _, r in bed_grp.iterrows():
                if r['count'] >= 2:
                    bedrooms_data.append({
                        'bedrooms': int(r['bedrooms']),
                        'avg_price': round(float(r['mean']), 2),
                        'median_price': round(float(r['median']), 2),
                        'count': int(r['count'])
                    })

        # 4. Average Price by Bathrooms
        bathrooms_data = []
        if 'bathrooms' in filtered_df.columns:
            bath_grp = filtered_df.groupby('bathrooms')['price'].agg(['mean', 'count']).reset_index()
            bath_grp = bath_grp.sort_values('bathrooms')
            for _, r in bath_grp.iterrows():
                if r['count'] >= 2:
                    bathrooms_data.append({
                        'bathrooms': float(r['bathrooms']),
                        'avg_price': round(float(r['mean']), 2),
                        'count': int(r['count'])
                    })

        # 5. Price vs Living Area Scatter Plot Sample (Max 120 points for chart smoothness)
        scatter_sample = []
        if 'sqft_living' in filtered_df.columns:
            sample_sub = filtered_df.sample(n=min(120, len(filtered_df)), random_state=42)
            for _, r in sample_sub.iterrows():
                scatter_sample.append({
                    'sqft_living': float(r['sqft_living']),
                    'price': float(r['price']),
                    'bedrooms': int(r.get('bedrooms', 3)),
                    'zipcode': str(r.get('zipcode', ''))
                })

        # 6. Price by Location / Top Zipcodes
        zipcode_data = []
        if 'zipcode' in filtered_df.columns:
            zip_grp = filtered_df.groupby('zipcode')['price'].agg(['mean', 'median', 'count']).reset_index()
            zip_grp = zip_grp.sort_values('count', ascending=False).head(12)
            for _, r in zip_grp.iterrows():
                zipcode_data.append({
                    'zipcode': str(r['zipcode']),
                    'avg_price': round(float(r['mean']), 2),
                    'median_price': round(float(r['median']), 2),
                    'count': int(r['count'])
                })

        # 7. Correlation Matrix (Price vs Key Numerical Features)
        correlation_list = []
        numeric_cols = [c for c in ['sqft_living', 'grade', 'sqft_above', 'bathrooms', 'view', 'bedrooms', 'sqft_lot', 'yr_built', 'condition'] if c in filtered_df.columns]
        if numeric_cols:
            corr_series = filtered_df[numeric_cols + ['price']].corr()['price'].drop('price')
            corr_series = corr_series.sort_values(ascending=False)
            for feature, score in corr_series.items():
                correlation_list.append({
                    'feature': feature,
                    'label': feature.replace('_', ' ').title(),
                    'correlation': round(float(score), 4)
                })

        return {
            'total_properties': total_properties,
            'summary': {
                'avg_price': avg_price,
                'median_price': median_price,
                'min_price': min_val,
                'max_price': max_val,
                'avg_sqft': avg_sqft,
                'avg_price_per_sqft': avg_price_per_sqft
            },
            'price_histogram': price_histogram,
            'bedrooms_data': bedrooms_data,
            'bathrooms_data': bathrooms_data,
            'scatter_sample': scatter_sample,
            'zipcode_data': zipcode_data,
            'correlation_data': correlation_list
        }

    def _empty_analytics_response(self, total_properties: int = 0) -> Dict[str, Any]:
        """Provides graceful fallback when dataset has no matching rows."""
        return {
            'total_properties': total_properties,
            'summary': {
                'avg_price': 0,
                'median_price': 0,
                'min_price': 0,
                'max_price': 0,
                'avg_sqft': 0,
                'avg_price_per_sqft': 0
            },
            'price_histogram': [],
            'bedrooms_data': [],
            'bathrooms_data': [],
            'scatter_sample': [],
            'zipcode_data': [],
            'correlation_data': []
        }

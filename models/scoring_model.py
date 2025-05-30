import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import logging # For internal logging

logger = logging.getLogger("scoring_model_logger") # Specific logger
logger.setLevel(logging.INFO) # Or logging.DEBUG for more verbosity
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)


class ProductScorer:
    def __init__(self, weights_config: Dict[str, Any]):
        self.weights_config = weights_config
        self.scoring_weights = weights_config.get('scoring_weights', {})
        self.brand_tier_map = weights_config.get('brand_tier_weights', {})
        self.filters = weights_config.get('filters', {})
        self.default_top_n = weights_config.get('top_n_products', 10)
        logger.debug(f"ProductScorer initialized. Default top_n: {self.default_top_n}, Filters: {self.filters}, Scoring Weights: {self.scoring_weights}")

    def _to_numeric_robust(self, series: pd.Series, default_on_error=0) -> pd.Series:
        if pd.api.types.is_numeric_dtype(series):
            return series.fillna(default_on_error) # Fill NaNs if already numeric
        # Attempt conversion for non-numeric series
        numeric_series = pd.to_numeric(series.astype(str).str.replace(',', '', regex=False), errors='coerce')
        return numeric_series.fillna(default_on_error)


    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        processed_df = df.copy()
        column_map = {
            'Price (USD)': 'price_usd', 'COGS (USD)': 'cogs_usd',
            'Units in Stock': 'units_in_stock', 'Days of Inventory': 'days_of_inventory',
            'Views Last Month': 'views_last_month', 'Volume Sold Last Month': 'volume_sold_last_month',
            'Brand Tier': 'brand_tier', 'Product Name': 'Product Name', 'Brand': 'Brand'
        }
        numeric_internal_cols = ['price_usd', 'cogs_usd', 'units_in_stock', 'days_of_inventory', 'views_last_month', 'volume_sold_last_month']

        for csv_col, internal_col in column_map.items():
            if csv_col in processed_df.columns:
                if internal_col in numeric_internal_cols:
                    processed_df[internal_col] = self._to_numeric_robust(processed_df[csv_col])
                elif internal_col != csv_col:
                     processed_df[internal_col] = processed_df[csv_col]
                # else: string columns like Brand Tier are handled if names match
            else:
                logger.warning(f"Expected CSV column '{csv_col}' not found. Defaulting internal column '{internal_col}'.")
                if internal_col in numeric_internal_cols: processed_df[internal_col] = 0
                else: processed_df[internal_col] = None
        return processed_df

    def apply_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        filtered_df = df.copy()
        min_stock = self.filters.get('min_stock')
        max_days = self.filters.get('max_inventory_days')

        if min_stock is not None and 'units_in_stock' in filtered_df.columns:
            units = self._to_numeric_robust(filtered_df['units_in_stock'])
            filtered_df = filtered_df[units >= min_stock]
        
        if max_days is not None and 'days_of_inventory' in filtered_df.columns:
            days = self._to_numeric_robust(filtered_df['days_of_inventory'], default_on_error=np.inf) # NaN days won't pass filter
            filtered_df = filtered_df[days <= max_days]
            
        logger.debug(f"Applied filters. Original rows: {len(df)}, Filtered rows: {len(filtered_df)}")
        return filtered_df.reset_index(drop=True)

    def calculate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        f_df = df.copy()
        
        price = self._to_numeric_robust(f_df.get('price_usd', pd.Series(dtype='float64')))
        cogs = self._to_numeric_robust(f_df.get('cogs_usd', pd.Series(dtype='float64')))
        profit_margin_array = np.where(price > 0, (price - cogs) / price, 0)
        f_df['profit_margin'] = pd.Series(profit_margin_array, index=f_df.index).fillna(0)

        f_df['sales_velocity'] = self._to_numeric_robust(f_df.get('volume_sold_last_month', pd.Series(dtype='float64')))
        f_df['engagement'] = self._to_numeric_robust(f_df.get('views_last_month', pd.Series(dtype='float64')))
        
        if 'brand_tier' in f_df.columns and self.brand_tier_map:
            f_df['brand_tier_weight'] = f_df['brand_tier'].map(self.brand_tier_map).fillna(0)
        else: f_df['brand_tier_weight'] = 0
        return f_df

    def normalize_features(self, df: pd.DataFrame) -> pd.DataFrame:
        norm_df = df.copy()
        features_to_normalize = ['sales_velocity', 'profit_margin', 'engagement', 'brand_tier_weight']
        
        for feature in features_to_normalize:
            if feature in norm_df.columns and not norm_df[feature].empty:
                series = self._to_numeric_robust(norm_df[feature])
                min_v, max_v = series.min(), series.max()
                if max_v > min_v: norm_df[f'norm_{feature}'] = (series - min_v) / (max_v - min_v)
                elif max_v == min_v and max_v != 0: norm_df[f'norm_{feature}'] = 1.0
                else: norm_df[f'norm_{feature}'] = 0.0
            else: norm_df[f'norm_{feature}'] = 0.0
        return norm_df

    def calculate_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        score_df = df.copy()
        score_df['score'] = 0.0
        for component, weight in self.scoring_weights.items():
            norm_col = f'norm_{"brand_tier_weight" if component == "brand_tier" else component}'
            if norm_col in score_df.columns:
                values = self._to_numeric_robust(score_df[norm_col])
                score_df['score'] += weight * values
            else: logger.warning(f"Normalized component '{norm_col}' for scoring (weight='{component}') not found.")
        return score_df

    def rank_products(self, df: pd.DataFrame, top_n: int) -> pd.DataFrame:
        df['score'] = self._to_numeric_robust(df.get('score', pd.Series(dtype='float64')))
        ranked = df.sort_values('score', ascending=False).reset_index(drop=True)
        ranked['rank'] = range(1, len(ranked) + 1)
        return ranked.head(top_n)

    def process(self, df: pd.DataFrame, top_n: Optional[int] = None) -> pd.DataFrame:
        effective_top_n = top_n if top_n is not None else self.default_top_n
        logger.info(f"Scorer processing {len(df)} products for top_n={effective_top_n}...")
        
        out_cols = ['Product Name', 'Brand', 'Price (USD)', 'score', 'rank']
        if df.empty:
            logger.info("Scorer: Input DataFrame is empty.")
            return pd.DataFrame(columns=out_cols)

        x = self.preprocess_data(df)
        x = self.calculate_features(x)
        x = self.apply_filters(x)
        
        if x.empty:
            logger.info("Scorer: DataFrame is empty after filtering.")
            return pd.DataFrame(columns=out_cols)

        x = self.normalize_features(x)
        x = self.calculate_scores(x)
        ranked = self.rank_products(x, top_n=effective_top_n)
        
        # Prepare final output with specified column names
        final_output_df = pd.DataFrame()
        # Map internal names back to CSV-like names for processed output consistency
        final_output_df['Product Name'] = ranked.get('Product Name', pd.Series(dtype=str))
        final_output_df['Brand'] = ranked.get('Brand', pd.Series(dtype=str))
        final_output_df['Price (USD)'] = ranked.get('price_usd', pd.Series(dtype=float)) # from internal 'price_usd'
        final_output_df['score'] = ranked.get('score', pd.Series(dtype=float))
        final_output_df['rank'] = ranked.get('rank', pd.Series(dtype=int))
        
        logger.info(f"Scorer processed {len(ranked)} products.")
        return final_output_df[out_cols] # Ensure order and presence of columns
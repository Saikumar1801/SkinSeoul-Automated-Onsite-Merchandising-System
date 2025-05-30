import pandas as pd
from typing import Optional
from pathlib import Path
from models.scoring_model import ProductScorer
from config.settings import settings
import logging

logger = logging.getLogger("data_processor_logger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)

class DataProcessor:
    def __init__(self):
        self.scorer = ProductScorer(settings.WEIGHTS)
        logger.debug("DataProcessor initialized.")
        
    def load_data(self, file_path: Optional[Path] = None) -> pd.DataFrame:
        f_path = file_path if file_path is not None else settings.RAW_DATA_PATH
        if not f_path.exists():
            logger.error(f"Raw data file not found: {f_path}")
            raise FileNotFoundError(f"Raw data file not found: {f_path}")
        try:
            logger.info(f"Loading data from {f_path}...")
            df = pd.read_csv(f_path)
            logger.info(f"Successfully loaded {len(df)} rows from {f_path}.")
            return df
        except Exception as e:
            logger.error(f"Error loading data from {f_path}: {e}", exc_info=True)
            return pd.DataFrame() 
    
    def process_and_score_data(self, df: pd.DataFrame, top_n: Optional[int] = None) -> pd.DataFrame:
        effective_top_n = top_n if top_n is not None else settings.WEIGHTS.get('top_n_products', 10)
        logger.info(f"DataProcessor: Processing and scoring data for top_n={effective_top_n} products...")
        return self.scorer.process(df, top_n=effective_top_n)
    
    def save_processed_data(self, df: pd.DataFrame, file_path: Optional[Path] = None) -> None:
        f_path = file_path if file_path is not None else settings.PROCESSED_DATA_PATH
        try:
            f_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(f_path, index=False)
            logger.info(f"Processed data saved to {f_path} ({len(df)} rows).")
        except Exception as e:
            logger.error(f"Error saving processed data to {f_path}: {e}", exc_info=True)
        
    def run_full_pipeline(self, top_n: Optional[int] = None) -> pd.DataFrame:
        logger.info("--- Starting Data Processing Full Pipeline ---")
        raw_df = self.load_data()
        if raw_df.empty:
            logger.warning("Raw data is empty. Aborting pipeline.")
            logger.info("--- Data Processing Full Pipeline Finished (Aborted due to empty raw data) ---")
            return pd.DataFrame()
            
        processed_df = self.process_and_score_data(raw_df, top_n=top_n)
        if not processed_df.empty:
            self.save_processed_data(processed_df)
        else:
            logger.warning("No products after processing and scoring. Processed data file will not be created/updated.")
        
        logger.info("--- Data Processing Full Pipeline Finished ---")
        return processed_df
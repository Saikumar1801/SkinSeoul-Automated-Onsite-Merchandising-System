from prefect import flow, task
import pandas as pd
from typing import Optional
import logging # Using Prefect's built-in logging which is good

# Adjust import paths based on project structure
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from pipelines.data_processing import DataProcessor
from config.settings import settings


@task(name="Load Raw Product Data", log_prints=True)
def load_raw_data_task() -> pd.DataFrame:
    processor = DataProcessor()
    # Prefect's logger is automatically available in tasks when log_prints=True
    prefect_logger = logging.getLogger("prefect.task_runs") 
    prefect_logger.info("Task (Load Raw Product Data): Starting...")
    df = processor.load_data()
    if df.empty:
        prefect_logger.warning("Task (Load Raw Product Data): Raw data loading resulted in an empty DataFrame.")
    else:
        prefect_logger.info(f"Task (Load Raw Product Data): Successfully loaded {len(df)} rows of raw data.")
    return df

@task(name="Process and Score Products", log_prints=True)
def process_and_score_data_task(df: pd.DataFrame, top_n: Optional[int] = None) -> pd.DataFrame:
    processor = DataProcessor()
    prefect_logger = logging.getLogger("prefect.task_runs")
    if df.empty:
        prefect_logger.warning("Task (Process and Score Products): Input DataFrame for processing is empty. Skipping.")
        return pd.DataFrame()
    
    effective_top_n = top_n if top_n is not None else settings.WEIGHTS.get('top_n_products', 10)
    prefect_logger.info(f"Task (Process and Score Products): Processing {len(df)} products for top_n={effective_top_n}...")
    
    processed_df = processor.process_and_score_data(df, top_n=effective_top_n)
    prefect_logger.info(f"Task (Process and Score Products): Processing complete. {len(processed_df)} products ranked.")
    return processed_df

@task(name="Save Ranked Products", log_prints=True)
def save_ranked_data_task(df: pd.DataFrame) -> None:
    processor = DataProcessor()
    prefect_logger = logging.getLogger("prefect.task_runs")
    if df.empty:
        prefect_logger.warning("Task (Save Ranked Products): DataFrame for saving is empty. Skipping save.")
        return
    prefect_logger.info(f"Task (Save Ranked Products): Saving {len(df)} ranked products...")
    processor.save_processed_data(df)


@flow(name="Product Ranking ETL Flow", log_prints=True)
def product_ranking_etl_flow(run_name: str = "default_run"):
    flow_logger = logging.getLogger("prefect.flow_runs") # Get Prefect's flow logger
    flow_logger.info(f"=== Starting Product Ranking ETL Flow: {run_name} ===")
    
    raw_data_df = load_raw_data_task()
    
    if raw_data_df is not None and not raw_data_df.empty:
        ranked_products_df = process_and_score_data_task(raw_data_df)
        if ranked_products_df is not None and not ranked_products_df.empty:
            save_ranked_data_task(ranked_products_df)
        else:
            flow_logger.warning("Flow: No products were ranked after processing. Output file will not be updated/created.")
    else:
        flow_logger.error("Flow: Raw data was empty or failed to load. ETL flow cannot proceed further.")
    
    flow_logger.info(f"=== Product Ranking ETL Flow: {run_name} completed. ===")

if __name__ == "__main__":
    from datetime import datetime
    test_run_name = f"manual_test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    product_ranking_etl_flow(run_name=test_run_name)
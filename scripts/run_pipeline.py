#!/usr/bin/env python3
import logging
from datetime import datetime

# Adjust import paths based on project structure
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from pipelines.ranking_pipeline import product_ranking_etl_flow

# Configure basic logging for this script
# Note: Prefect flows and tasks have their own logging configured via log_prints or custom loggers
script_logger = logging.getLogger("run_pipeline_script")
script_logger.setLevel(logging.INFO)
# Avoid adding duplicate handlers if this script is imported elsewhere or run multiple times in same session
if not script_logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    script_logger.addHandler(handler)


if __name__ == "__main__":
    script_logger.info("Starting product ranking ETL pipeline script...")
    
    current_time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    flow_run_name = f"product_ranking_run_{current_time_str}"
    
    try:
        product_ranking_etl_flow(run_name=flow_run_name)
        script_logger.info(f"Product ranking ETL pipeline script finished successfully for run: {flow_run_name}.")
    except Exception as e:
        script_logger.error(f"An error occurred during the pipeline execution for run {flow_run_name}: {e}", exc_info=True)
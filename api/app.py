from fastapi import FastAPI, HTTPException
from typing import List, Optional
import pandas as pd
from pathlib import Path
import logging
import sys

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from .schemas import ProductRankedResponse, ProductDetailResponse
from models.scoring_model import ProductScorer
from config.settings import settings
from pipelines.data_processing import DataProcessor

logger = logging.getLogger("api_logger")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

app = FastAPI(
    title="SkinSeoul Merchandising API",
    description="API for automated product ranking and merchandising for SkinSeoul.",
    version="1.0.4" # Incremented version
)

scorer: Optional[ProductScorer] = None
data_processor: Optional[DataProcessor] = None

@app.on_event("startup")
async def load_resources():
    global scorer, data_processor
    try:
        logger.info("API Startup: Loading resources...")
        scorer = ProductScorer(settings.WEIGHTS)
        data_processor = DataProcessor()
        if not settings.RAW_DATA_PATH.exists():
            logger.critical(f"Raw data file {settings.RAW_DATA_PATH} not found.")
        logger.info("API Startup: Resources loaded successfully.")
    except Exception as e:
        logger.critical(f"Error loading resources on startup: {e}", exc_info=True)

@app.get("/ranked-products/", response_model=List[ProductRankedResponse])
async def get_ranked_products(top_n: int = 10):
    if not scorer or not data_processor:
        logger.error("API Error: Scoring service not available.")
        raise HTTPException(status_code=503, detail="Scoring service not available.")

    try:
        ranked_df: Optional[pd.DataFrame] = None
        if settings.PROCESSED_DATA_PATH.exists():
            logger.info(f"API: Loading pre-processed data from {settings.PROCESSED_DATA_PATH} for top_n={top_n}")
            ranked_df = pd.read_csv(settings.PROCESSED_DATA_PATH)
            if 'rank' not in ranked_df.columns:
                logger.warning(f"Processed data missing 'rank'. Re-creating.")
                ranked_df['rank'] = range(1, len(ranked_df) + 1)
            if top_n < len(ranked_df):
                 ranked_df = ranked_df.head(top_n)
        else:
            logger.warning(f"API: Processed data not found. Processing raw data on-the-fly...")
            if not settings.RAW_DATA_PATH.exists():
                 logger.error(f"API Error: Raw data file {settings.RAW_DATA_PATH} not found for on-the-fly processing.")
                 raise HTTPException(status_code=404, detail=f"Raw data file {settings.RAW_DATA_PATH} not found.")
            raw_df = data_processor.load_data()
            if raw_df.empty:
                logger.info("API: Raw data empty. Returning no ranked products.")
                return []
            ranked_df = scorer.process(raw_df, top_n=top_n)

        if ranked_df is None or ranked_df.empty:
            logger.info("API: No products available after processing/loading.")
            return []

        # --- MODIFICATION START ---
        # Explicitly create Pydantic model instances
        # This ensures that aliases are correctly used during instantiation.
        product_responses: List[ProductRankedResponse] = []
        for record in ranked_df.to_dict(orient="records"):
            try:
                # Pydantic V2 uses model_validate for dicts
                product_responses.append(ProductRankedResponse.model_validate(record))
            except Exception as e_val: # Catch Pydantic validation errors per record for debugging
                logger.error(f"Validation error for record {record}: {e_val}")
                # Decide how to handle: skip record, or raise overall error
                # For now, let's see if any individual record fails
        
        if not product_responses and not ranked_df.empty: # If all records failed validation
            logger.error("All records failed Pydantic validation for ProductRankedResponse.")
            raise HTTPException(status_code=500, detail="Internal server error during data validation.")
            
        return product_responses
        # --- MODIFICATION END ---

    except FileNotFoundError as e:
        logger.error(f"API Error in /ranked-products: FileNotFoundError - {e}", exc_info=True)
        raise HTTPException(status_code=404, detail=f"A required data file was not found: {e}.")
    except Exception as e:
        logger.error(f"API Error in /ranked-products: {type(e).__name__} - {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/product-details/{product_name}", response_model=ProductDetailResponse)
async def get_product_details(product_name: str):
    if not data_processor:
        logger.error("API Error: Data service not available.")
        raise HTTPException(status_code=503, detail="Data service not available.")
    try:
        df = data_processor.load_data(settings.RAW_DATA_PATH)
        if df.empty:
             logger.warning(f"API Warning: Raw data file loaded as empty.")
             raise HTTPException(status_code=404, detail=f"Raw data file empty or not loaded.")

        product_data_df = df[df['Product Name'] == product_name]

        if product_data_df.empty:
            logger.info(f"API: Product '{product_name}' not found.")
            raise HTTPException(status_code=404, detail=f"Product '{product_name}' not found.")

        product_dict = product_data_df.iloc[0].to_dict()
        # For single dicts, Pydantic V2 usually handles **product_dict or model_validate(product_dict)
        try:
            return ProductDetailResponse.model_validate(product_dict)
        except Exception as e_val:
            logger.error(f"Validation error for product details {product_dict}: {e_val}")
            raise HTTPException(status_code=500, detail="Internal server error during product detail validation.")


    except FileNotFoundError:
        logger.error(f"API Error: Raw data file not found.", exc_info=True)
        raise HTTPException(status_code=404, detail=f"Raw data file not found.")
    except Exception as e:
        logger.error(f"API Error in /product-details for '{product_name}': {type(e).__name__} - {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting API server on {settings.API_HOST}:{settings.API_PORT}...")
    uvicorn.run("api.app:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
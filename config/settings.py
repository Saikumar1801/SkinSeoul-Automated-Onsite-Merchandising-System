import os
from pathlib import Path
from dotenv import load_dotenv
import yaml
import logging # For logging issues during settings load

logger = logging.getLogger("settings_loader") # Specific logger for settings
logger.setLevel(logging.INFO)
handler = logging.StreamHandler() # Default to stdout
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
if not logger.handlers: # Avoid adding multiple handlers if reloaded
    logger.addHandler(handler)


BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=dotenv_path)

class Settings:
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    CONFIG_DIR: Path = BASE_DIR / "config"

    RAW_DATA_FILENAME: str = "Mock_Skincare_Dataset.csv"
    PROCESSED_DATA_FILENAME: str = "ranked_products.csv"
    
    RAW_DATA_PATH: Path = RAW_DATA_DIR / RAW_DATA_FILENAME
    PROCESSED_DATA_PATH: Path = PROCESSED_DATA_DIR / PROCESSED_DATA_FILENAME
    
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", 8000))
    
    WEIGHTS_FILE_PATH: Path = CONFIG_DIR / "weights.yaml"
    try:
        with open(WEIGHTS_FILE_PATH, 'r') as f:
            WEIGHTS = yaml.safe_load(f)
        logger.info(f"Successfully loaded weights from {WEIGHTS_FILE_PATH}")
    except FileNotFoundError:
        logger.critical(f"Weights file not found at {WEIGHTS_FILE_PATH}. Using default empty weights. Scoring will be significantly affected.")
        WEIGHTS = {'scoring_weights': {}, 'brand_tier_weights': {}, 'filters': {}, 'top_n_products': 10}
    except yaml.YAMLError as e:
        logger.critical(f"Error parsing weights file {WEIGHTS_FILE_PATH}: {e}. Using default empty weights. Scoring will be significantly affected.")
        WEIGHTS = {'scoring_weights': {}, 'brand_tier_weights': {}, 'filters': {}, 'top_n_products': 10}

settings = Settings()
try:
    settings.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
except Exception as e:
    logger.error(f"Could not create processed data directory {settings.PROCESSED_DATA_DIR}: {e}")
# SkinSeoul Automated Onsite Merchandising System

**Version:** 1.0.2
**Date:** October 26, 2023
**Project:** AI Agent Innovation Internship

## 1. Overview

This project implements an automated merchandising system designed for SKINSEOUL, an e-commerce platform specializing in K-Beauty products. The system dynamically ranks products based on a configurable set of business metrics, aiming to enhance product discovery, boost conversion rates, and reduce manual curation efforts.

The system features:
-   **Data-Driven Product Scoring:** Products from a mock dataset (`Mock_Skincare_Dataset.csv`) are scored based on factors like sales velocity, profit margin, brand tier, and user engagement.
-   **Configurable Logic:** Scoring weights and filtering rules are managed externally via a YAML file (`config/weights.yaml`), allowing for easy business adjustments.
-   **Automated ETL Pipeline:** A data processing pipeline, orchestrated by [Prefect](https://www.prefect.io/), handles data ingestion, cleaning, feature engineering, scoring, and ranking.
-   **RESTful API:** A [FastAPI](https://fastapi.tiangolo.com/) application exposes endpoints to serve the ranked product data and individual product details, ready for frontend integration.
-   **Modular and Testable Codebase:** The project is structured for maintainability, with components for configuration, data handling, modeling, pipelines, and API services. Basic unit tests are included.

## 2. Project Structure

skinseoul_merchandising/
├── .env.example # Example environment variables for API configuration
├── .gitignore # Specifies intentionally untracked files that Git should ignore
├── README.md # This file: Project overview, setup, and usage instructions
├── requirements.txt # Python dependencies for the project
├── api/ # Contains the FastAPI application
│ ├── init.py
│ ├── app.py # Main FastAPI application logic and endpoints
│ └── schemas.py # (Optional) Pydantic schemas if separated from app.py
├── config/ # Configuration files
│ ├── init.py
│ ├── settings.py # Project settings, paths, and loads weights.yaml
│ └── weights.yaml # Configurable scoring weights and business rule filters
├── data/ # Data storage
│ ├── raw/
│ │ └── Mock_Skincare_Dataset.csv # Input raw product data
│ └── processed/ # Output directory for ranked_products.csv (auto-created)
├── models/ # Core business logic and algorithms
│ ├── init.py
│ └── scoring_model.py # ProductScorer class for ranking logic
├── pipelines/ # Data processing and ETL workflows
│ ├── init.py
│ ├── data_processing.py # DataProcessor class for data loading and transformation
│ └── ranking_pipeline.py # Prefect flow definition (product_ranking_etl_flow)
├── scripts/ # Utility and execution scripts
│ ├── run_pipeline.py # Script to execute the Prefect product ranking pipeline
│ └── refresh_data.py # (Placeholder) Script for future data refresh mechanisms
└── tests/ # Unit and integration tests
├── init.py
├── test_data_processing.py # Tests for data_processing.py
└── test_scoring.py # Tests for scoring_model.py


## 3. Technical Stack

-   **Python:** Core programming language (version 3.10+ recommended, developed with 3.13 in mind).
-   **Pandas & NumPy:** For data manipulation and numerical operations.
-   **Prefect:** For workflow orchestration and automation of the data pipeline.
-   **FastAPI:** For building the high-performance RESTful API.
-   **Uvicorn:** ASGI server to run the FastAPI application.
-   **PyYAML:** For parsing the `weights.yaml` configuration file.
-   **python-dotenv:** For managing environment variables.
-   **Pytest:** For running unit tests.

## 4. Setup and Installation

### Prerequisites

-   Python (3.10 or newer recommended)
-   `pip` (Python package installer)
-   Git (for cloning the repository)

### Steps

1.  **Clone the Repository:**
    ```bash
    git clone SkinSeoul-Automated-Onsite-Merchandising-System.git
    cd SkinSeoul-Automated-Onsite-Merchandising-System
    ```

2.  **Create and Activate a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # On Windows:
    venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Variables (Optional):**
    The API host and port can be configured via a `.env` file in the project root. Copy the example and modify if needed:
    ```bash
    cp .env.example .env
    ```
    Edit `.env` to set `API_HOST` or `API_PORT` if you don't want the defaults (`0.0.0.0:8000`).

5.  **Verify Mock Dataset:**
    Ensure `data/raw/Mock_Skincare_Dataset.csv` exists and contains the product data.

## 5. Usage

### 5.1. Running the Data Processing Pipeline

This pipeline processes the raw product data, applies the scoring logic, and generates a ranked list of products.

Execute the script:
```bash
python scripts/run_pipeline.py
```

Output: This will create/update data/processed/ranked_products.csv.
Logs: The script and Prefect will output logs to the console, indicating the progress and status of each task in the flow. You might also see a temporary Prefect UI server URL if you are running Prefect locally for the first time or without a dedicated server.

### 5.2. Starting the API Server
The API server exposes endpoints to access the ranked products and product details.
Start the Uvicorn server:

```
uvicorn api.app:app --reload
```

--reload: Enables auto-reloading when code changes (useful for development).
By default, the API will be available at http://localhost:8000.

### 5.3. API Endpoints

Once the server is running, you can access the following endpoints using a browser or an API client (like Postman or curl):

Get Top Ranked Products:

URL: GET http://localhost:8000/ranked-products/

Query Parameter (Optional): top_n (integer) to specify the number of top products to return.

Example: http://localhost:8000/ranked-products/?top_n=5

Response: A JSON array of ranked products.

Get Product Details:

URL: GET http://localhost:8000/product-details/{product_name}

Replace {product_name} with the URL-encoded name of a product from the dataset.

Example: http://localhost:8000/product-details/Pure%20Collagen%20Cleanser

Response: A JSON object with details for the specified product.

API Documentation (Interactive):

Swagger UI: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc

## 6. Configuration (config/weights.yaml)
The core ranking logic is highly configurable through config/weights.yaml. This allows business stakeholders or data analysts to fine-tune the merchandising strategy without modifying Python code.

Key sections:

scoring_weights: Defines the relative importance of different factors (e.g., sales_velocity, profit_margin).

brand_tier_weights: Maps brand tiers (e.g., 'A', 'B', 'C') to numerical weights.

filters: Sets criteria to exclude products before scoring (e.g., min_stock, max_inventory_days).

top_n_products: Default number of products the pipeline aims to output.

After modifying weights.yaml, re-run the data processing pipeline (python scripts/run_pipeline.py) for the changes to take effect in data/processed/ranked_products.csv and subsequently in the API (if it reads the processed file).

## 7. Running Tests
Unit tests are provided to verify the core functionality of the scoring model and data processing components.

To run tests:

```
pytest
```
Ensure you are in the project root directory (skinseoul_merchandising) where pytest.ini (if any) or test discovery will work.

## 8. Future Enhancements & Considerations

Real-time Data Ingestion: Integrate with actual e-commerce databases or event streams for more up-to-date product information.

Advanced Scoring Models: Incorporate machine learning models for predictive ranking, or more sophisticated heuristics.

Personalization: Extend the system to provide personalized rankings based on user behavior and preferences.

Touchpoint-Specific Logic: Develop distinct ranking strategies and configurations for different website merchandising areas (e.g., homepage, category pages, cross-sell widgets).

A/B Testing Framework: Implement capabilities to test different ranking algorithms and measure their impact on business KPIs.

Manual Override Interface: Create a mechanism or UI for business users to manually pin or boost specific products.

Full CI/CD Pipeline: Set up continuous integration and deployment for automated testing and releases.

Prefect Cloud/Server Deployment: For robust scheduling, monitoring, and management of the ETL pipeline in a production environment.

## 9. Troubleshooting

ImportError: Ensure your virtual environment is activated and all dependencies in requirements.txt are installed. Check that your Python path includes the project root, especially when running scripts. The provided scripts attempt to manage this.

FileNotFoundError for Mock_Skincare_Dataset.csv or weights.yaml: Verify these files exist in the correct locations (data/raw/ and config/ respectively).

Prefect Issues: Consult the Prefect Documentation. Sometimes, cleaning up old Prefect SQLite databases (~/.prefect/prefect.db or similar, depending on version and OS) can resolve local issues.

API Not Responding: Check that Uvicorn started correctly and there are no port conflicts. Review console logs from Uvicorn and the FastAPI application for errors.

## 10. Contribution
This project was developed as part of the AI Agent Innovation Internship. For future contributions or modifications, please follow standard Git practices (feature branches, pull requests, code reviews). Ensure new code is well-documented and accompanied by relevant tests.

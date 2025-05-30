import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adjust import paths
import sys
project_root_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root_path))

from pipelines.data_processing import DataProcessor
from config.settings import settings # For accessing paths, weights for scorer
from models.scoring_model import ProductScorer # To potentially mock or use

@pytest.fixture
def data_processor_instance():
    # This will initialize DataProcessor, which in turn initializes ProductScorer with actual weights
    return DataProcessor()

@pytest.fixture
def sample_raw_csv_content():
    # Match your actual CSV columns
    return (
        "Product Name,Brand,Brand Tier,Price (USD),COGS (USD),Days of Inventory,Units in Stock,Views Last Month,Volume Sold Last Month\n"
        "Test Product 1,BrandA,A,100,50,30,100,1000,100\n"
        "Test Product 2,BrandB,B,80,60,60,50,500,50\n"
        "Filtered Product LowStock,BrandC,C,50,25,20,5,200,20\n" # Will be filtered by min_stock in default weights
        "Filtered Product OldStock,BrandD,A,120,60,100,30,300,30\n" # Will be filtered by max_inventory_days in default weights
    )

@pytest.fixture
def temp_raw_data_file(tmp_path, sample_raw_csv_content):
    # Create a temporary raw CSV file for testing load_data
    raw_file = tmp_path / "temp_raw_data.csv"
    raw_file.write_text(sample_raw_csv_content)
    return raw_file

def test_load_data_success(data_processor_instance, temp_raw_data_file):
    df = data_processor_instance.load_data(file_path=temp_raw_data_file)
    assert not df.empty
    assert len(df) == 4 # 4 products in sample_raw_csv_content
    assert "Product Name" in df.columns
    assert df.iloc[0]["Product Name"] == "Test Product 1"

def test_load_data_file_not_found(data_processor_instance, tmp_path):
    non_existent_file = tmp_path / "i_do_not_exist.csv"
    with pytest.raises(FileNotFoundError):
        data_processor_instance.load_data(file_path=non_existent_file)

def test_process_and_score_data_integration(data_processor_instance, temp_raw_data_file):
    """
    Tests the integration of DataProcessor with ProductScorer using actual scoring.
    Relies on the correctness of ProductScorer and weights.yaml.
    """
    raw_df = pd.read_csv(temp_raw_data_file)
    
    # Assuming default weights: min_stock=10, max_inventory_days=90
    # "Filtered Product LowStock" (stock=5) should be out.
    # "Filtered Product OldStock" (days=100) should be out.
    # Expecting 2 products to remain and be scored.
    
    processed_df = data_processor_instance.process_and_score_data(raw_df, top_n=5) # Ask for more than expected
    
    assert not processed_df.empty
    assert "score" in processed_df.columns
    assert "rank" in processed_df.columns
    assert len(processed_df) == 2 # Only "Test Product 1" and "Test Product 2" should pass filters
    
    # Check if the remaining products are the correct ones
    remaining_products = processed_df["Product Name"].tolist()
    assert "Test Product 1" in remaining_products
    assert "Test Product 2" in remaining_products
    assert "Filtered Product LowStock" not in remaining_products
    assert "Filtered Product OldStock" not in remaining_products

    if len(processed_df) > 1:
        assert processed_df.iloc[0]["score"] >= processed_df.iloc[1]["score"] # Check ranking order

def test_save_processed_data(data_processor_instance, tmp_path):
    df_to_save = pd.DataFrame({
        'Product Name': ['Saved Product 1'],
        'Brand': ['BrandSave'],
        'Price (USD)': [99.99],
        'score': [0.95],
        'rank': [1]
    })
    output_file = tmp_path / "processed_test_output.csv"
    
    data_processor_instance.save_processed_data(df_to_save, file_path=output_file)
    
    assert output_file.exists()
    saved_df = pd.read_csv(output_file)
    assert len(saved_df) == 1
    pd.testing.assert_frame_equal(saved_df, df_to_save, check_dtype=False) # check_dtype=False for flexibility

@patch('pipelines.data_processing.DataProcessor.load_data')
@patch('pipelines.data_processing.DataProcessor.process_and_score_data')
@patch('pipelines.data_processing.DataProcessor.save_processed_data')
def test_run_full_pipeline_mocked(mock_save, mock_process_score, mock_load, data_processor_instance):
    """Tests the full pipeline execution flow with mocked sub-methods."""
    sample_df = pd.DataFrame({'Product Name': ['Mocked Raw Product']})
    mock_load.return_value = sample_df
    
    mock_processed_df = pd.DataFrame({'Product Name': ['Mocked Processed Product'], 'score': [0.88], 'rank': [1]})
    mock_process_score.return_value = mock_processed_df
    
    result_df = data_processor_instance.run_full_pipeline(top_n=1)
    
    mock_load.assert_called_once()
    mock_process_score.assert_called_with(sample_df, top_n=1)
    mock_save.assert_called_with(mock_processed_df)
    pd.testing.assert_frame_equal(result_df, mock_processed_df)

def test_run_full_pipeline_empty_raw_data(data_processor_instance):
    """Test full pipeline when raw data is empty by mocking load_data."""
    with patch.object(data_processor_instance, 'load_data', return_value=pd.DataFrame()) as mock_load:
        # Ensure process_and_score_data and save_processed_data are not called
        with patch.object(data_processor_instance, 'process_and_score_data') as mock_process, \
             patch.object(data_processor_instance, 'save_processed_data') as mock_save:
            
            result_df = data_processor_instance.run_full_pipeline()
            
            assert result_df.empty
            mock_load.assert_called_once()
            mock_process.assert_not_called()
            mock_save.assert_not_called()
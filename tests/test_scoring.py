import pytest
import pandas as pd
from models.scoring_model import ProductScorer
from config import settings

@pytest.fixture
def sample_data():
    return pd.DataFrame({
        'Product Name': ['Product A', 'Product B', 'Product C'],
        'Brand': ['Brand X', 'Brand Y', 'Brand Z'],
        'Brand Tier': ['A', 'B', 'C'],
        'Price (USD)': [100, 50, 30],
        'COGS (USD)': [40, 25, 15],
        'Days of Inventory': [30, 45, 60],
        'Units in Stock': [50, 20, 5],
        'Views Last Month': [1000, 500, 200],
        'Volume Sold Last Month': [100, 50, 10]
    })

def test_product_scorer(sample_data):
    scorer = ProductScorer(settings.WEIGHTS)
    processed_df = scorer.process(sample_data)
    
    # Check filtering
    assert len(processed_df) == 2  # Should filter out Product C (stock < 10)
    
    # Check scoring
    assert all(col in processed_df.columns for col in ['score', 'profit_margin'])
    assert processed_df['score'].between(0, 1).all()
    
    # Check ranking
    assert processed_df['score'].iloc[0] >= processed_df['score'].iloc[1]
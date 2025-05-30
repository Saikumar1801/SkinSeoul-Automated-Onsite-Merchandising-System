from pydantic import BaseModel, Field, model_validator
from typing import List, Optional

# --- Response Models (as used by GET endpoints) ---

class ProductRankedResponse(BaseModel):
    # Field definitions now include aliases to match the DataFrame column names
    product_name: str = Field(
        ...,
        alias="Product Name",
        example="Pure Collagen Cleanser",
        description="The name of the product."
    )
    brand: str = Field(
        ...,
        alias="Brand",
        example="COSRX",
        description="The brand of the product."
    )
    price: float = Field(
        ...,
        alias="Price (USD)",
        example=36.22,
        description="The retail price of the product in USD."
    )
    score: float = Field(
        ...,
        example=0.85,
        description="The calculated merchandising score for the product."
    )
    rank: int = Field(
        ...,
        example=1,
        description="The rank of the product based on its score."
    )

    # Pydantic V2 model configuration
    model_config = {
        "populate_by_name": True,  # Replaces allow_population_by_field_name=True
                                   # This allows using aliases for population
        "from_attributes": True,   # Replaces orm_mode=True
        "str_strip_whitespace": True # Replaces anystr_strip_whitespace=True
    }


class ProductDetailResponse(BaseModel):
    product_name: str = Field(..., alias="Product Name")
    brand: str = Field(..., alias="Brand")
    brand_tier: str = Field(..., alias="Brand Tier")
    price_usd: float = Field(..., alias="Price (USD)")
    cogs_usd: float = Field(..., alias="COGS (USD)")
    units_in_stock: int = Field(..., alias="Units in Stock")
    days_of_inventory: int = Field(..., alias="Days of Inventory")
    views_last_month: int = Field(..., alias="Views Last Month")
    volume_sold_last_month: int = Field(..., alias="Volume Sold Last Month")

    # Pydantic V2 model configuration
    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
        "str_strip_whitespace": True
    }

# --- Request Models (Example for future POST/PUT, not currently used by GET endpoints) ---
#
# class ProductCreateRequest(BaseModel):
#     product_name: str = Field(..., min_length=3, max_length=100)
#     brand: str = Field(..., min_length=2, max_length=50)
#     # ... other fields
#
#     model_config = {
#         "str_strip_whitespace": True
#     }
#
# class ProductUpdateRequest(BaseModel):
#     product_name: Optional[str] = Field(None, min_length=3, max_length=100)
#     # ... other fields
#
#     model_config = {
#         "str_strip_whitespace": True
#     }
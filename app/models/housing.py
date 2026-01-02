from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PriceRange(BaseModel):
    min: int = Field(..., description="Minimum estimated price in USD")
    max: int = Field(..., description="Maximum estimated price in USD")
    median: int = Field(..., description="Median estimated price in USD")


class HousingPricingResponse(BaseModel):
    neighborhood: str
    city: str
    state: str
    price_range: PriceRange
    confidence_level: ConfidenceLevel
    data_sources: List[str] = Field(
        ...,
        min_length=1,
        description="List of data sources or estimation methods used"
    )
    summary: str = Field(
        ...,
        description="Brief explanation of the pricing estimate"
    )
    caveats: List[str] = Field(
        default_factory=list,
        description="Important disclaimers or limitations"
    )

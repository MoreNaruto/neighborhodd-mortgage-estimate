import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.models.housing import HousingPricingResponse, PriceRange, ConfidenceLevel


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def sample_housing_response():
    return HousingPricingResponse(
        neighborhood="Downtown",
        city="Austin",
        state="TX",
        price_range=PriceRange(
            min=350000,
            max=850000,
            median=550000
        ),
        confidence_level=ConfidenceLevel.MEDIUM,
        data_sources=[
            "General knowledge of Austin housing market trends",
            "Regional economic indicators"
        ],
        summary="Downtown Austin features a mix of high-rise condos and urban living spaces.",
        caveats=[
            "This is an estimate based on general market knowledge",
            "Actual prices vary significantly by property type"
        ]
    )


@pytest.fixture
def sample_housing_response_dict():
    return {
        "neighborhood": "Downtown",
        "city": "Austin",
        "state": "TX",
        "price_range": {
            "min": 350000,
            "max": 850000,
            "median": 550000
        },
        "confidence_level": "medium",
        "data_sources": [
            "General knowledge of Austin housing market trends",
            "Regional economic indicators"
        ],
        "summary": "Downtown Austin features a mix of high-rise condos and urban living spaces.",
        "caveats": [
            "This is an estimate based on general market knowledge",
            "Actual prices vary significantly by property type"
        ]
    }


@pytest.fixture
def mock_anthropic_client():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"test": "data"}')]
    mock_client.messages.create.return_value = mock_response
    return mock_client

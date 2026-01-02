import pytest
from pydantic import ValidationError

from app.models.housing import (
    ConfidenceLevel,
    PriceRange,
    HousingPricingResponse
)


class TestPriceRange:
    def test_valid_price_range(self):
        price_range = PriceRange(min=100000, max=500000, median=300000)
        assert price_range.min == 100000
        assert price_range.max == 500000
        assert price_range.median == 300000

    def test_price_range_with_missing_fields(self):
        with pytest.raises(ValidationError):
            PriceRange(min=100000, max=500000)

    def test_price_range_with_invalid_types(self):
        with pytest.raises(ValidationError):
            PriceRange(min="invalid", max=500000, median=300000)


class TestConfidenceLevel:
    def test_confidence_level_values(self):
        assert ConfidenceLevel.LOW == "low"
        assert ConfidenceLevel.MEDIUM == "medium"
        assert ConfidenceLevel.HIGH == "high"

    def test_confidence_level_validation(self):
        response = HousingPricingResponse(
            neighborhood="Test",
            city="Test",
            state="TX",
            price_range=PriceRange(min=100000, max=500000, median=300000),
            confidence_level=ConfidenceLevel.HIGH,
            data_sources=["test"],
            summary="test"
        )
        assert response.confidence_level == ConfidenceLevel.HIGH


class TestHousingPricingResponse:
    def test_valid_housing_response(self, sample_housing_response):
        assert sample_housing_response.neighborhood == "Downtown"
        assert sample_housing_response.city == "Austin"
        assert sample_housing_response.state == "TX"
        assert sample_housing_response.price_range.min == 350000
        assert sample_housing_response.confidence_level == ConfidenceLevel.MEDIUM
        assert len(sample_housing_response.data_sources) == 2
        assert len(sample_housing_response.caveats) == 2

    def test_housing_response_from_dict(self, sample_housing_response_dict):
        response = HousingPricingResponse(**sample_housing_response_dict)
        assert response.neighborhood == "Downtown"
        assert response.city == "Austin"
        assert response.confidence_level == ConfidenceLevel.MEDIUM

    def test_housing_response_missing_required_fields(self):
        with pytest.raises(ValidationError):
            HousingPricingResponse(
                neighborhood="Test",
                city="Test"
            )

    def test_housing_response_invalid_confidence_level(self):
        with pytest.raises(ValidationError):
            HousingPricingResponse(
                neighborhood="Test",
                city="Test",
                state="TX",
                price_range=PriceRange(min=100000, max=500000, median=300000),
                confidence_level="invalid",
                data_sources=["test"],
                summary="test"
            )

    def test_housing_response_caveats_default_empty(self):
        response = HousingPricingResponse(
            neighborhood="Test",
            city="Test",
            state="TX",
            price_range=PriceRange(min=100000, max=500000, median=300000),
            confidence_level=ConfidenceLevel.MEDIUM,
            data_sources=["test"],
            summary="test"
        )
        assert response.caveats == []

    def test_housing_response_json_serialization(self, sample_housing_response):
        json_data = sample_housing_response.model_dump()
        assert isinstance(json_data, dict)
        assert json_data["neighborhood"] == "Downtown"
        assert json_data["confidence_level"] == "medium"
        assert isinstance(json_data["price_range"], dict)

    def test_housing_response_with_empty_data_sources(self):
        with pytest.raises(ValidationError):
            HousingPricingResponse(
                neighborhood="Test",
                city="Test",
                state="TX",
                price_range=PriceRange(min=100000, max=500000, median=300000),
                confidence_level=ConfidenceLevel.MEDIUM,
                data_sources=[],
                summary="test"
            )

import pytest
from unittest.mock import patch, AsyncMock
from fastapi import status

from app.services.claude_service import ClaudeServiceError
from app.models.housing import HousingPricingResponse


class TestHousingPricingEndpoint:
    def test_health_check(self, test_client):
        response = test_client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "healthy"}

    def test_successful_pricing_request(self, test_client, sample_housing_response):
        with patch(
            'app.api.housing.claude_service.get_housing_pricing_estimate',
            return_value=sample_housing_response
        ):
            response = test_client.get(
                "/housing/pricing",
                params={
                    "neighborhood": "Downtown",
                    "city": "Austin",
                    "state": "TX"
                }
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["neighborhood"] == "Downtown"
            assert data["city"] == "Austin"
            assert data["state"] == "TX"
            assert "price_range" in data
            assert "confidence_level" in data
            assert "data_sources" in data
            assert "summary" in data

    def test_missing_query_parameters(self, test_client):
        response = test_client.get("/housing/pricing")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_missing_neighborhood_parameter(self, test_client):
        response = test_client.get(
            "/housing/pricing",
            params={
                "city": "Austin",
                "state": "TX"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_missing_city_parameter(self, test_client):
        response = test_client.get(
            "/housing/pricing",
            params={
                "neighborhood": "Downtown",
                "state": "TX"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_missing_state_parameter(self, test_client):
        response = test_client.get(
            "/housing/pricing",
            params={
                "neighborhood": "Downtown",
                "city": "Austin"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_empty_neighborhood_parameter(self, test_client):
        response = test_client.get(
            "/housing/pricing",
            params={
                "neighborhood": "   ",
                "city": "Austin",
                "state": "TX"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non-empty" in response.json()["detail"].lower()

    def test_empty_city_parameter(self, test_client):
        response = test_client.get(
            "/housing/pricing",
            params={
                "neighborhood": "Downtown",
                "city": "",
                "state": "TX"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_empty_state_parameter(self, test_client):
        response = test_client.get(
            "/housing/pricing",
            params={
                "neighborhood": "Downtown",
                "city": "Austin",
                "state": ""
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_whitespace_trimming(self, test_client, sample_housing_response):
        with patch(
            'app.api.housing.claude_service.get_housing_pricing_estimate',
            return_value=sample_housing_response
        ) as mock_service:
            response = test_client.get(
                "/housing/pricing",
                params={
                    "neighborhood": "  Downtown  ",
                    "city": "  Austin  ",
                    "state": "  TX  "
                }
            )

            assert response.status_code == status.HTTP_200_OK
            mock_service.assert_called_once_with(
                neighborhood="Downtown",
                city="Austin",
                state="TX"
            )

    def test_claude_service_error_returns_502(self, test_client):
        with patch(
            'app.api.housing.claude_service.get_housing_pricing_estimate',
            side_effect=ClaudeServiceError("Claude API failed")
        ):
            response = test_client.get(
                "/housing/pricing",
                params={
                    "neighborhood": "Downtown",
                    "city": "Austin",
                    "state": "TX"
                }
            )

            assert response.status_code == status.HTTP_502_BAD_GATEWAY
            assert "Upstream service error" in response.json()["detail"]

    def test_unexpected_error_returns_500(self, test_client):
        with patch(
            'app.api.housing.claude_service.get_housing_pricing_estimate',
            side_effect=Exception("Unexpected error")
        ):
            response = test_client.get(
                "/housing/pricing",
                params={
                    "neighborhood": "Downtown",
                    "city": "Austin",
                    "state": "TX"
                }
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Internal server error" in response.json()["detail"]

    def test_special_characters_in_parameters(self, test_client, sample_housing_response):
        with patch(
            'app.api.housing.claude_service.get_housing_pricing_estimate',
            return_value=sample_housing_response
        ):
            response = test_client.get(
                "/housing/pricing",
                params={
                    "neighborhood": "North-West District",
                    "city": "St. Louis",
                    "state": "MO"
                }
            )

            assert response.status_code == status.HTTP_200_OK

    def test_response_structure(self, test_client, sample_housing_response):
        with patch(
            'app.api.housing.claude_service.get_housing_pricing_estimate',
            return_value=sample_housing_response
        ):
            response = test_client.get(
                "/housing/pricing",
                params={
                    "neighborhood": "Downtown",
                    "city": "Austin",
                    "state": "TX"
                }
            )

            data = response.json()
            assert "neighborhood" in data
            assert "city" in data
            assert "state" in data
            assert "price_range" in data
            assert "min" in data["price_range"]
            assert "max" in data["price_range"]
            assert "median" in data["price_range"]
            assert "confidence_level" in data
            assert "data_sources" in data
            assert isinstance(data["data_sources"], list)
            assert "summary" in data
            assert "caveats" in data
            assert isinstance(data["caveats"], list)

    def test_openapi_schema(self, test_client):
        response = test_client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        schema = response.json()
        assert "/housing/pricing" in schema["paths"]

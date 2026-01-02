import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from anthropic import APIError, APITimeoutError

from app.services.claude_service import ClaudeService, ClaudeServiceError
from app.models.housing import HousingPricingResponse, ConfidenceLevel


@pytest.fixture
def claude_service():
    with patch('app.services.claude_service.settings') as mock_settings:
        mock_settings.anthropic_api_key = "test_key"
        mock_settings.claude_model = "claude-test"
        mock_settings.claude_timeout = 30
        mock_settings.claude_max_tokens = 4096
        service = ClaudeService()
        return service


class TestClaudeService:
    @pytest.mark.asyncio
    async def test_successful_housing_estimate(
        self,
        claude_service,
        sample_housing_response_dict
    ):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(sample_housing_response_dict))]

        with patch.object(claude_service.client.messages, 'create', return_value=mock_response):
            result = await claude_service.get_housing_pricing_estimate(
                neighborhood="Downtown",
                city="Austin",
                state="TX"
            )

            assert isinstance(result, HousingPricingResponse)
            assert result.neighborhood == "Downtown"
            assert result.city == "Austin"
            assert result.state == "TX"
            assert result.confidence_level == ConfidenceLevel.MEDIUM

    @pytest.mark.asyncio
    async def test_claude_api_timeout_error(self, claude_service):
        with patch.object(
            claude_service.client.messages,
            'create',
            side_effect=APITimeoutError("Timeout")
        ):
            with pytest.raises(ClaudeServiceError) as exc_info:
                await claude_service.get_housing_pricing_estimate(
                    neighborhood="Downtown",
                    city="Austin",
                    state="TX"
                )
            assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_claude_api_error(self, claude_service):
        with patch.object(
            claude_service.client.messages,
            'create',
            side_effect=APIError("API Error")
        ):
            with pytest.raises(ClaudeServiceError) as exc_info:
                await claude_service.get_housing_pricing_estimate(
                    neighborhood="Downtown",
                    city="Austin",
                    state="TX"
                )
            assert "API error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_json_response(self, claude_service):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="not valid json")]

        with patch.object(claude_service.client.messages, 'create', return_value=mock_response):
            with pytest.raises(ClaudeServiceError) as exc_info:
                await claude_service.get_housing_pricing_estimate(
                    neighborhood="Downtown",
                    city="Austin",
                    state="TX"
                )
            assert "Invalid JSON" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validation_error_response(self, claude_service):
        invalid_response = {
            "neighborhood": "Downtown",
            "city": "Austin"
        }
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(invalid_response))]

        with patch.object(claude_service.client.messages, 'create', return_value=mock_response):
            with pytest.raises(ClaudeServiceError) as exc_info:
                await claude_service.get_housing_pricing_estimate(
                    neighborhood="Downtown",
                    city="Austin",
                    state="TX"
                )
            assert "validation failed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_retry_logic_success_on_second_attempt(
        self,
        claude_service,
        sample_housing_response_dict
    ):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(sample_housing_response_dict))]

        with patch.object(
            claude_service.client.messages,
            'create',
            side_effect=[APITimeoutError("Timeout"), mock_response]
        ):
            result = await claude_service.get_housing_pricing_estimate(
                neighborhood="Downtown",
                city="Austin",
                state="TX"
            )
            assert isinstance(result, HousingPricingResponse)

    @pytest.mark.asyncio
    async def test_retry_exhausted(self, claude_service):
        with patch.object(
            claude_service.client.messages,
            'create',
            side_effect=APITimeoutError("Timeout")
        ):
            with pytest.raises(ClaudeServiceError):
                await claude_service.get_housing_pricing_estimate(
                    neighborhood="Downtown",
                    city="Austin",
                    state="TX"
                )

    def test_build_pricing_prompt(self, claude_service):
        prompt = claude_service._build_pricing_prompt(
            neighborhood="Downtown",
            city="Austin",
            state="TX"
        )

        assert "Downtown" in prompt
        assert "Austin" in prompt
        assert "TX" in prompt
        assert "MLS" in prompt
        assert "Zillow" in prompt
        assert "JSON" in prompt
        assert "confidence_level" in prompt

    @pytest.mark.asyncio
    async def test_unexpected_exception(self, claude_service):
        with patch.object(
            claude_service.client.messages,
            'create',
            side_effect=Exception("Unexpected error")
        ):
            with pytest.raises(ClaudeServiceError) as exc_info:
                await claude_service.get_housing_pricing_estimate(
                    neighborhood="Downtown",
                    city="Austin",
                    state="TX"
                )
            assert "Unexpected error" in str(exc_info.value)

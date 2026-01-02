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
        mock_request = MagicMock()
        with patch.object(
            claude_service.client.messages,
            'create',
            side_effect=APIError("API Error", request=mock_request, body=None)
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
            # With the new JSON extraction logic, this message is wrapped as "Unexpected error"
            assert "No JSON object found" in str(exc_info.value)

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


class TestExtractJsonFromResponse:
    """Tests for the _extract_json_from_response method added to handle various Claude response formats."""

    def test_extract_clean_json(self, claude_service):
        """Test extraction of clean JSON without any formatting."""
        clean_json = '{"key": "value", "number": 42}'
        result = claude_service._extract_json_from_response(clean_json)
        assert result == clean_json
        assert json.loads(result) == {"key": "value", "number": 42}

    def test_extract_json_with_whitespace(self, claude_service):
        """Test extraction of JSON with leading/trailing whitespace."""
        json_with_whitespace = '  \n  {"key": "value"}  \n  '
        result = claude_service._extract_json_from_response(json_with_whitespace)
        assert result == '{"key": "value"}'
        assert json.loads(result) == {"key": "value"}

    def test_extract_json_with_markdown_code_fence(self, claude_service):
        """Test extraction of JSON wrapped in markdown code fences."""
        markdown_json = '```json\n{"key": "value", "nested": {"data": 123}}\n```'
        result = claude_service._extract_json_from_response(markdown_json)
        assert result == '{"key": "value", "nested": {"data": 123}}'
        assert json.loads(result) == {"key": "value", "nested": {"data": 123}}

    def test_extract_json_with_plain_code_fence(self, claude_service):
        """Test extraction of JSON wrapped in plain code fences (no language specified)."""
        markdown_json = '```\n{"key": "value"}\n```'
        result = claude_service._extract_json_from_response(markdown_json)
        assert result == '{"key": "value"}'
        assert json.loads(result) == {"key": "value"}

    def test_extract_json_with_text_before_and_after(self, claude_service):
        """Test extraction of JSON with extra text before and after."""
        response_with_text = 'Here is the JSON response:\n{"key": "value"}\nThat was the response.'
        result = claude_service._extract_json_from_response(response_with_text)
        assert result == '{"key": "value"}'
        assert json.loads(result) == {"key": "value"}

    def test_extract_nested_json_with_multiple_braces(self, claude_service):
        """Test extraction of nested JSON objects with multiple braces."""
        nested_json = 'Text before {"outer": {"inner": {"deep": "value"}}} text after'
        result = claude_service._extract_json_from_response(nested_json)
        assert result == '{"outer": {"inner": {"deep": "value"}}}'
        assert json.loads(result) == {"outer": {"inner": {"deep": "value"}}}

    def test_extract_json_with_arrays(self, claude_service):
        """Test extraction of JSON containing arrays."""
        json_with_arrays = '```json\n{"items": [1, 2, 3], "nested": [{"a": 1}, {"b": 2}]}\n```'
        result = claude_service._extract_json_from_response(json_with_arrays)
        parsed = json.loads(result)
        assert parsed["items"] == [1, 2, 3]
        assert len(parsed["nested"]) == 2

    def test_extract_json_multiline(self, claude_service):
        """Test extraction of multiline JSON object."""
        multiline_json = '''```
{
  "key": "value",
  "number": 42,
  "nested": {
    "field": "data"
  }
}
```'''
        result = claude_service._extract_json_from_response(multiline_json)
        parsed = json.loads(result)
        assert parsed["key"] == "value"
        assert parsed["number"] == 42
        assert parsed["nested"]["field"] == "data"

    def test_extract_json_no_opening_brace_raises_error(self, claude_service):
        """Test that missing opening brace raises ClaudeServiceError."""
        invalid_response = "This response has no JSON object"
        with pytest.raises(ClaudeServiceError) as exc_info:
            claude_service._extract_json_from_response(invalid_response)
        assert "No JSON object found" in str(exc_info.value)

    def test_extract_json_no_closing_brace_raises_error(self, claude_service):
        """Test that missing closing brace raises ClaudeServiceError."""
        invalid_response = '{"key": "value"'
        with pytest.raises(ClaudeServiceError) as exc_info:
            claude_service._extract_json_from_response(invalid_response)
        assert "No JSON object found" in str(exc_info.value)

    def test_extract_json_empty_string_raises_error(self, claude_service):
        """Test that empty string raises ClaudeServiceError."""
        with pytest.raises(ClaudeServiceError) as exc_info:
            claude_service._extract_json_from_response("")
        assert "No JSON object found" in str(exc_info.value)

    def test_extract_json_only_whitespace_raises_error(self, claude_service):
        """Test that whitespace-only string raises ClaudeServiceError."""
        with pytest.raises(ClaudeServiceError) as exc_info:
            claude_service._extract_json_from_response("   \n\t   ")
        assert "No JSON object found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_integration_with_call_claude_with_retry_clean_json(
        self,
        claude_service,
        sample_housing_response_dict
    ):
        """Test that _extract_json_from_response integrates correctly with _call_claude_with_retry for clean JSON."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(sample_housing_response_dict))]

        with patch.object(claude_service.client.messages, 'create', return_value=mock_response):
            result = await claude_service._call_claude_with_retry("test prompt")
            assert result == sample_housing_response_dict

    @pytest.mark.asyncio
    async def test_integration_with_call_claude_with_retry_markdown_wrapped(
        self,
        claude_service,
        sample_housing_response_dict
    ):
        """Test that _extract_json_from_response integrates correctly with _call_claude_with_retry for markdown-wrapped JSON."""
        mock_response = MagicMock()
        markdown_response = f'```json\n{json.dumps(sample_housing_response_dict)}\n```'
        mock_response.content = [MagicMock(text=markdown_response)]

        with patch.object(claude_service.client.messages, 'create', return_value=mock_response):
            result = await claude_service._call_claude_with_retry("test prompt")
            assert result == sample_housing_response_dict

    @pytest.mark.asyncio
    async def test_integration_with_call_claude_with_retry_text_wrapped(
        self,
        claude_service,
        sample_housing_response_dict
    ):
        """Test that _extract_json_from_response integrates correctly with _call_claude_with_retry for text-wrapped JSON."""
        mock_response = MagicMock()
        text_response = f'Here is your response:\n{json.dumps(sample_housing_response_dict)}\nEnd of response.'
        mock_response.content = [MagicMock(text=text_response)]

        with patch.object(claude_service.client.messages, 'create', return_value=mock_response):
            result = await claude_service._call_claude_with_retry("test prompt")
            assert result == sample_housing_response_dict

    @pytest.mark.asyncio
    async def test_integration_with_call_claude_with_retry_no_json_raises_error(
        self,
        claude_service
    ):
        """Test that missing JSON in response raises appropriate error through the integration."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="This response contains no JSON")]

        with patch.object(claude_service.client.messages, 'create', return_value=mock_response):
            with pytest.raises(ClaudeServiceError) as exc_info:
                await claude_service._call_claude_with_retry("test prompt")
            assert "No JSON object found" in str(exc_info.value)

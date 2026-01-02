import json
import asyncio
from typing import Optional
from anthropic import Anthropic, APIError, APITimeoutError
from pydantic import ValidationError

from app.config import settings
from app.models.housing import HousingPricingResponse


class ClaudeServiceError(Exception):
    pass


class ClaudeService:
    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model
        self.timeout = settings.claude_timeout
        self.max_tokens = settings.claude_max_tokens

    async def get_housing_pricing_estimate(
        self,
        neighborhood: str,
        city: str,
        state: str
    ) -> HousingPricingResponse:
        prompt = self._build_pricing_prompt(neighborhood, city, state)

        try:
            response_json = await self._call_claude_with_retry(prompt, max_retries=2)
            return self._parse_and_validate_response(response_json)
        except APITimeoutError as e:
            raise ClaudeServiceError(f"Claude API timeout: {str(e)}")
        except APIError as e:
            raise ClaudeServiceError(f"Claude API error: {str(e)}")
        except Exception as e:
            raise ClaudeServiceError(f"Unexpected error: {str(e)}")

    def _build_pricing_prompt(
        self,
        neighborhood: str,
        city: str,
        state: str
    ) -> str:
        return f"""You are a housing market analysis assistant. Provide estimated housing pricing insights for the specified location.

Location:
- Neighborhood: {neighborhood}
- City: {city}
- State: {state}

IMPORTANT CONSTRAINTS:
- You do NOT have access to MLS, Zillow, Redfin, Realtor.com, or any proprietary housing datasets
- Base your estimates on general knowledge of the region, economic factors, and publicly known trends
- All pricing data must be framed as estimates with appropriate confidence levels
- Be transparent about the limitations of your estimates

Provide your response as a JSON object with this exact structure:
{{
  "neighborhood": "{neighborhood}",
  "city": "{city}",
  "state": "{state}",
  "price_range": {{
    "min": <integer>,
    "max": <integer>,
    "median": <integer>
  }},
  "confidence_level": "low" | "medium" | "high",
  "data_sources": [
    "list of estimation methods or knowledge sources used"
  ],
  "summary": "brief explanation of the pricing estimate",
  "caveats": [
    "important disclaimers or limitations"
  ]
}}

Return ONLY the JSON object, no additional text or formatting."""

    async def _call_claude_with_retry(
        self,
        prompt: str,
        max_retries: int = 2
    ) -> dict:
        for attempt in range(max_retries + 1):
            try:
                response = await asyncio.to_thread(
                    self.client.messages.create,
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=self.timeout
                )

                content = response.content[0].text
                return json.loads(content)

            except (APITimeoutError, APIError) as e:
                if attempt == max_retries:
                    raise
                await asyncio.sleep(2 ** attempt)
            except json.JSONDecodeError as e:
                raise ClaudeServiceError(f"Invalid JSON response from Claude: {str(e)}")

    def _parse_and_validate_response(self, response_json: dict) -> HousingPricingResponse:
        try:
            return HousingPricingResponse(**response_json)
        except ValidationError as e:
            raise ClaudeServiceError(f"Response validation failed: {str(e)}")


claude_service = ClaudeService()

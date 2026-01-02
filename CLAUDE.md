# Claude Code Instructions

You are operating inside a production-grade backend repository.

## Core Principles
- Prefer correctness and clarity over cleverness
- Never hallucinate proprietary or real-time data
- All pricing data must be framed as estimates
- All responses must be deterministic and JSON-serializable

## Technology Constraints
- Language: Python 3.11+
- Framework: FastAPI
- Async-first design
- Use Pydantic v2 models
- Use the official Anthropic Python SDK only

## Architecture Rules
- API routes go in `app/api`
- External integrations go in `app/services`
- No business logic inside route handlers
- Configuration must be centralized in `app/config.py`
- Environment variables only for secrets

## Claude API Usage Rules
- Always request JSON-only responses from Claude
- Validate and parse Claude output before returning it
- Handle timeouts, retries, and malformed responses
- Never return raw Claude text to clients

## Data Integrity & Legal Guardrails
- Do NOT claim access to:
  - MLS
  - Zillow
  - Redfin
  - Realtor.com
  - Proprietary or paid housing datasets
- Clearly label confidence levels as low/medium/high
- Include data_sources explaining the estimate basis

## Error Handling
- Upstream Claude failures → HTTP 502
- Input validation failures → HTTP 400
- Unexpected failures → HTTP 500 with safe error messages

## Repository Hygiene
- Do not modify files unless required by the task
- Do not remove existing functionality
- Keep diffs minimal and focused
- Add README instructions for any new setup steps

## Output Requirements
- Produce fully working code
- No TODOs or placeholders
- No commented-out blocks
- No explanatory prose inside API responses

## Testing Requirements
- All production code must have corresponding unit tests
- Tests go in `tests/` directory mirroring `app/` structure
- Use pytest as the test framework
- Maintain minimum 80% code coverage
- Use pytest-asyncio for async test support

### Testing Standards
- Mock external dependencies (Anthropic API, network calls)
- Test both success and failure scenarios
- Test input validation and error handling
- Test edge cases and boundary conditions
- Use descriptive test names that explain what is being tested
- Organize tests in classes by functionality

### Test Structure
- Unit tests for Pydantic models: `tests/models/`
- Unit tests for services: `tests/services/`
- Integration tests for API endpoints: `tests/api/`
- Shared fixtures in `tests/conftest.py`

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/api/test_housing.py

# Run specific test
pytest tests/api/test_housing.py::TestHousingPricingEndpoint::test_successful_pricing_request
```

### What to Test
- Models: validation, serialization, field requirements
- Services: successful calls, retries, timeouts, errors, malformed responses
- API endpoints: valid requests, missing parameters, empty values, error responses
- Error handling: all HTTP status codes (400, 502, 500)
- Edge cases: special characters, whitespace, boundary values

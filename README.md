# Neighborhood Housing Pricing API

Utilizing Claude AI to provide estimated housing pricing insights for any neighborhood in the U.S.

## Features

- FastAPI-based REST API
- GET /housing/pricing endpoint for housing price estimates
- Powered by Claude AI (Anthropic)
- Async-first architecture
- Comprehensive error handling
- Pydantic v2 validation

## Prerequisites

- Python 3.11 or higher
- Anthropic API key

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd neighborhodd-mortgage-estimate
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file:
```bash
cp .env.example .env
```

5. Add your Anthropic API key to the `.env` file:
```
ANTHROPIC_API_KEY=your_actual_api_key_here
```

## Running the Server

Start the development server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Usage

### Get Housing Pricing Estimate

**Endpoint:** `GET /housing/pricing`

**Query Parameters:**
- `neighborhood` (required): Neighborhood name
- `city` (required): City name
- `state` (required): State name or abbreviation

**Example Request:**
```bash
curl "http://localhost:8000/housing/pricing?neighborhood=Downtown&city=Austin&state=TX"
```

**Example Response:**
```json
{
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
    "Regional economic indicators",
    "Downtown urban area pricing patterns"
  ],
  "summary": "Downtown Austin features a mix of high-rise condos and urban living spaces with pricing reflecting its central location and amenities.",
  "caveats": [
    "This is an estimate based on general market knowledge",
    "Actual prices vary significantly by property type, size, and condition",
    "Does not reflect real-time MLS or proprietary data"
  ]
}
```

## Health Check

**Endpoint:** `GET /health`

```bash
curl http://localhost:8000/health
```

## Testing

The project includes comprehensive unit and integration tests with 80%+ code coverage.

### Running Tests

```bash
# Install test dependencies (if not already installed)
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run with HTML coverage report
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in your browser

# Run specific test file
pytest tests/api/test_housing.py

# Run specific test
pytest tests/api/test_housing.py::TestHousingPricingEndpoint::test_successful_pricing_request

# Run with verbose output
pytest -v
```

### Test Coverage

- **Models** (`tests/models/`): Pydantic validation, serialization, field requirements
- **Services** (`tests/services/`): Claude API integration, retries, error handling
- **API Endpoints** (`tests/api/`): Request validation, response structure, error codes

### Writing Tests

When adding new features, ensure you:
1. Write tests that cover both success and failure scenarios
2. Mock external dependencies (Claude API)
3. Test edge cases and boundary conditions
4. Maintain minimum 80% code coverage

## Error Handling

- `400` - Invalid input parameters
- `502` - Claude API service error
- `500` - Internal server error

## Important Disclaimers

This API provides estimated housing pricing insights and does NOT have access to:
- MLS (Multiple Listing Service)
- Zillow
- Redfin
- Realtor.com
- Any proprietary or paid housing datasets

All estimates are based on general knowledge and should be used for informational purposes only.

from fastapi import APIRouter, HTTPException, Query

from app.models.housing import HousingPricingResponse
from app.services.claude_service import claude_service, ClaudeServiceError


router = APIRouter(prefix="/housing", tags=["housing"])


@router.get("/pricing", response_model=HousingPricingResponse)
async def get_housing_pricing(
    neighborhood: str = Query(..., description="Neighborhood name"),
    city: str = Query(..., description="City name"),
    state: str = Query(..., description="State name or abbreviation")
) -> HousingPricingResponse:
    if not neighborhood.strip() or not city.strip() or not state.strip():
        raise HTTPException(
            status_code=400,
            detail="neighborhood, city, and state must be non-empty strings"
        )

    try:
        result = await claude_service.get_housing_pricing_estimate(
            neighborhood=neighborhood.strip(),
            city=city.strip(),
            state=state.strip()
        )
        return result
    except ClaudeServiceError as e:
        raise HTTPException(status_code=502, detail=f"Upstream service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

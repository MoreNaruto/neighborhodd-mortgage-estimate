from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.housing import router as housing_router


app = FastAPI(
    title="Neighborhood Housing Pricing API",
    description="Estimated housing pricing insights powered by Claude AI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(housing_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

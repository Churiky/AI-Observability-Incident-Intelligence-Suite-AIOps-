"""
API v1 router configuration.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import logs, incidents, anomalies, predictions, ai, metrics

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(anomalies.router, prefix="/anomalies", tags=["anomalies"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])


@api_router.get("/")
async def root():
    return {"message": "API v1 is operational"}
# app/api/v1/api_router.py
from fastapi import APIRouter

from app.api.v1.endpoints import claims, analysis, data_upload

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    analysis.router, 
    prefix="/analyze", 
    tags=["analysis"],
    responses={404: {"description": "Not found"}}
)

api_router.include_router(
    claims.router, 
    prefix="/claims", 
    tags=["claims"],
    responses={404: {"description": "Not found"}}
)

api_router.include_router(
    data_upload.router, 
    prefix="/data", 
    tags=["data"],
    responses={404: {"description": "Not found"}}
)

# Add health check at API level
@api_router.get("/health")
async def api_health_check():
    """API-level health check"""
    return {
        "status": "healthy",
        "api_version": "v1",
        "endpoints": [
            "/analyze - FRA analysis with WebGIS",
            "/claims - FRA claims management", 
            "/data - Data upload and processing"
        ]
    }
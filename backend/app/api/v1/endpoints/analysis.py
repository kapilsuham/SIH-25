# app/api/v1/endpoints/analysis.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional
import logging
import asyncio

from app.db.session import get_db
from app.services.fra_mapping_service import FRAMappingService
from app.crud import crud_claim

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize mapping service
mapping_service = FRAMappingService()

class AnalysisRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    radius_km: float = Field(default=2.0, ge=0.1, le=50.0, description="Analysis radius in kilometers")
    save_to_db: bool = Field(default=True, description="Save analysis results to database")
    user_id: Optional[str] = Field(None, description="User identifier")

    @validator('latitude')
    def validate_latitude(cls, v):
        if not (-90 <= v <= 90):
            raise ValueError('Latitude must be between -90 and 90 degrees')
        return v

    @validator('longitude')
    def validate_longitude(cls, v):
        if not (-180 <= v <= 180):
            raise ValueError('Longitude must be between -180 and 180 degrees')
        return v

class AnalysisResponse(BaseModel):
    status: str
    coordinates: Dict[str, float]
    geographic_features: Dict[str, Any]
    satellite_analysis: Dict[str, Any]
    fra_analysis: Dict[str, Any]
    maps: Dict[str, str]
    recommendations: Dict[str, Any]
    analysis_timestamp: str
    execution_time_seconds: float
    data_sources: list

# app/api/v1/endpoints/analysis.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional
import logging
import asyncio

from app.db.session import get_db
from app.services.fra_mapping_service import FRAMappingService
from app.crud import crud_claim

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize mapping service
mapping_service = FRAMappingService()

class AnalysisRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    radius_km: float = Field(default=2.0, ge=0.1, le=50.0, description="Analysis radius in kilometers")
    save_to_db: bool = Field(default=True, description="Save analysis results to database")
    user_id: Optional[str] = Field(None, description="User identifier")

    @validator('latitude')
    def validate_latitude(cls, v):
        if not (-90 <= v <= 90):
            raise ValueError('Latitude must be between -90 and 90 degrees')
        return v

    @validator('longitude')
    def validate_longitude(cls, v):
        if not (-180 <= v <= 180):
            raise ValueError('Longitude must be between -180 and 180 degrees')
        return v

class AnalysisResponse(BaseModel):
    status: str
    coordinates: Dict[str, float]
    geographic_features: Dict[str, Any]
    satellite_analysis: Dict[str, Any]
    fra_analysis: Dict[str, Any]
    maps: Dict[str, str]
    recommendations: Dict[str, Any]
    analysis_timestamp: str
    execution_time_seconds: float
    data_sources: list

@router.post("/", response_model=AnalysisResponse)
async def perform_fra_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Perform comprehensive FRA analysis with WebGIS and satellite imagery
    Automatically saves generated maps to frontend public folder
    """
    try:
        logger.info(f"Starting FRA analysis for coordinates: {request.latitude}, {request.longitude}")
        
        # Perform the comprehensive analysis
        result = await mapping_service.analyze_and_map(
            request.latitude, 
            request.longitude, 
            request.radius_km
        )
        
        if result['status'] != 'success':
            raise HTTPException(status_code=400, detail=result.get('message', 'Analysis failed'))
        
        # Save to database in background if requested
        if request.save_to_db:
            background_tasks.add_task(
                save_analysis_to_db, 
                db, request, result
            )
        
        logger.info(f"Analysis completed successfully in {result['execution_time_seconds']:.2f} seconds")
        return result
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for analysis service"""
    return {
        "status": "healthy",
        "service": "FRA Analysis Service",
        "mapping_service": "ready",
        "frontend_integration": "enabled" if mapping_service.frontend_public_dir else "disabled"
    }

@router.get("/maps/{filename}")
async def get_map_file(filename: str):
    """Get generated map file"""
    import os
    from fastapi.responses import FileResponse
    
    file_path = os.path.join(mapping_service.backend_maps_dir, filename)
    
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='text/html')
    else:
        raise HTTPException(status_code=404, detail="Map file not found")

@router.get("/maps")
async def list_generated_maps():
    """List all generated map files"""
    import os
    
    maps = []
    if os.path.exists(mapping_service.backend_maps_dir):
        for filename in os.listdir(mapping_service.backend_maps_dir):
            if filename.endswith('.html'):
                file_path = os.path.join(mapping_service.backend_maps_dir, filename)
                stat = os.stat(file_path)
                maps.append({
                    'filename': filename,
                    'size_bytes': stat.st_size,
                    'created_at': stat.st_ctime,
                    'url': f"/api/v1/analyze/maps/{filename}"
                })
    
    return {
        'total_maps': len(maps),
        'maps': sorted(maps, key=lambda x: x['created_at'], reverse=True)
    }

@router.delete("/maps/{filename}")
async def delete_map_file(filename: str):
    """Delete a generated map file"""
    import os
    
    # Delete from backend
    backend_path = os.path.join(mapping_service.backend_maps_dir, filename)
    deleted_files = []
    
    if os.path.exists(backend_path):
        os.remove(backend_path)
        deleted_files.append(backend_path)
    
    # Delete from frontend if exists
    if mapping_service.frontend_public_dir:
        frontend_path = os.path.join(mapping_service.frontend_public_dir, "fra_maps", filename)
        if os.path.exists(frontend_path):
            os.remove(frontend_path)
            deleted_files.append(frontend_path)
    
    if deleted_files:
        return {"message": f"Deleted {len(deleted_files)} files", "deleted_files": deleted_files}
    else:
        raise HTTPException(status_code=404, detail="Map file not found")

class BatchAnalysisRequest(BaseModel):
    coordinates: list[Dict[str, float]] = Field(..., description="List of coordinate pairs")
    radius_km: float = Field(default=2.0, ge=0.1, le=50.0)
    save_to_db: bool = Field(default=True)

@router.post("/batch")
async def perform_batch_analysis(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Perform batch FRA analysis for multiple locations
    """
    if len(request.coordinates) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 locations per batch request")
    
    results = []
    
    for i, coord in enumerate(request.coordinates):
        try:
            lat = coord.get('lat') or coord.get('latitude')
            lon = coord.get('lon') or coord.get('longitude')
            
            if lat is None or lon is None:
                results.append({
                    'index': i,
                    'status': 'error',
                    'message': 'Invalid coordinates'
                })
                continue
            
            # Perform analysis
            result = await mapping_service.analyze_and_map(lat, lon, request.radius_km)
            result['index'] = i
            results.append(result)
            
        except Exception as e:
            results.append({
                'index': i,
                'status': 'error',
                'message': str(e)
            })
    
    return {
        'total_requests': len(request.coordinates),
        'successful': len([r for r in results if r.get('status') == 'success']),
        'failed': len([r for r in results if r.get('status') == 'error']),
        'results': results
    }

async def save_analysis_to_db(db: Session, request: AnalysisRequest, result: Dict[str, Any]):
    """Save analysis result to database (background task)"""
    try:
        import json
        
        # Save as analysis result
        crud_claim.save_analysis_result(
            db=db,
            analysis_type="comprehensive_fra",
            coordinates_lat=request.latitude,
            coordinates_lon=request.longitude,
            radius_km=request.radius_km,
            results_data=result,
            execution_time=result.get('execution_time_seconds', 0),
            data_sources=','.join(result.get('data_sources', []))
        )
        
        logger.info(f"Analysis result saved to database for {request.latitude}, {request.longitude}")
        
    except Exception as e:
        logger.error(f"Failed to save analysis to database: {e}")

# Additional utility endpoints

@router.get("/regions")
async def get_supported_regions():
    """Get list of supported regions and their characteristics"""
    return {
        'supported_regions': mapping_service.regions,
        'total_regions': len(mapping_service.regions)
    }

@router.post("/validate-coordinates")
async def validate_coordinates(latitude: float, longitude: float):
    """Validate coordinates and return region information"""
    
    if not mapping_service._validate_coordinates(latitude, longitude, 2.0):
        raise HTTPException(status_code=400, detail="Invalid coordinates")
    
    region_info = mapping_service._identify_region(latitude, longitude)
    
    return {
        'valid': True,
        'coordinates': {'latitude': latitude, 'longitude': longitude},
        'region': region_info,
        'estimated_analysis_time': '30-60 seconds'
    }
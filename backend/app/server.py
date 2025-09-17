from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from app.fra_mapping import FRAMappingAPI

# Initialize FastAPI
app = FastAPI(title="FRA DSS Backend", version="2.0")

# Allow frontend (React @5173) to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# FRA mapping API instance
fra_api = FRAMappingAPI()

# Request model
class AnalyzeRequest(BaseModel):
    latitude: float
    longitude: float
    radius_km: Optional[float] = 2.0


@app.get("/")
def root():
    return {"status": "ok", "message": "FRA DSS API running 🚀"}


@app.post("/api/v1/analyze")
def analyze_location(request: AnalyzeRequest):
    """Run full FRA analysis and return structured results"""
    return fra_api.analyze_location(
        request.latitude, request.longitude, request.radius_km
    )


@app.get("/api/v1/map")
def get_map(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius_km: float = Query(2.0)
):
    """Return interactive map (HTML string)"""
    html_map = fra_api.get_interactive_map(latitude, longitude, radius_km)
    return {"map_html": html_map}

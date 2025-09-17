from typing import Dict, Any

class FRAMappingSystem:
    def __init__(self):
        # Setup models, GIS connections, etc.
        pass

    def analyze_location(self, lat: float, lon: float, radius_km: float = 2.0) -> Dict[str, Any]:
        # Dummy example – replace with your ML/GIS logic
        return {
            "latitude": lat,
            "longitude": lon,
            "radius_km": radius_km,
            "forest_cover": "Dense Forest",
            "eligible_schemes": ["MGNREGA", "PM-KISAN"],
            "risk_index": 0.35
        }

    def get_interactive_map(self, lat: float, lon: float, radius_km: float = 2.0) -> str:
        # Return dummy HTML map (replace with folium or Leaflet later)
        return f"""
        <div>
          <h3>Map for location</h3>
          <p>Lat: {lat}, Lon: {lon}, Radius: {radius_km} km</p>
        </div>
        """

class FRAMappingAPI:
    def __init__(self):
        self.system = FRAMappingSystem()

    def analyze_location(self, lat: float, lon: float, radius_km: float = 2.0):
        return self.system.analyze_location(lat, lon, radius_km)

    def get_interactive_map(self, lat: float, lon: float, radius_km: float = 2.0):
        return self.system.get_interactive_map(lat, lon, radius_km)

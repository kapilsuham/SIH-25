from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import math
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Predefined test locations across India with enhanced data
TEST_LOCATIONS = [
    {"name": "Ranchi, Jharkhand", "lat": 23.3441, "lng": 85.3096, 
     "tribes": ["Santhal", "Munda", "Oraon"], "forest_type": "Tropical Dry Deciduous",
     "population_density": "medium", "development_index": 0.42},
    {"name": "Raipur, Chhattisgarh", "lat": 21.2787, "lng": 81.866, 
     "tribes": ["Gond", "Kamar", "Baiga"], "forest_type": "Tropical Moist Deciduous",
     "population_density": "high", "development_index": 0.38},
    {"name": "Bhubaneswar, Odisha", "lat": 20.2961, "lng": 85.8245, 
     "tribes": ["Santhal", "Kondh", "Saora"], "forest_type": "Tropical Semi-Evergreen",
     "population_density": "medium", "development_index": 0.45},
    {"name": "Bhopal, Madhya Pradesh", "lat": 23.2599, "lng": 77.4126, 
     "tribes": ["Gond", "Bhil", "Korku"], "forest_type": "Tropical Dry Deciduous",
     "population_density": "medium", "development_index": 0.48},
    {"name": "Agartala, Tripura", "lat": 23.8315, "lng": 91.2868, 
     "tribes": ["Tripuri", "Reang", "Jamatia"], "forest_type": "Tropical Evergreen",
     "population_density": "low", "development_index": 0.41},
    {"name": "Varanasi, Uttar Pradesh", "lat": 25.3176, "lng": 82.9739, 
     "tribes": ["Gond", "Kol", "Bhuiya"], "forest_type": "Tropical Dry Deciduous",
     "population_density": "very_high", "development_index": 0.52},
    {"name": "Guwahati, Assam", "lat": 26.2389, "lng": 92.9375, 
     "tribes": ["Bodo", "Mising", "Karbi"], "forest_type": "Tropical Evergreen",
     "population_density": "high", "development_index": 0.47},
    {"name": "Goa", "lat": 15.2993, "lng": 74.124, 
     "tribes": ["Kunbi", "Gauda", "Velip"], "forest_type": "West Coast Tropical Evergreen",
     "population_density": "medium", "development_index": 0.68}
]

# Forest density data by region (kg/m²)
FOREST_DENSITY = {
    "Tropical Evergreen": 35.5,
    "West Coast Tropical Evergreen": 42.7,
    "Tropical Semi-Evergreen": 28.3,
    "Tropical Moist Deciduous": 22.6,
    "Tropical Dry Deciduous": 16.8
}

# Carbon sequestration rates by forest type (kg/m²/year)
CARBON_SEQUESTRATION = {
    "Tropical Evergreen": 2.8,
    "West Coast Tropical Evergreen": 3.2,
    "Tropical Semi-Evergreen": 2.3,
    "Tropical Moist Deciduous": 1.9,
    "Tropical Dry Deciduous": 1.4
}

def calculate_distance(lat1, lng1, lat2, lng2):
    """Calculate distance between two coordinates using Haversine formula"""
    R = 6371  # Earth's radius in km
    dLat = math.radians(lat2 - lat1)
    dLng = math.radians(lng2 - lng1)
    a = (math.sin(dLat/2) * math.sin(dLat/2) +
          math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
          math.sin(dLng/2) * math.sin(dLng/2))
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def find_closest_location(lat, lng):
    """Find the closest predefined location to the given coordinates"""
    closest = None
    min_distance = float('inf')
    
    for location in TEST_LOCATIONS:
        distance = calculate_distance(lat, lng, location["lat"], location["lng"])
        if distance < min_distance:
            min_distance = distance
            closest = location
            
    return closest, min_distance

def generate_analysis_data(lat, lng, radius):
    """Generate comprehensive FRA analysis data for the given location"""
    closest_location, distance = find_closest_location(lat, lng)
    
    # Base scores influenced by distance to known location
    distance_factor = min(1.0, distance / 200.0)  # Normalize distance factor
    
    # Generate realistic scores with some randomness
    forest_coverage = max(20, min(95, 75 - (distance_factor * 40) + random.randint(-15, 15)))
    tribal_status = max(15, min(90, 70 - (distance_factor * 30) + random.randint(-10, 10)))
    livelihood_potential = max(25, min(90, 65 - (distance_factor * 25) + random.randint(-10, 15)))
    community_presence = max(20, min(95, 80 - (distance_factor * 35) + random.randint(-15, 10)))
    
    # Calculate total score (weighted average)
    total_score = int((forest_coverage * 0.3 + tribal_status * 0.25 + 
                      livelihood_potential * 0.25 + community_presence * 0.2))
    
    # Determine suitability level
    if total_score >= 80:
        suitability = "very_high"
    elif total_score >= 65:
        suitability = "high"
    elif total_score >= 50:
        suitability = "medium"
    else:
        suitability = "low"
    
    # Calculate forest area based on coverage percentage
    area = math.pi * (radius ** 2)  # Area in km²
    forest_area = (forest_coverage / 100) * area
    
    # Calculate biomass and carbon data if forest type is known
    biomass = None
    carbon_sequestration = None
    if closest_location and closest_location["forest_type"] in FOREST_DENSITY:
        # Calculate biomass in metric tons
        biomass = FOREST_DENSITY[closest_location["forest_type"]] * forest_area * 1000000 / 1000
        # Calculate annual carbon sequestration in tons
        carbon_sequestration = CARBON_SEQUESTRATION[closest_location["forest_type"]] * forest_area * 1000000 / 1000
    
    # Generate land use breakdown (ensuring total adds to 100)
    base_land_use = {
        "forest": forest_coverage,
        "agriculture": random.randint(10, 30),
        "water": random.randint(2, 8),
        "settlement": random.randint(3, 10),
        "barren": random.randint(0, 5)
    }
    
    # Normalize to 100%
    total = sum(base_land_use.values())
    land_use_breakdown = {k: round((v / total) * 100, 1) for k, v in base_land_use.items()}
    
    # Generate recommendations based on suitability and location characteristics
    recommendations = generate_recommendations(suitability, closest_location, land_use_breakdown)
    
    return {
        "geographic_features": {
            "coordinates": {"latitude": lat, "longitude": lng},
            "analysis_radius_km": radius,
            "statistics": {
                "total_settlements": random.randint(5, 25),
                "tribal_villages": random.randint(3, 15),
                "forest_area_sq_km": round(forest_area, 2),
                "total_area_sq_km": round(area, 2),
                "biomass_tons": round(biomass, 2) if biomass else None,
                "carbon_sequestration_tons_year": round(carbon_sequestration, 2) if carbon_sequestration else None
            }
        },
        "fra_analysis": {
            "overall_suitability": suitability,
            "total_score": total_score,
            "component_scores": {
                "forest_coverage": forest_coverage,
                "tribal_status": tribal_status,
                "livelihood_potential": livelihood_potential,
                "community_presence": community_presence
            },
            "land_use_breakdown": land_use_breakdown,
            "region_info": {
                "region_name": closest_location["name"] if closest_location else "Unknown Region",
                "dominant_tribes": closest_location["tribes"] if closest_location else ["Various Tribal Communities"],
                "forest_type": closest_location["forest_type"] if closest_location else "Unknown",
                "development_index": closest_location["development_index"] if closest_location else 0.4,
                "distance_to_nearest_known_location_km": round(distance, 2)
            }
        },
        "recommendations": recommendations,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "api_version": "1.0",
            "data_source": "FRA Analysis API with simulated regional data"
        }
    }

def generate_recommendations(suitability, location_data, land_use):
    """Generate context-aware recommendations based on analysis results"""
    base_recommendations = {
        "immediate_actions": [
            "Conduct community meetings to understand local needs and traditional forest practices",
            "Form Village Forest Rights Committee with adequate tribal representation",
            "Document traditional forest use patterns and community dependencies"
        ],
        "infrastructure_development": [
            "Improve road connectivity to facilitate market access for forest produce",
            "Develop water conservation structures to enhance watershed management"
        ],
        "conservation_priorities": [
            "Establish community-led forest protection measures",
            "Implement sustainable harvesting practices to maintain forest health"
        ],
        "livelihood_opportunities": [
            "Promote sustainable NTFP (Non-Timber Forest Product) collection and value addition",
            "Develop eco-tourism initiatives focused on tribal culture and forest biodiversity"
        ]
    }
    
    # Add location-specific recommendations
    if location_data:
        tribe_str = ", ".join(location_data["tribes"][:2])  # Use first 2 tribes
        base_recommendations["immediate_actions"].append(
            f"Engage with {tribe_str} communities to understand their specific rights and needs"
        )
        
        base_recommendations["livelihood_opportunities"].append(
            f"Support traditional {location_data['tribes'][0]} crafts and practices for sustainable income generation"
        )
    
    # Add suitability-based recommendations
    if suitability == "very_high":
        base_recommendations["immediate_actions"].insert(
            0, "High priority area - expedite FRA recognition process with dedicated task force"
        )
        base_recommendations["conservation_priorities"].insert(
            0, "Designate as conservation priority zone with enhanced protection measures"
        )
    elif suitability == "low":
        base_recommendations["immediate_actions"].append(
            "Conduct detailed ethnographic study to document unrecognized tribal communities"
        )
        base_recommendations["infrastructure_development"].append(
            "Focus on basic amenities and infrastructure development to improve quality of life"
        )
    
    # Add land use-based recommendations
    if land_use["forest"] < 30:
        base_recommendations["conservation_priorities"].append(
            "Initiate afforestation programs with native species to improve forest cover"
        )
    
    if land_use["agriculture"] > 40:
        base_recommendations["livelihood_opportunities"].append(
            "Promote agroforestry practices to combine sustainable agriculture with forest conservation"
        )
    
    return base_recommendations

@app.route('/api/analyze', methods=['POST'])
def analyze_location():
    """API endpoint for FRA analysis"""
    try:
        # Get and validate request data
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Validate required parameters
        required_params = ['latitude', 'longitude']
        for param in required_params:
            if param not in data:
                return jsonify({"error": f"Missing required parameter: {param}"}), 400
        
        lat = data['latitude']
        lng = data['longitude']
        radius = data.get('radius_km', 2.0)
        
        # Validate parameter values
        if not isinstance(lat, (int, float)) or lat < -90 or lat > 90:
            return jsonify({"error": "Latitude must be a number between -90 and 90"}), 400
            
        if not isinstance(lng, (int, float)) or lng < -180 or lng > 180:
            return jsonify({"error": "Longitude must be a number between -180 and 180"}), 400
            
        if not isinstance(radius, (int, float)) or radius <= 0 or radius > 100:
            return jsonify({"error": "Radius must be a number between 0.1 and 100"}), 400
        
        # Generate analysis data
        analysis_data = generate_analysis_data(lat, lng, radius)
        
        return jsonify(analysis_data)
        
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "OK",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0"
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)

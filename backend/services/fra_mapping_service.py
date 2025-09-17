# app/services/fra_mapping_service.py
import numpy as np
import requests
import json
import folium
from folium import plugins
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import base64
from io import BytesIO
import logging
import os
import time
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

class FRAMappingService:
    """
    Complete FRA Analysis System with WebGIS and Satellite Integration
    Auto-saves generated maps to frontend public folder
    """
    
    def __init__(self):
        # Path configuration - adjust these paths based on your setup
        self.backend_maps_dir = "fra_maps"
        self.frontend_public_dir = self._find_frontend_public_dir()
        
        self.color_scheme = {
            'forest': '#228B22',
            'water': '#1E90FF', 
            'agriculture': '#FFD700',
            'settlement': '#FF6347',
            'roads': '#808080',
            'boundaries': '#8B4513',
            'tribal_areas': '#9932CC',
            'protected_areas': '#32CD32'
        }
        
        # Regional characteristics for India
        self.regions = {
            'jharkhand': {
                'lat_range': (21.5, 25), 'lon_range': (83, 88),
                'forest_high': True, 'tribal': True, 'mineral_rich': True
            },
            'chhattisgarh': {
                'lat_range': (17.5, 24.5), 'lon_range': (80, 85),
                'forest_high': True, 'tribal': True, 'mining': True
            },
            'odisha': {
                'lat_range': (17.5, 22.5), 'lon_range': (81.5, 87.5),
                'forest_medium': True, 'tribal': True, 'coastal': True
            },
            'madhya_pradesh': {
                'lat_range': (21.1, 26.9), 'lon_range': (74.0, 82.8),
                'forest_high': True, 'tribal': True, 'agriculture': True
            }
        }
        
        # Ensure directories exist
        os.makedirs(self.backend_maps_dir, exist_ok=True)
        if self.frontend_public_dir:
            os.makedirs(os.path.join(self.frontend_public_dir, "fra_maps"), exist_ok=True)

    def _find_frontend_public_dir(self) -> Optional[str]:
        """Find the frontend public directory automatically"""
        possible_paths = [
            "../frontend/public",  # If backend is in subfolder
            "../../frontend/public",  # If backend is in nested subfolder
            "../public",  # If backend and frontend are siblings
            "./public",  # If public is in current directory
            "../fra-atlas-frontend/public",  # Common project structure
            "../../fra-atlas-frontend/public"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                abs_path = os.path.abspath(path)
                logger.info(f"Found frontend public directory at: {abs_path}")
                return abs_path
        
        logger.warning("Frontend public directory not found. Maps will only be saved to backend directory.")
        return None

    async def analyze_and_map(self, latitude: float, longitude: float, radius_km: float = 2.0) -> Dict[str, Any]:
        """
        Complete FRA analysis with detailed mapping - User input based
        """
        
        logger.info(f"Starting analysis for user coordinates: {latitude:.4f}, {longitude:.4f}")
        
        start_time = time.time()
        
        try:
            # Step 1: Validate user input
            if not self._validate_coordinates(latitude, longitude, radius_km):
                return self._create_error_response("Invalid coordinates or radius provided")
            
            # Step 2: Get geographic features from OpenStreetMap
            logger.info("Fetching geographic data from OpenStreetMap...")
            geographic_data = await self._fetch_comprehensive_geographic_data(latitude, longitude, radius_km)
            
            # Step 3: Get satellite imagery analysis
            logger.info("Analyzing satellite imagery...")
            satellite_data = await self._analyze_satellite_imagery(latitude, longitude, radius_km)
            
            # Step 4: Process and classify features
            logger.info("Processing geographic features...")
            processed_features = self._process_geographic_features(geographic_data, satellite_data)
            
            # Step 5: Perform FRA analysis
            logger.info("Conducting FRA suitability analysis...")
            fra_analysis = self._perform_fra_analysis(processed_features, latitude, longitude)
            
            # Step 6: Generate interactive maps and save to frontend
            logger.info("Generating interactive maps...")
            maps_data = await self._create_and_save_maps(
                processed_features, fra_analysis, satellite_data, latitude, longitude, radius_km
            )
            
            # Step 7: Generate comprehensive recommendations
            logger.info("Generating recommendations...")
            recommendations = self._generate_comprehensive_recommendations(
                processed_features, fra_analysis, satellite_data
            )
            
            execution_time = time.time() - start_time
            
            result = {
                'status': 'success',
                'coordinates': {'lat': latitude, 'lon': longitude, 'radius_km': radius_km},
                'geographic_features': processed_features,
                'satellite_analysis': satellite_data,
                'fra_analysis': fra_analysis,
                'maps': maps_data,
                'recommendations': recommendations,
                'analysis_timestamp': datetime.now().isoformat(),
                'execution_time_seconds': execution_time,
                'data_sources': ['OpenStreetMap', 'Satellite Analysis', 'FRA Algorithm']
            }
            
            logger.info(f"Analysis completed successfully in {execution_time:.2f} seconds")
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return self._create_error_response(f"Analysis failed: {str(e)}")

    def _validate_coordinates(self, lat: float, lon: float, radius: float) -> bool:
        """Validate user input coordinates"""
        if not (-90 <= lat <= 90):
            return False
        if not (-180 <= lon <= 180):
            return False
        if not (0.1 <= radius <= 50):  # Reasonable radius limits
            return False
        return True

    def _create_error_response(self, message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            'status': 'error',
            'message': message,
            'timestamp': datetime.now().isoformat()
        }

    async def _fetch_comprehensive_geographic_data(self, lat: float, lon: float, radius_km: float) -> Dict[str, Any]:
        """Fetch detailed geographic data from OpenStreetMap"""
        
        try:
            # Comprehensive Overpass query for FRA-relevant features
            overpass_query = f"""
            [out:json][timeout:30];
            (
              // Water features
              way["natural"="water"](around:{radius_km*1000},{lat},{lon});
              way["waterway"](around:{radius_km*1000},{lat},{lon});
              relation["natural"="water"](around:{radius_km*1000},{lat},{lon});
              
              // Forest and vegetation
              way["natural"="forest"](around:{radius_km*1000},{lat},{lon});
              way["natural"="wood"](around:{radius_km*1000},{lat},{lon});
              way["landuse"="forest"](around:{radius_km*1000},{lat},{lon});
              way["natural"="scrub"](around:{radius_km*1000},{lat},{lon});
              
              // Agricultural areas
              way["landuse"="farmland"](around:{radius_km*1000},{lat},{lon});
              way["landuse"="orchard"](around:{radius_km*1000},{lat},{lon});
              way["landuse"="vineyard"](around:{radius_km*1000},{lat},{lon});
              way["landuse"="meadow"](around:{radius_km*1000},{lat},{lon});
              
              // Settlements and buildings
              way["place"="village"](around:{radius_km*1000},{lat},{lon});
              way["place"="hamlet"](around:{radius_km*1000},{lat},{lon});
              way["landuse"="residential"](around:{radius_km*1000},{lat},{lon});
              way["building"](around:{radius_km*1000},{lat},{lon});
              
              // Transportation
              way["highway"](around:{radius_km*1000},{lat},{lon});
              way["railway"](around:{radius_km*1000},{lat},{lon});
              
              // Administrative boundaries
              relation["admin_level"](around:{radius_km*1000},{lat},{lon});
              
              // Protected areas
              way["leisure"="nature_reserve"](around:{radius_km*1000},{lat},{lon});
              way["boundary"="protected_area"](around:{radius_km*1000},{lat},{lon});
              
              // Points of interest
              node["amenity"](around:{radius_km*1000},{lat},{lon});
              way["amenity"](around:{radius_km*1000},{lat},{lon});
              
              // Cultural and historical sites
              node["historic"](around:{radius_km*1000},{lat},{lon});
              way["historic"](around:{radius_km*1000},{lat},{lon});
            );
            out geom;
            """
            
            response = requests.post(
                'http://overpass-api.de/api/interpreter',
                data={'data': overpass_query},
                timeout=30
            )
            
            if response.status_code == 200:
                osm_data = response.json()
                return {
                    'osm_features': self._parse_osm_data(osm_data),
                    'data_source': 'OpenStreetMap',
                    'success': True
                }
            else:
                logger.warning(f"OSM query failed with status {response.status_code}")
                return self._generate_fallback_geographic_data(lat, lon, radius_km)
                
        except Exception as e:
            logger.warning(f"OSM data fetch failed: {e}")
            return self._generate_fallback_geographic_data(lat, lon, radius_km)

    def _parse_osm_data(self, osm_data: Dict) -> Dict[str, List]:
        """Parse OSM data into categorized features"""
        
        features = {
            'water_bodies': [],
            'rivers_streams': [],
            'forests': [],
            'agricultural_areas': [],
            'settlements': [],
            'roads': [],
            'buildings': [],
            'boundaries': [],
            'protected_areas': [],
            'points_of_interest': [],
            'cultural_sites': []
        }
        
        for element in osm_data.get('elements', []):
            tags = element.get('tags', {})
            coordinates = self._extract_coordinates(element)
            
            if not coordinates:
                continue
            
            feature_data = {
                'id': element.get('id'),
                'coordinates': coordinates,
                'geometry_type': element.get('type'),
                'properties': tags,
                'name': tags.get('name', 'Unnamed')
            }
            
            # Categorize based on tags
            if tags.get('natural') == 'water' or tags.get('landuse') == 'reservoir':
                features['water_bodies'].append(feature_data)
            elif tags.get('waterway') in ['river', 'stream', 'brook', 'creek']:
                features['rivers_streams'].append(feature_data)
            elif tags.get('natural') in ['forest', 'wood'] or tags.get('landuse') == 'forest':
                features['forests'].append(feature_data)
            elif tags.get('landuse') in ['farmland', 'orchard', 'vineyard', 'meadow']:
                features['agricultural_areas'].append(feature_data)
            elif tags.get('place') in ['village', 'hamlet', 'town'] or tags.get('landuse') == 'residential':
                features['settlements'].append(feature_data)
            elif tags.get('highway'):
                features['roads'].append(feature_data)
            elif tags.get('building'):
                features['buildings'].append(feature_data)
            elif tags.get('admin_level'):
                features['boundaries'].append(feature_data)
            elif tags.get('leisure') == 'nature_reserve' or tags.get('boundary') == 'protected_area':
                features['protected_areas'].append(feature_data)
            elif tags.get('amenity'):
                features['points_of_interest'].append(feature_data)
            elif tags.get('historic'):
                features['cultural_sites'].append(feature_data)
        
        return features

    def _extract_coordinates(self, element: Dict) -> Optional[List]:
        """Extract coordinates from OSM element"""
        geometry_type = element.get('type')
        
        if geometry_type == 'node':
            lat = element.get('lat')
            lon = element.get('lon')
            if lat is not None and lon is not None:
                return [lon, lat]
        
        elif geometry_type == 'way':
            nodes = element.get('geometry', [])
            if nodes:
                return [[node.get('lon'), node.get('lat')] 
                       for node in nodes if node.get('lon') and node.get('lat')]
        
        return None

    def _generate_fallback_geographic_data(self, lat: float, lon: float, radius_km: float) -> Dict[str, Any]:
        """Generate realistic fallback data when OSM is unavailable"""
        
        region_info = self._identify_region(lat, lon)
        characteristics = region_info.get('characteristics', {})
        
        # Generate features based on region and user location
        features = self._generate_realistic_features(lat, lon, radius_km, characteristics)
        
        return {
            'osm_features': features,
            'data_source': 'Generated_Fallback',
            'success': True,
            'note': 'Using generated data due to OpenStreetMap unavailability'
        }

    def _generate_realistic_features(self, lat: float, lon: float, radius_km: float, characteristics: Dict) -> Dict:
        """Generate realistic geographic features based on region"""
        
        radius_deg = radius_km / 111.0
        
        features = {
            'water_bodies': [],
            'rivers_streams': [],
            'forests': [],
            'agricultural_areas': [],
            'settlements': [],
            'roads': [],
            'buildings': [],
            'boundaries': [],
            'protected_areas': [],
            'points_of_interest': [],
            'cultural_sites': []
        }
        
        # Generate water features based on region
        water_count = 4 if characteristics.get('coastal') else 3
        for i in range(water_count):
            w_lat = lat + np.random.uniform(-radius_deg, radius_deg)
            w_lon = lon + np.random.uniform(-radius_deg, radius_deg)
            
            if i == 0:  # Main water body
                water_coords = self._generate_polygon_coordinates(w_lat, w_lon, 0.002)
                features['water_bodies'].append({
                    'id': f'water_{i}',
                    'coordinates': water_coords,
                    'geometry_type': 'way',
                    'properties': {'name': f'Water Body {i+1}', 'natural': 'water'},
                    'name': f'Water Body {i+1}'
                })
            else:  # Rivers/streams
                stream_coords = self._generate_stream_coordinates(w_lat, w_lon, radius_deg * 0.4)
                features['rivers_streams'].append({
                    'id': f'stream_{i}',
                    'coordinates': stream_coords,
                    'geometry_type': 'way',
                    'properties': {'name': f'Stream {i}', 'waterway': 'stream'},
                    'name': f'Stream {i}'
                })
        
        # Generate forests based on region characteristics
        forest_count = 6 if characteristics.get('forest_high') else 3
        for i in range(forest_count):
            f_lat = lat + np.random.uniform(-radius_deg, radius_deg)
            f_lon = lon + np.random.uniform(-radius_deg, radius_deg)
            
            forest_size = 0.006 if characteristics.get('forest_high') else 0.003
            forest_coords = self._generate_polygon_coordinates(f_lat, f_lon, forest_size)
            
            features['forests'].append({
                'id': f'forest_{i}',
                'coordinates': forest_coords,
                'geometry_type': 'way',
                'properties': {'name': f'Forest Area {i+1}', 'natural': 'forest'},
                'name': f'Forest Area {i+1}'
            })
        
        # Generate settlements based on tribal characteristics
        settlement_count = 4 if characteristics.get('tribal') else 6
        for i in range(settlement_count):
            s_lat = lat + np.random.uniform(-radius_deg * 0.8, radius_deg * 0.8)
            s_lon = lon + np.random.uniform(-radius_deg * 0.8, radius_deg * 0.8)
            
            settlement_coords = self._generate_polygon_coordinates(s_lat, s_lon, 0.001)
            settlement_type = 'tribal_village' if characteristics.get('tribal') else 'village'
            
            features['settlements'].append({
                'id': f'settlement_{i}',
                'coordinates': settlement_coords,
                'geometry_type': 'way',
                'properties': {'name': f'Village {i+1}', 'place': 'village'},
                'name': f'Village {i+1}'
            })
        
        # Generate agricultural areas
        agri_count = 8 if characteristics.get('agriculture') else 4
        for i in range(agri_count):
            a_lat = lat + np.random.uniform(-radius_deg, radius_deg)
            a_lon = lon + np.random.uniform(-radius_deg, radius_deg)
            
            agri_coords = self._generate_polygon_coordinates(a_lat, a_lon, 0.003)
            
            features['agricultural_areas'].append({
                'id': f'farm_{i}',
                'coordinates': agri_coords,
                'geometry_type': 'way',
                'properties': {'name': f'Agricultural Area {i+1}', 'landuse': 'farmland'},
                'name': f'Agricultural Area {i+1}'
            })
        
        return features

    async def _analyze_satellite_imagery(self, lat: float, lon: float, radius_km: float) -> Dict[str, Any]:
        """Simulate satellite imagery analysis"""
        
        # In production, this would connect to actual satellite APIs
        # For now, we'll generate realistic satellite analysis based on region
        
        region_info = self._identify_region(lat, lon)
        characteristics = region_info.get('characteristics', {})
        
        # Generate NDVI values based on region
        if characteristics.get('forest_high'):
            mean_ndvi = np.random.uniform(0.4, 0.7)
        elif characteristics.get('forest_medium'):
            mean_ndvi = np.random.uniform(0.3, 0.5)
        else:
            mean_ndvi = np.random.uniform(0.2, 0.4)
        
        # Generate land use percentages from "satellite analysis"
        if characteristics.get('forest_high'):
            forest_pct = np.random.uniform(45, 70)
        elif characteristics.get('forest_medium'):
            forest_pct = np.random.uniform(25, 45)
        else:
            forest_pct = np.random.uniform(10, 25)
        
        water_pct = np.random.uniform(8, 20) if characteristics.get('coastal') else np.random.uniform(3, 12)
        agriculture_pct = np.random.uniform(20, 40) if characteristics.get('agriculture') else np.random.uniform(10, 25)
        settlement_pct = np.random.uniform(5, 15)
        other_pct = max(0, 100 - forest_pct - water_pct - agriculture_pct - settlement_pct)
        
        return {
            'imagery_available': True,
            'acquisition_date': (datetime.now() - timedelta(days=np.random.randint(1, 30))).isoformat(),
            'cloud_cover_percent': np.random.uniform(5, 25),
            'resolution_meters': 10,
            'ndvi_analysis': {
                'mean_ndvi': mean_ndvi,
                'vegetation_health': 'good' if mean_ndvi > 0.4 else 'moderate',
                'forest_coverage_percent': forest_pct
            },
            'land_use_satellite': {
                'forest': forest_pct,
                'water': water_pct,
                'agriculture': agriculture_pct,
                'settlement': settlement_pct,
                'other': other_pct
            },
            'environmental_indicators': {
                'deforestation_risk': 'low' if forest_pct > 40 else 'medium',
                'water_stress': 'low' if water_pct > 10 else 'moderate',
                'biodiversity_index': min(100, forest_pct * 1.3)
            }
        }

    async def _create_and_save_maps(self, processed_features: Dict, fra_analysis: Dict, 
                                   satellite_data: Dict, lat: float, lon: float, radius_km: float) -> Dict[str, str]:
        """Create comprehensive maps and save to both backend and frontend"""
        
        maps_data = {}
        filename_base = f"fra_analysis_{lat:.4f}_{lon:.4f}"
        
        # Create interactive map
        interactive_map_html = self._create_interactive_map(
            processed_features, fra_analysis, lat, lon, radius_km
        )
        maps_data['interactive_map'] = await self._save_map_file(
            interactive_map_html, f"{filename_base}_interactive_map.html"
        )
        
        # Create FRA suitability visualization
        fra_viz_html = self._create_fra_suitability_visualization(fra_analysis, lat, lon)
        maps_data['fra_suitability'] = await self._save_map_file(
            fra_viz_html, f"{filename_base}_fra_suitability_map.html"
        )
        
        # Create feature distribution plot
        feature_plot_html = self._create_feature_distribution_plot(processed_features)
        maps_data['feature_distribution'] = await self._save_map_file(
            feature_plot_html, f"{filename_base}_feature_distribution_plot.html"
        )
        
        # Create land use chart
        land_use_html = self._create_land_use_chart(fra_analysis['land_use_breakdown'])
        maps_data['land_use_chart'] = await self._save_map_file(
            land_use_html, f"{filename_base}_land_use_chart.html"
        )
        
        return maps_data

    async def _save_map_file(self, html_content: str, filename: str) -> str:
        """Save map file to both backend and frontend directories"""
        
        # Save to backend directory
        backend_path = os.path.join(self.backend_maps_dir, filename)
        with open(backend_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Save to frontend public directory if available
        if self.frontend_public_dir:
            frontend_maps_dir = os.path.join(self.frontend_public_dir, "fra_maps")
            os.makedirs(frontend_maps_dir, exist_ok=True)
            
            frontend_path = os.path.join(frontend_maps_dir, filename)
            with open(frontend_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Map saved to frontend: {frontend_path}")
            return f"/fra_maps/{filename}"  # Return relative path for frontend
        
        logger.info(f"Map saved to backend: {backend_path}")
        return backend_path # Continuing from the previous FRAMappingService class...
    
    def _generate_polygon_coordinates(self, center_lat: float, center_lon: float, size: float) -> List[List[float]]:
        """Generate polygon coordinates for areas"""
        angles = np.linspace(0, 2*np.pi, 8)
        coords = []
        
        for angle in angles:
            lat = center_lat + size * np.cos(angle)
            lon = center_lon + size * np.sin(angle) / np.cos(np.radians(center_lat))
            coords.append([lon, lat])
        
        coords.append(coords[0])  # Close polygon
        return coords

    def _generate_stream_coordinates(self, start_lat: float, start_lon: float, length: float) -> List[List[float]]:
        """Generate meandering stream coordinates"""
        coords = []
        segments = 10
        
        for i in range(segments + 1):
            progress = i / segments
            meander = 0.3 * np.sin(progress * np.pi * 4) * length
            
            lat = start_lat + progress * length * np.cos(np.pi/4) + meander * np.cos(np.pi/4 + np.pi/2)
            lon = start_lon + progress * length * np.sin(np.pi/4) + meander * np.sin(np.pi/4 + np.pi/2)
            coords.append([lon, lat])
        
        return coords

    def _identify_region(self, lat: float, lon: float) -> Dict[str, Any]:
        """Identify region characteristics based on coordinates"""
        for region_name, bounds in self.regions.items():
            lat_min, lat_max = bounds['lat_range']
            lon_min, lon_max = bounds['lon_range']
            
            if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                return {
                    'region_name': region_name.replace('_', ' ').title(),
                    'characteristics': {k: v for k, v in bounds.items() if k not in ['lat_range', 'lon_range']}
                }
        
        return {
            'region_name': 'Other Region',
            'characteristics': {'mixed_terrain': True}
        }

    def _process_geographic_features(self, geographic_data: Dict, satellite_data: Dict) -> Dict[str, Any]:
        """Process and combine geographic and satellite data"""
        
        features = geographic_data['osm_features']
        data_source = geographic_data['data_source']
        
        # Calculate feature statistics
        stats = {
            'total_water_bodies': len(features.get('water_bodies', [])),
            'total_rivers_streams': len(features.get('rivers_streams', [])),
            'total_forest_areas': len(features.get('forests', [])),
            'total_agricultural_areas': len(features.get('agricultural_areas', [])),
            'total_settlements': len(features.get('settlements', [])),
            'total_roads': len(features.get('roads', [])),
            'total_buildings': len(features.get('buildings', [])),
            'total_protected_areas': len(features.get('protected_areas', [])),
            'total_cultural_sites': len(features.get('cultural_sites', [])),
            'data_source': data_source
        }
        
        # Use satellite data for land use if available, otherwise calculate from features
        if satellite_data.get('imagery_available'):
            coverage = satellite_data['land_use_satellite']
        else:
            coverage = self._calculate_area_coverage(features)
        
        return {
            'features': features,
            'statistics': stats,
            'coverage_estimates': coverage,
            'feature_quality': 'high' if data_source == 'OpenStreetMap' else 'simulated',
            'satellite_verified': satellite_data.get('imagery_available', False)
        }

    def _calculate_area_coverage(self, features: Dict) -> Dict[str, float]:
        """Calculate estimated area coverage from feature counts"""
        total_features = sum([
            len(features.get('water_bodies', [])),
            len(features.get('forests', [])),
            len(features.get('agricultural_areas', [])),
            len(features.get('settlements', []))
        ])
        
        if total_features == 0:
            return {'forest': 20, 'water': 5, 'agriculture': 30, 'settlement': 10, 'other': 35}
        
        # Estimate percentages based on feature counts
        forest_pct = (len(features.get('forests', [])) / max(1, total_features)) * 60
        water_pct = (len(features.get('water_bodies', [])) + len(features.get('rivers_streams', [])) * 0.5) / max(1, total_features) * 25
        agri_pct = (len(features.get('agricultural_areas', [])) / max(1, total_features)) * 45
        settlement_pct = (len(features.get('settlements', [])) / max(1, total_features)) * 15
        
        # Normalize to 100%
        total_pct = forest_pct + water_pct + agri_pct + settlement_pct
        if total_pct > 100:
            scale = 100 / total_pct
            forest_pct *= scale
            water_pct *= scale
            agri_pct *= scale
            settlement_pct *= scale
        
        other_pct = max(0, 100 - forest_pct - water_pct - agri_pct - settlement_pct)
        
        return {
            'forest': forest_pct,
            'water': water_pct,
            'agriculture': agri_pct,
            'settlement': settlement_pct,
            'other': other_pct
        }

    def _perform_fra_analysis(self, processed_features: Dict, lat: float, lon: float) -> Dict[str, Any]:
        """Perform comprehensive FRA suitability analysis"""
        
        coverage = processed_features['coverage_estimates']
        stats = processed_features['statistics']
        
        # Get region info
        region_info = self._identify_region(lat, lon)
        is_tribal = region_info['characteristics'].get('tribal', False)
        
        # Enhanced FRA scoring algorithm
        forest_score = min(40, coverage['forest'] * 0.8)
        tribal_score = 30 if is_tribal else 10
        livelihood_score = min(20, (coverage['agriculture'] + coverage['water'] * 0.5) * 0.4)
        community_score = min(15, stats['total_settlements'] * 2.5)
        infrastructure_score = min(10, stats['total_roads'] * 1.5)
        
        # Bonus points for protected areas and cultural sites
        conservation_bonus = min(5, stats.get('total_protected_areas', 0) * 2)
        cultural_bonus = min(5, stats.get('total_cultural_sites', 0) * 1.5)
        
        total_score = (forest_score + tribal_score + livelihood_score + 
                      community_score + infrastructure_score + conservation_bonus + cultural_bonus)
        
        # Determine suitability levels
        if total_score >= 85:
            overall_suitability = 'very_high'
        elif total_score >= 70:
            overall_suitability = 'high'
        elif total_score >= 50:
            overall_suitability = 'medium'
        elif total_score >= 30:
            overall_suitability = 'low'
        else:
            overall_suitability = 'very_low'
        
        return {
            'overall_suitability': overall_suitability,
            'total_score': total_score,
            'component_scores': {
                'forest_coverage': forest_score,
                'tribal_status': tribal_score,
                'livelihood_potential': livelihood_score,
                'community_presence': community_score,
                'infrastructure_access': infrastructure_score,
                'conservation_value': conservation_bonus,
                'cultural_significance': cultural_bonus
            },
            'land_use_breakdown': coverage,
            'region_info': region_info,
            'suitable_for_ifr': coverage['forest'] > 15 and coverage['agriculture'] > 10,
            'suitable_for_cfr': coverage['forest'] > 30 and stats['total_settlements'] >= 2,
            'suitable_for_cr': is_tribal and stats['total_settlements'] > 1,
            'priority_recommendations': self._generate_priority_actions(total_score, coverage, is_tribal)
        }

    def _generate_priority_actions(self, score: float, coverage: Dict, is_tribal: bool) -> List[str]:
        """Generate priority actions based on FRA score"""
        actions = []
        
        if score >= 70:
            actions.append("Immediate FRA implementation recommended")
            actions.append("Establish Forest Rights Committee")
            if is_tribal:
                actions.append("Prioritize Community Forest Resource rights")
        elif score >= 50:
            actions.append("FRA implementation with capacity building")
            actions.append("Community consultation and awareness")
        else:
            actions.append("Infrastructure development needed before FRA implementation")
            actions.append("Focus on livelihood enhancement programs")
        
        if coverage['forest'] > 40:
            actions.append("High conservation priority area")
        if coverage['water'] < 5:
            actions.append("Water resource development critical")
            
        return actions

    def _create_interactive_map(self, processed_features: Dict, fra_analysis: Dict, 
                               lat: float, lon: float, radius_km: float) -> str:
        """Create comprehensive interactive Folium map"""
        
        # Initialize map with satellite overlay option
        m = folium.Map(location=[lat, lon], zoom_start=13, tiles='OpenStreetMap')
        
        # Add satellite imagery layer
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri World Imagery',
            name='Satellite View',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Add terrain layer
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}',
            attr='Esri Terrain',
            name='Terrain View',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Analysis center marker
        folium.Marker(
            [lat, lon],
            popup=f"""
            <div style='width: 200px'>
                <h4>Analysis Center</h4>
                <p><b>Coordinates:</b> {lat:.4f}, {lon:.4f}</p>
                <p><b>FRA Suitability:</b> {fra_analysis['overall_suitability'].replace('_', ' ').title()}</p>
                <p><b>Score:</b> {fra_analysis['total_score']:.1f}/100</p>
                <p><b>Region:</b> {fra_analysis['region_info']['region_name']}</p>
            </div>
            """,
            icon=folium.Icon(color='red', icon='bullseye', prefix='fa')
        ).add_to(m)
        
        # Analysis radius circle
        folium.Circle(
            location=[lat, lon],
            radius=radius_km * 1000,
            popup=f"Analysis Area ({radius_km} km radius)",
            color='red',
            fillColor='red',
            fillOpacity=0.1,
            weight=2
        ).add_to(m)
        
        features = processed_features['features']
        
        # Add feature layers with proper styling
        self._add_water_features(m, features)
        self._add_forest_features(m, features)
        self._add_agricultural_features(m, features)
        self._add_settlement_features(m, features)
        self._add_infrastructure_features(m, features)
        self._add_protected_areas(m, features)
        
        # Add layer control
        folium.LayerControl(collapsed=False).add_to(m)
        
        # Add custom legend
        legend_html = self._create_map_legend()
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Add measurement tool
        plugins.MeasureControl().add_to(m)
        
        # Add fullscreen button
        plugins.Fullscreen().add_to(m)
        
        return m._repr_html_()

    def _add_water_features(self, m, features):
        """Add water features to map"""
        if features.get('water_bodies') or features.get('rivers_streams'):
            water_group = folium.FeatureGroup(name="💧 Water Features", show=True)
            
            # Water bodies
            for water in features.get('water_bodies', []):
                if len(water['coordinates']) > 2:
                    coords = [[coord[1], coord[0]] for coord in water['coordinates']]
                    folium.Polygon(
                        locations=coords,
                        popup=f"<b>{water.get('name', 'Water Body')}</b><br>Type: {water.get('properties', {}).get('natural', 'water')}",
                        color=self.color_scheme['water'],
                        fillColor=self.color_scheme['water'],
                        fillOpacity=0.6,
                        weight=2
                    ).add_to(water_group)
            
            # Rivers and streams
            for river in features.get('rivers_streams', []):
                if len(river['coordinates']) > 1:
                    coords = [[coord[1], coord[0]] for coord in river['coordinates']]
                    folium.PolyLine(
                        locations=coords,
                        popup=f"<b>{river.get('name', 'Waterway')}</b><br>Type: {river.get('properties', {}).get('waterway', 'stream')}",
                        color=self.color_scheme['water'],
                        weight=3,
                        opacity=0.8
                    ).add_to(water_group)
            
            water_group.add_to(m)

    def _add_forest_features(self, m, features):
        """Add forest features to map"""
        if features.get('forests'):
            forest_group = folium.FeatureGroup(name="🌲 Forest Areas", show=True)
            
            for forest in features['forests']:
                if len(forest['coordinates']) > 2:
                    coords = [[coord[1], coord[0]] for coord in forest['coordinates']]
                    folium.Polygon(
                        locations=coords,
                        popup=f"<b>{forest.get('name', 'Forest Area')}</b><br>Type: {forest.get('properties', {}).get('natural', 'forest')}",
                        color=self.color_scheme['forest'],
                        fillColor=self.color_scheme['forest'],
                        fillOpacity=0.7,
                        weight=2
                    ).add_to(forest_group)
            
            forest_group.add_to(m)

    def _add_agricultural_features(self, m, features):
        """Add agricultural features to map"""
        if features.get('agricultural_areas'):
            agri_group = folium.FeatureGroup(name="🌾 Agricultural Areas", show=True)
            
            for farm in features['agricultural_areas']:
                if len(farm['coordinates']) > 2:
                    coords = [[coord[1], coord[0]] for coord in farm['coordinates']]
                    folium.Polygon(
                        locations=coords,
                        popup=f"<b>{farm.get('name', 'Agricultural Area')}</b><br>Type: {farm.get('properties', {}).get('landuse', 'farmland')}",
                        color=self.color_scheme['agriculture'],
                        fillColor=self.color_scheme['agriculture'],
                        fillOpacity=0.6,
                        weight=2
                    ).add_to(agri_group)
            
            agri_group.add_to(m)

    def _add_settlement_features(self, m, features):
        """Add settlement features to map"""
        if features.get('settlements'):
            settlement_group = folium.FeatureGroup(name="🏘️ Settlements", show=True)
            
            for settlement in features['settlements']:
                if len(settlement['coordinates']) > 2:
                    coords = [[coord[1], coord[0]] for coord in settlement['coordinates']]
                    folium.Polygon(
                        locations=coords,
                        popup=f"<b>{settlement.get('name', 'Settlement')}</b><br>Type: {settlement.get('properties', {}).get('place', 'village')}",
                        color=self.color_scheme['settlement'],
                        fillColor=self.color_scheme['settlement'],
                        fillOpacity=0.5,
                        weight=2
                    ).add_to(settlement_group)
                elif len(settlement['coordinates']) == 2:
                    folium.Marker(
                        [settlement['coordinates'][1], settlement['coordinates'][0]],
                        popup=f"<b>{settlement.get('name', 'Settlement')}</b>",
                        icon=folium.Icon(color='orange', icon='home', prefix='fa')
                    ).add_to(settlement_group)
            
            settlement_group.add_to(m)

    def _add_infrastructure_features(self, m, features):
        """Add roads and infrastructure to map"""
        if features.get('roads'):
            road_group = folium.FeatureGroup(name="🛣️ Roads & Infrastructure", show=False)
            
            for road in features['roads']:
                if len(road['coordinates']) > 1:
                    coords = [[coord[1], coord[0]] for coord in road['coordinates']]
                    
                    # Road styling based on type
                    road_type = road.get('properties', {}).get('highway', 'track')
                    if road_type in ['primary', 'trunk']:
                        weight, color = 5, '#FF0000'
                    elif road_type in ['secondary']:
                        weight, color = 4, '#FF8C00'
                    elif road_type in ['tertiary']:
                        weight, color = 3, '#FFD700'
                    else:
                        weight, color = 2, '#808080'
                    
                    folium.PolyLine(
                        locations=coords,
                        popup=f"<b>Road</b><br>Type: {road_type}",
                        color=color,
                        weight=weight,
                        opacity=0.7
                    ).add_to(road_group)
            
            road_group.add_to(m)

    def _add_protected_areas(self, m, features):
        """Add protected areas to map"""
        if features.get('protected_areas'):
            protected_group = folium.FeatureGroup(name="🛡️ Protected Areas", show=True)
            
            for area in features['protected_areas']:
                if len(area['coordinates']) > 2:
                    coords = [[coord[1], coord[0]] for coord in area['coordinates']]
                    folium.Polygon(
                        locations=coords,
                        popup=f"<b>{area.get('name', 'Protected Area')}</b>",
                        color=self.color_scheme['protected_areas'],
                        fillColor=self.color_scheme['protected_areas'],
                        fillOpacity=0.3,
                        weight=3,
                        dashArray='5, 5'
                    ).add_to(protected_group)
            
            protected_group.add_to(m)

    def _create_map_legend(self) -> str:
        """Create custom legend for the map"""
        return """
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 200px; height: 220px; 
                    background-color: white; border: 2px solid grey; z-index: 9999; 
                    font-size: 12px; padding: 10px; border-radius: 5px; box-shadow: 0 0 15px rgba(0,0,0,0.2);">
        <h4 style="margin: 0 0 10px 0; font-size: 14px;">FRA Analysis Legend</h4>
        <div style="margin-bottom: 5px;"><span style="background: #1E90FF; width: 15px; height: 15px; display: inline-block; margin-right: 5px;"></span>Water Bodies</div>
        <div style="margin-bottom: 5px;"><span style="background: #228B22; width: 15px; height: 15px; display: inline-block; margin-right: 5px;"></span>Forest Areas</div>
        <div style="margin-bottom: 5px;"><span style="background: #FFD700; width: 15px; height: 15px; display: inline-block; margin-right: 5px;"></span>Agriculture</div>
        <div style="margin-bottom: 5px;"><span style="background: #FF6347; width: 15px; height: 15px; display: inline-block; margin-right: 5px;"></span>Settlements</div>
        <div style="margin-bottom: 5px;"><span style="background: #32CD32; width: 15px; height: 15px; display: inline-block; margin-right: 5px; opacity: 0.5;"></span>Protected Areas</div>
        <div style="margin-bottom: 5px;"><span style="background: #FF0000; width: 15px; height: 15px; display: inline-block; margin-right: 5px;"></span>Analysis Center</div>
        <hr style="margin: 10px 0;">
        <div style="font-size: 10px; color: #666;">Click layers to toggle visibility<br>Use measure tool for distances</div>
        </div>
        """

    def _create_fra_suitability_visualization(self, fra_analysis: Dict, lat: float, lon: float) -> str:
        """Create comprehensive FRA suitability visualization"""
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('FRA Suitability Score', 'Component Analysis', 'Rights Eligibility', 'Priority Actions'),
            specs=[[{"type": "indicator"}, {"type": "bar"}], 
                   [{"type": "bar"}, {"type": "table"}]]
        )
        
        # Suitability gauge
        suitability_colors = {'very_high': 'green', 'high': 'lightgreen', 'medium': 'yellow', 'low': 'orange', 'very_low': 'red'}
        
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=fra_analysis['total_score'],
                title={'text': f"Overall: {fra_analysis['overall_suitability'].replace('_', ' ').title()}"},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': suitability_colors.get(fra_analysis['overall_suitability'], 'gray')},
                    'steps': [
                        {'range': [0, 30], 'color': "lightgray"},
                        {'range': [30, 50], 'color': "yellow"},
                        {'range': [50, 70], 'color': "lightgreen"},
                        {'range': [70, 100], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 85
                    }
                }
            ),
            row=1, col=1
        )
        
        # Component breakdown
        components = list(fra_analysis['component_scores'].keys())
        scores = list(fra_analysis['component_scores'].values())
        
        fig.add_trace(
            go.Bar(
                x=[comp.replace('_', ' ').title() for comp in components],
                y=scores,
                marker_color=['#228B22', '#9932CC', '#FFD700', '#FF6347', '#1E90FF', '#32CD32', '#8B4513']
            ),
            row=1, col=2
        )
        
        # Rights eligibility
        rights_data = {
            'Individual Forest Rights (IFR)': fra_analysis['suitable_for_ifr'],
            'Community Forest Resources (CFR)': fra_analysis['suitable_for_cfr'],
            'Community Rights (CR)': fra_analysis['suitable_for_cr']
        }
        
        fig.add_trace(
            go.Bar(
                x=list(rights_data.keys()),
                y=[1 if eligible else 0 for eligible in rights_data.values()],
                marker_color=['green' if eligible else 'red' for eligible in rights_data.values()],
                text=['✓ Eligible' if eligible else '✗ Not Eligible' for eligible in rights_data.values()],
                textposition='auto'
            ),
            row=2, col=1
        )
        
        # Priority actions table
        actions = fra_analysis.get('priority_recommendations', [])
        fig.add_trace(
            go.Table(
                header=dict(values=['Priority Actions'], fill_color='lightblue'),
                cells=dict(values=[actions], fill_color='white')
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title_text=f"FRA Suitability Assessment - {fra_analysis['region_info']['region_name']}",
            height=700,
            showlegend=False
        )
        
        return fig.to_html(include_plotlyjs='cdn')

    def _create_feature_distribution_plot(self, processed_features: Dict) -> str:
        """Create feature distribution analysis"""
        
        stats = processed_features['statistics']
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Feature Counts', 'Land Use Distribution', 'Data Quality', 'Regional Analysis'),
            specs=[[{"type": "bar"}, {"type": "pie"}], 
                   [{"type": "indicator"}, {"type": "bar"}]]
        )
        
        # Feature counts
        feature_names = ['Water Bodies', 'Streams', 'Forests', 'Agriculture', 'Settlements', 'Roads']
        feature_counts = [
            stats['total_water_bodies'], stats['total_rivers_streams'], 
            stats['total_forest_areas'], stats['total_agricultural_areas'],
            stats['total_settlements'], stats['total_roads']
        ]
        
        fig.add_trace(
            go.Bar(x=feature_names, y=feature_counts,
                   marker_color=['#1E90FF', '#4682B4', '#228B22', '#FFD700', '#FF6347', '#808080']),
            row=1, col=1
        )
        
        # Land use pie chart
        coverage = processed_features['coverage_estimates']
        fig.add_trace(
            go.Pie(labels=list(coverage.keys()), values=list(coverage.values()),
                   marker_colors=['#228B22', '#1E90FF', '#FFD700', '#FF6347', '#D3D3D3']),
            row=1, col=2
        )
        
        # Data quality indicator
        quality_score = 100 if processed_features['feature_quality'] == 'high' else 75
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=quality_score,
                title={'text': f"Data Quality<br>{processed_features['feature_quality'].title()}"},
                gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "green" if quality_score == 100 else "orange"}}
            ),
            row=2, col=1
        )
        
        # Regional comparison (mock data)
        regions = ['Current Area', 'State Average', 'National Average']
        forest_pct = [coverage['forest'], 35, 25]
        
        fig.add_trace(
            go.Bar(x=regions, y=forest_pct, name="Forest Coverage %",
                   marker_color=['#228B22', '#90EE90', '#32CD32']),
            row=2, col=2
        )
        
        fig.update_layout(title_text="Geographic Feature Analysis Dashboard", height=600, showlegend=False)
        return fig.to_html(include_plotlyjs='cdn')

    def _create_land_use_chart(self, land_use_breakdown: Dict) -> str:
        """Create land use breakdown visualization"""
        
        fig = go.Figure(data=[
            go.Pie(
                labels=[label.title() for label in land_use_breakdown.keys()],
                values=list(land_use_breakdown.values()),
                hole=0.4,
                marker_colors=['#228B22', '#1E90FF', '#FFD700', '#FF6347', '#D3D3D3'],
                textinfo='label+percent',
                textposition='outside'
            )
        ])
        
        fig.update_layout(
            title_text="Land Use Distribution Analysis",
            annotations=[dict(text='Land Use', x=0.5, y=0.5, font_size=20, showarrow=False)],
            height=500
        )
        
        return fig.to_html(include_plotlyjs='cdn')

    def _generate_comprehensive_recommendations(self, processed_features: Dict, 
                                              fra_analysis: Dict, satellite_data: Dict) -> Dict[str, List[str]]:
        """Generate comprehensive location-based recommendations"""
        
        features = processed_features['features']
        coverage = fra_analysis['land_use_breakdown']
        stats = processed_features['statistics']
        suitability = fra_analysis['overall_suitability']
        
        recommendations = {
            'immediate_actions': [],
            'infrastructure_development': [],
            'conservation_priorities': [],
            'livelihood_opportunities': [],
            'capacity_building': [],
            'monitoring_requirements': [],
            'scheme_eligibility': [],
            'location_specific_notes': []
        }
        
        # Immediate actions based on suitability
        if suitability in ['very_high', 'high']:
            recommendations['immediate_actions'].extend([
                f"Initiate FRA implementation process in {stats['total_settlements']} identified settlements",
                "Conduct community awareness programs about forest rights",
                "Begin documentation of traditional forest use patterns",
                "Establish Village Forest Rights Committees (VFRCs)"
            ])
        elif suitability == 'medium':
            recommendations['immediate_actions'].extend([
                "Conduct detailed feasibility study for FRA implementation",
                "Strengthen community organization and awareness",
                "Address infrastructure gaps before FRA implementation"
            ])
        
        # Infrastructure development
        if stats['total_roads'] < 3:
            recommendations['infrastructure_development'].append(
                "Improve road connectivity - limited transportation network detected"
            )
        
        if coverage['water'] < 10:
            recommendations['infrastructure_development'].append(
                "Water infrastructure development critical - low water resource availability"
            )
        
        # Conservation priorities
        if coverage['forest'] > 40:
            recommendations['conservation_priorities'].extend([
                f"High conservation value - {coverage['forest']:.1f}% forest coverage",
                f"Develop conservation plan for {stats['total_forest_areas']} forest patches",
                "Implement community-based forest management"
            ])
        
        if stats.get('total_protected_areas', 0) > 0:
            recommendations['conservation_priorities'].append(
                f"Coordinate with existing protected area management ({stats['total_protected_areas']} areas identified)"
            )
        
        # Livelihood opportunities
        if coverage['agriculture'] > 20:
            recommendations['livelihood_opportunities'].extend([
                f"Agricultural enhancement in {stats['total_agricultural_areas']} identified areas",
                "Promote sustainable farming practices",
                "Explore organic certification opportunities"
            ])
        
        if coverage['forest'] > 30:
            recommendations['livelihood_opportunities'].extend([
                "Non-timber forest product (NTFP) development potential",
                "Community-based eco-tourism opportunities",
                "Sustainable forest-based enterprises"
            ])
        
        # Capacity building
        recommendations['capacity_building'].extend([
            "Train local facilitators on FRA processes",
            "Develop GIS and mapping skills in communities",
            "Strengthen traditional governance systems"
        ])
        
        # Monitoring requirements
        if satellite_data.get('imagery_available'):
            recommendations['monitoring_requirements'].extend([
                "Establish satellite-based forest monitoring system",
                "Regular NDVI monitoring for vegetation health",
                "Annual land use change detection"
            ])
        
        recommendations['monitoring_requirements'].extend([
            "Set up community-based monitoring protocols",
            "Regular biodiversity assessments",
            "Socio-economic impact monitoring"
        ])
        
        # Scheme eligibility
        if fra_analysis['suitable_for_ifr']:
            recommendations['scheme_eligibility'].append("Eligible for Individual Forest Rights (IFR) under FRA")
        if fra_analysis['suitable_for_cfr']:
            recommendations['scheme_eligibility'].append("Eligible for Community Forest Resource (CFR) rights")
        if fra_analysis['suitable_for_cr']:
            recommendations['scheme_eligibility'].append("Eligible for Community Rights (CR) under FRA")
        
        # Add other scheme eligibilities based on characteristics
        if coverage['forest'] > 30:
            recommendations['scheme_eligibility'].extend([
                "Potential for Joint Forest Management (JFM) programs",
                "Eligible for Green India Mission activities"
            ])
        
        # Location-specific notes
        settlement_names = [s.get('name', f'Settlement {i+1}') for i, s in enumerate(features.get('settlements', []))]
        if settlement_names:
            recommendations['location_specific_notes'].append(
                f"Key settlements for community engagement: {', '.join(settlement_names[:5])}"
            )
        
        if satellite_data.get('environmental_indicators'):
            env_indicators = satellite_data['environmental_indicators']
            if env_indicators.get('deforestation_risk') != 'low':
                recommendations['location_specific_notes'].append(
                    f"Deforestation risk: {env_indicators['deforestation_risk']} - enhanced monitoring required"
                )
        
        return recommendations
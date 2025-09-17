#
# ==============================================================================
#  Original Code (Your classes and functions)
# ==============================================================================
#

import numpy as np
import requests
import json
import folium
from folium import plugins
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import base64
from io import BytesIO
import matplotlib.pyplot as plt

# Added for FastAPI integration
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

class FRAMappingSystem:
    """
    FRA Analysis System with comprehensive map rendering capabilities
    Shows actual locations of lakes, rivers, forests, settlements, etc.
    """
    
    def __init__(self):
        # Initialize base FRA analysis system
        self.analysis_data = {}
        self.map_layers = {}
        self.color_scheme = {
            'forest': '#228B22',
            'water': '#1E90FF', 
            'agriculture': '#FFD700',
            'settlement': '#FF6347',
            'roads': '#808080',
            'boundaries': '#8B4513',
            'tribal_areas': '#9932CC'
        }
        
        # Geographic regions for fallback
        self.regions = {
            'jharkhand': {'lat_range': (21.5, 25), 'lon_range': (83, 88), 'forest_high': True, 'tribal': True},
            'chhattisgarh': {'lat_range': (17.5, 24.5), 'lon_range': (80, 85), 'forest_high': True, 'tribal': True},
            'odisha': {'lat_range': (17.5, 22.5), 'lon_range': (81.5, 87.5), 'forest_medium': True, 'tribal': True}
        }

    def analyze_and_map(self, latitude: float, longitude: float, radius_km: float = 2.0) -> Dict:
        """
        Complete FRA analysis with detailed mapping
        """
        
        print(f"🗺️ Analyzing and mapping area: {latitude:.4f}, {longitude:.4f}")
        
        # Step 1: Get geographic features from multiple sources
        print("📍 Fetching geographic data...")
        geographic_data = self._fetch_comprehensive_geographic_data(latitude, longitude, radius_km)
        
        # Step 2: Process and classify features
        print("🌍 Processing geographic features...")
        processed_features = self._process_geographic_features(geographic_data)
        
        # Step 3: Perform FRA analysis
        print("🌲 Conducting FRA suitability analysis...")
        fra_analysis = self._perform_fra_analysis(processed_features, latitude, longitude)
        
        # Step 4: Generate interactive maps
        print("🗺️ Generating interactive maps...")
        maps_data = self._create_comprehensive_maps(processed_features, fra_analysis, latitude, longitude, radius_km)
        
        # Step 5: Generate scheme recommendations with locations
        print("📋 Creating location-based recommendations...")
        recommendations = self._generate_location_based_recommendations(processed_features, fra_analysis)
        
        result = {
            'status': 'success',
            'coordinates': {'lat': latitude, 'lon': longitude, 'radius_km': radius_km},
            'geographic_features': processed_features,
            'fra_analysis': fra_analysis,
            'maps': maps_data,
            'recommendations': recommendations,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        print("✅ Analysis and mapping complete!")
        return result

    def _fetch_comprehensive_geographic_data(self, lat: float, lon: float, radius_km: float) -> Dict:
        """Fetch detailed geographic data from multiple sources"""
        
        geographic_data = {
            'osm_features': None,
            'simulated_features': None,
            'data_sources': []
        }
        
        # Try OpenStreetMap first
        try:
            print("   Attempting OpenStreetMap query...")
            osm_data = self._query_osm_detailed(lat, lon, radius_km)
            if osm_data:
                geographic_data['osm_features'] = osm_data
                geographic_data['data_sources'].append('OpenStreetMap')
                print("   ✅ OpenStreetMap data retrieved")
            else:
                print("   ⚠️ OpenStreetMap query failed")
        except Exception as e:
            print(f"   ❌ OSM error: {str(e)[:50]}...")
        
        # Fallback to simulated geographic data based on region
        if not geographic_data['osm_features']:
            print("   🔄 Using geographic simulation...")
            simulated_data = self._simulate_detailed_geography(lat, lon, radius_km)
            geographic_data['simulated_features'] = simulated_data
            geographic_data['data_sources'].append('Geographic_Simulation')
            print("   ✅ Geographic simulation complete")
        
        return geographic_data

    def _query_osm_detailed(self, lat: float, lon: float, radius_km: float) -> Optional[Dict]:
        """Detailed OpenStreetMap query for mapping features"""
        
        try:
            # Comprehensive Overpass query for mapping
            overpass_query = f"""
            [out:json][timeout:25];
            (
              // Water features
              way["natural"="water"](around:{radius_km*1000},{lat},{lon});
              way["waterway"](around:{radius_km*1000},{lat},{lon});
              relation["natural"="water"](around:{radius_km*1000},{lat},{lon});
              
              // Forest and vegetation
              way["natural"="forest"](around:{radius_km*1000},{lat},{lon});
              way["natural"="wood"](around:{radius_km*1000},{lat},{lon});
              way["landuse"="forest"](around:{radius_km*1000},{lat},{lon});
              
              // Agricultural areas
              way["landuse"="farmland"](around:{radius_km*1000},{lat},{lon});
              way["landuse"="orchard"](around:{radius_km*1000},{lat},{lon});
              way["landuse"="vineyard"](around:{radius_km*1000},{lat},{lon});
              
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
              
              // Points of interest
              node["amenity"](around:{radius_km*1000},{lat},{lon});
              way["amenity"](around:{radius_km*1000},{lat},{lon});
            );
            out geom;
            """
            
            response = requests.post(
                'https://overpass-api.de/api/interpreter',
                data={'data': overpass_query},
                timeout=25
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_osm_for_mapping(data)
            
            return None
            
        except Exception as e:
            return None

    def _parse_osm_for_mapping(self, osm_data: Dict) -> Dict:
        """Parse OSM data into mappable features with coordinates"""
        
        features = {
            'water_bodies': [],
            'rivers_streams': [],
            'forests': [],
            'agricultural_areas': [],
            'settlements': [],
            'roads': [],
            'buildings': [],
            'boundaries': [],
            'points_of_interest': []
        }
        
        for element in osm_data.get('elements', []):
            tags = element.get('tags', {})
            geometry_type = element.get('type')
            
            # Extract coordinates based on geometry type
            coordinates = self._extract_coordinates(element)
            if not coordinates:
                continue
            
            # Categorize features
            feature_data = {
                'id': element.get('id'),
                'coordinates': coordinates,
                'geometry_type': geometry_type,
                'properties': tags
            }
            
            # Water features
            if tags.get('natural') == 'water' or tags.get('landuse') == 'reservoir':
                feature_data['feature_type'] = 'lake' if 'lake' in tags.get('name', '').lower() else 'water_body'
                features['water_bodies'].append(feature_data)
            
            elif tags.get('waterway') in ['river', 'stream', 'brook', 'creek']:
                feature_data['feature_type'] = tags.get('waterway')
                features['rivers_streams'].append(feature_data)
            
            # Forest areas
            elif tags.get('natural') in ['forest', 'wood'] or tags.get('landuse') == 'forest':
                feature_data['feature_type'] = 'forest'
                features['forests'].append(feature_data)
            
            # Agricultural areas
            elif tags.get('landuse') in ['farmland', 'orchard', 'vineyard', 'meadow']:
                feature_data['feature_type'] = tags.get('landuse')
                features['agricultural_areas'].append(feature_data)
            
            # Settlements
            elif tags.get('place') in ['village', 'hamlet', 'town'] or tags.get('landuse') == 'residential':
                feature_data['feature_type'] = tags.get('place', 'residential')
                feature_data['name'] = tags.get('name', 'Unnamed settlement')
                features['settlements'].append(feature_data)
            
            # Roads
            elif tags.get('highway'):
                feature_data['feature_type'] = tags.get('highway')
                feature_data['name'] = tags.get('name', f"{tags.get('highway')} road")
                features['roads'].append(feature_data)
            
            # Buildings
            elif tags.get('building'):
                feature_data['feature_type'] = tags.get('building')
                features['buildings'].append(feature_data)
            
            # Administrative boundaries
            elif tags.get('admin_level'):
                feature_data['feature_type'] = f"admin_level_{tags.get('admin_level')}"
                feature_data['name'] = tags.get('name', 'Administrative boundary')
                features['boundaries'].append(feature_data)
            
            # Points of interest
            elif tags.get('amenity'):
                feature_data['feature_type'] = tags.get('amenity')
                feature_data['name'] = tags.get('name', tags.get('amenity'))
                features['points_of_interest'].append(feature_data)
        
        return features

    def _extract_coordinates(self, element: Dict) -> Optional[List]:
        """Extract coordinates from OSM element"""
        
        geometry_type = element.get('type')
        
        if geometry_type == 'node':
            lat = element.get('lat')
            lon = element.get('lon')
            if lat is not None and lon is not None:
                return [lon, lat]  # [longitude, latitude] for GeoJSON
        
        elif geometry_type == 'way':
            nodes = element.get('geometry', [])
            if nodes:
                return [[node.get('lon'), node.get('lat')] for node in nodes if node.get('lon') and node.get('lat')]
        
        elif geometry_type == 'relation':
            # For relations, we'd need to process members, simplified here
            return None
        
        return None

    def _simulate_detailed_geography(self, lat: float, lon: float, radius_km: float) -> Dict:
        """Generate realistic geographic features when real data is unavailable"""
        
        # Identify region characteristics
        region_info = self._identify_region(lat, lon)
        characteristics = region_info.get('characteristics', {})
        
        # Generate realistic features based on region
        features = {
            'water_bodies': [],
            'rivers_streams': [],
            'forests': [],
            'agricultural_areas': [],
            'settlements': [],
            'roads': [],
            'buildings': [],
            'boundaries': [],
            'points_of_interest': []
        }
        
        # Calculate area bounds
        radius_deg = radius_km / 111.0  # Approximate conversion
        bounds = {
            'north': lat + radius_deg,
            'south': lat - radius_deg,
            'east': lon + radius_deg,
            'west': lon - radius_deg
        }
        
        # Generate water features
        water_count = 3 if characteristics.get('water_rich') else 2
        for i in range(water_count):
            # Random location within bounds
            w_lat = lat + (np.random.random() - 0.5) * radius_deg * 1.5
            w_lon = lon + (np.random.random() - 0.5) * radius_deg * 1.5
            
            if i == 0:  # Main water body (lake/pond)
                # Generate polygon for water body
                water_coords = self._generate_polygon_coordinates(w_lat, w_lon, 0.002)
                features['water_bodies'].append({
                    'id': f'sim_water_{i}',
                    'coordinates': water_coords,
                    'geometry_type': 'way',
                    'feature_type': 'pond' if radius_km < 1 else 'lake',
                    'properties': {'name': f'Water Body {i+1}', 'natural': 'water'}
                })
            else:  # Rivers/streams
                # Generate line for river/stream
                stream_coords = self._generate_stream_coordinates(w_lat, w_lon, radius_deg * 0.3)
                features['rivers_streams'].append({
                    'id': f'sim_stream_{i}',
                    'coordinates': stream_coords,
                    'geometry_type': 'way',
                    'feature_type': 'stream',
                    'properties': {'name': f'Stream {i}', 'waterway': 'stream'}
                })
        
        # Generate forest areas
        if characteristics.get('forest_high') or characteristics.get('forest_medium'):
            forest_count = 4 if characteristics.get('forest_high') else 2
            for i in range(forest_count):
                f_lat = lat + (np.random.random() - 0.5) * radius_deg * 1.2
                f_lon = lon + (np.random.random() - 0.5) * radius_deg * 1.2
                
                forest_size = 0.005 if characteristics.get('forest_high') else 0.003
                forest_coords = self._generate_polygon_coordinates(f_lat, f_lon, forest_size)
                
                features['forests'].append({
                    'id': f'sim_forest_{i}',
                    'coordinates': forest_coords,
                    'geometry_type': 'way',
                    'feature_type': 'forest',
                    'properties': {'name': f'Forest Area {i+1}', 'natural': 'forest'}
                })
        
        # Generate agricultural areas
        if characteristics.get('agriculture', True): # Default to true for simulation
            agri_count = 5
            for i in range(agri_count):
                a_lat = lat + (np.random.random() - 0.5) * radius_deg * 1.0
                a_lon = lon + (np.random.random() - 0.5) * radius_deg * 1.0
                
                agri_coords = self._generate_polygon_coordinates(a_lat, a_lon, 0.003)
                
                features['agricultural_areas'].append({
                    'id': f'sim_farm_{i}',
                    'coordinates': agri_coords,
                    'geometry_type': 'way',
                    'feature_type': 'farmland',
                    'properties': {'name': f'Farm {i+1}', 'landuse': 'farmland'}
                })
        
        # Generate settlements
        settlement_count = 3 if characteristics.get('tribal') else 5
        for i in range(settlement_count):
            s_lat = lat + (np.random.random() - 0.5) * radius_deg * 0.8
            s_lon = lon + (np.random.random() - 0.5) * radius_deg * 0.8
            
            settlement_coords = self._generate_polygon_coordinates(s_lat, s_lon, 0.001)
            
            features['settlements'].append({
                'id': f'sim_settlement_{i}',
                'coordinates': settlement_coords,
                'geometry_type': 'way',
                'feature_type': 'village' if characteristics.get('tribal') else 'hamlet',
                'properties': {'name': f'Village {i+1}', 'place': 'village'},
                'name': f'Village {i+1}'
            })
        
        # Generate road network
        road_count = 4
        for i in range(road_count):
            road_coords = self._generate_road_coordinates(lat, lon, radius_deg, i)
            
            road_types = ['primary', 'secondary', 'tertiary', 'track']
            road_type = road_types[i % len(road_types)]
            
            features['roads'].append({
                'id': f'sim_road_{i}',
                'coordinates': road_coords,
                'geometry_type': 'way',
                'feature_type': road_type,
                'properties': {'highway': road_type},
                'name': f'{road_type.title()} Road'
            })
        
        return features

    def _generate_polygon_coordinates(self, center_lat: float, center_lon: float, size: float) -> List[List[float]]:
        """Generate polygon coordinates for areas"""
        
        angles = np.linspace(0, 2*np.pi, 8)  # Octagon
        coords = []
        
        for angle in angles:
            lat = center_lat + size * np.cos(angle)
            lon = center_lon + size * np.sin(angle) / np.cos(np.radians(center_lat))
            coords.append([lon, lat])
        
        # Close the polygon
        coords.append(coords[0])
        
        return coords

    def _generate_stream_coordinates(self, start_lat: float, start_lon: float, length: float) -> List[List[float]]:
        """Generate meandering stream coordinates"""
        
        coords = []
        segments = 10
        
        for i in range(segments + 1):
            progress = i / segments
            
            # Add some meandering
            meander = 0.3 * np.sin(progress * np.pi * 4) * length
            
            lat = start_lat + progress * length * np.cos(np.pi/4) + meander * np.cos(np.pi/4 + np.pi/2)
            lon = start_lon + progress * length * np.sin(np.pi/4) + meander * np.sin(np.pi/4 + np.pi/2)
            
            coords.append([lon, lat])
        
        return coords

    def _generate_road_coordinates(self, center_lat: float, center_lon: float, radius_deg: float, road_index: int) -> List[List[float]]:
        """Generate road network coordinates"""
        
        coords = []
        
        # Create roads radiating from center and some connecting roads
        if road_index == 0:  # North-South road
            start_lat = center_lat - radius_deg * 0.8
            end_lat = center_lat + radius_deg * 0.8
            for lat in np.linspace(start_lat, end_lat, 10):
                coords.append([center_lon, lat])
        
        elif road_index == 1:  # East-West road
            start_lon = center_lon - radius_deg * 0.8
            end_lon = center_lon + radius_deg * 0.8
            for lon in np.linspace(start_lon, end_lon, 10):
                coords.append([lon, center_lat])
        
        elif road_index == 2:  # Diagonal road NE-SW
            for i in range(10):
                progress = i / 9
                lat = center_lat + (progress - 0.5) * radius_deg * 1.2
                lon = center_lon + (progress - 0.5) * radius_deg * 1.2
                coords.append([lon, lat])
        
        else:  # Curved connecting road
            angles = np.linspace(0, np.pi, 8)
            for angle in angles:
                lat = center_lat + radius_deg * 0.6 * np.sin(angle)
                lon = center_lon + radius_deg * 0.6 * np.cos(angle)
                coords.append([lon, lat])
        
        return coords

    def _identify_region(self, lat: float, lon: float) -> Dict:
        """Identify region characteristics"""
        
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

    def _process_geographic_features(self, geographic_data: Dict) -> Dict:
        """Process and standardize geographic features for analysis"""
        
        # Use OSM data if available, otherwise use simulated data
        if geographic_data['osm_features']:
            features = geographic_data['osm_features']
            data_source = 'OpenStreetMap'
        else:
            features = geographic_data['simulated_features']
            data_source = 'Geographic_Simulation'
        
        # Calculate feature statistics
        stats = {
            'total_water_bodies': len(features.get('water_bodies', [])),
            'total_rivers_streams': len(features.get('rivers_streams', [])),
            'total_forest_areas': len(features.get('forests', [])),
            'total_agricultural_areas': len(features.get('agricultural_areas', [])),
            'total_settlements': len(features.get('settlements', [])),
            'total_roads': len(features.get('roads', [])),
            'total_buildings': len(features.get('buildings', [])),
            'data_source': data_source
        }
        
        # Calculate area coverage estimates
        coverage = self._calculate_area_coverage(features)
        
        processed = {
            'features': features,
            'statistics': stats,
            'coverage_estimates': coverage,
            'feature_quality': 'high' if data_source == 'OpenStreetMap' else 'simulated'
        }
        
        return processed

    def _calculate_area_coverage(self, features: Dict) -> Dict:
        """Calculate estimated area coverage for different land uses"""
        
        # Simplified area calculation based on feature counts
        total_features = sum([
            len(features.get('water_bodies', [])),
            len(features.get('forests', [])),
            len(features.get('agricultural_areas', [])),
            len(features.get('settlements', []))
        ])
        
        if total_features == 0:
            return {'forest': 0, 'water': 0, 'agriculture': 0, 'settlement': 0, 'other': 100}
        
        # Estimate percentages based on feature counts and types
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
            'forest': round(forest_pct, 2),
            'water': round(water_pct, 2),
            'agriculture': round(agri_pct, 2),
            'settlement': round(settlement_pct, 2),
            'other': round(other_pct, 2)
        }

    def _perform_fra_analysis(self, processed_features: Dict, lat: float, lon: float) -> Dict:
        """Perform Forest Rights Act suitability analysis"""
        
        coverage = processed_features['coverage_estimates']
        stats = processed_features['statistics']
        
        # Get region info
        region_info = self._identify_region(lat, lon)
        is_tribal = region_info['characteristics'].get('tribal', False)
        
        # Calculate FRA scores
        forest_score = min(40, coverage['forest'] * 0.8)
        tribal_score = 30 if is_tribal else 10
        livelihood_score = min(20, (coverage['agriculture'] + coverage['water'] * 0.5) * 0.4)
        community_score = min(10, stats['total_settlements'] * 2)
        
        total_score = forest_score + tribal_score + livelihood_score + community_score
        
        # Determine suitability levels
        if total_score >= 80:
            overall_suitability = 'very_high'
        elif total_score >= 65:
            overall_suitability = 'high'
        elif total_score >= 45:
            overall_suitability = 'medium'
        else:
            overall_suitability = 'low'
        
        return {
            'overall_suitability': overall_suitability,
            'total_score': total_score,
            'component_scores': {
                'forest_coverage': forest_score,
                'tribal_status': tribal_score,
                'livelihood_potential': livelihood_score,
                'community_presence': community_score
            },
            'land_use_breakdown': coverage,
            'region_info': region_info,
            'suitable_for_ifr': coverage['forest'] > 15 and coverage['agriculture'] > 10,
            'suitable_for_cfr': coverage['forest'] > 30,
            'suitable_for_cr': is_tribal and stats['total_settlements'] > 1
        }

    def _create_comprehensive_maps(self, processed_features: Dict, fra_analysis: Dict, 
                                   lat: float, lon: float, radius_km: float) -> Dict:
        """Create comprehensive interactive maps"""
        
        maps_data = {
            'interactive_map_html': None,
            'feature_distribution_plot': None,
            'fra_suitability_map': None,
            'land_use_chart': None,
            'asset_locations': None
        }
        
        # Create main interactive map
        print("   📍 Creating interactive feature map...")
        maps_data['interactive_map_html'] = self._create_interactive_map(
            processed_features, fra_analysis, lat, lon, radius_km
        )
        
        # Create feature distribution visualization
        print("   📊 Creating feature distribution charts...")
        maps_data['feature_distribution_plot'] = self._create_feature_distribution_plot(processed_features)
        
        # Create FRA suitability visualization
        print("   🌲 Creating FRA suitability map...")
        maps_data['fra_suitability_map'] = self._create_fra_suitability_visualization(fra_analysis, lat, lon)
        
        # Create land use pie chart
        print("   🥧 Creating land use breakdown chart...")
        maps_data['land_use_chart'] = self._create_land_use_chart(fra_analysis['land_use_breakdown'])
        
        return maps_data

    def _create_interactive_map(self, processed_features: Dict, fra_analysis: Dict, 
                                lat: float, lon: float, radius_km: float) -> str:
        """Create interactive Folium map with all features"""
        
        m = folium.Map(location=[lat, lon], zoom_start=13, tiles='OpenStreetMap')
        
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri', name='Satellite', overlay=False, control=True
        ).add_to(m)
        
        folium.Marker(
            [lat, lon],
            popup=f"Analysis Center<br>FRA Suitability: {fra_analysis['overall_suitability'].replace('_', ' ').title()}",
            icon=folium.Icon(color='red', icon='crosshairs', prefix='fa')
        ).add_to(m)
        
        folium.Circle(
            location=[lat, lon], radius=radius_km * 1000,
            popup=f"Analysis Area ({radius_km} km radius)",
            color='red', fillColor='red', fillOpacity=0.1
        ).add_to(m)
        
        features = processed_features['features']
        
        if features.get('water_bodies'):
            water_group = folium.FeatureGroup(name="💧 Water Bodies")
            for water in features['water_bodies']:
                if water['geometry_type'] == 'way' and len(water['coordinates']) > 2:
                    coords = [[coord[1], coord[0]] for coord in water['coordinates']]
                    folium.Polygon(
                        locations=coords,
                        popup=f"Water Body: {water.get('properties', {}).get('name', 'Unnamed')}",
                        color=self.color_scheme['water'], fillColor=self.color_scheme['water'], fillOpacity=0.6
                    ).add_to(water_group)
            water_group.add_to(m)
        
        if features.get('rivers_streams'):
            river_group = folium.FeatureGroup(name="🌊 Rivers & Streams")
            for river in features['rivers_streams']:
                if river['coordinates'] and len(river['coordinates']) > 1:
                    coords = [[coord[1], coord[0]] for coord in river['coordinates']]
                    folium.PolyLine(
                        locations=coords,
                        popup=f"Stream: {river.get('properties', {}).get('name', river.get('feature_type', 'Unnamed'))}",
                        color=self.color_scheme['water'], weight=3, opacity=0.8
                    ).add_to(river_group)
            river_group.add_to(m)
        
        if features.get('forests'):
            forest_group = folium.FeatureGroup(name="🌲 Forest Areas")
            for forest in features['forests']:
                if forest['geometry_type'] == 'way' and len(forest['coordinates']) > 2:
                    coords = [[coord[1], coord[0]] for coord in forest['coordinates']]
                    folium.Polygon(
                        locations=coords,
                        popup=f"Forest: {forest.get('properties', {}).get('name', 'Forest Area')}",
                        color=self.color_scheme['forest'], fillColor=self.color_scheme['forest'], fillOpacity=0.7
                    ).add_to(forest_group)
            forest_group.add_to(m)
        
        if features.get('agricultural_areas'):
            agri_group = folium.FeatureGroup(name="🌾 Agricultural Areas")
            for farm in features['agricultural_areas']:
                if farm['geometry_type'] == 'way' and len(farm['coordinates']) > 2:
                    coords = [[coord[1], coord[0]] for coord in farm['coordinates']]
                    folium.Polygon(
                        locations=coords,
                        popup=f"Agriculture: {farm.get('properties', {}).get('name', farm.get('feature_type', 'Farmland'))}",
                        color=self.color_scheme['agriculture'], fillColor=self.color_scheme['agriculture'], fillOpacity=0.6
                    ).add_to(agri_group)
            agri_group.add_to(m)
        
        if features.get('settlements'):
            settlement_group = folium.FeatureGroup(name="🏘️ Settlements")
            for settlement in features['settlements']:
                if settlement['geometry_type'] == 'way' and len(settlement['coordinates']) > 2:
                    coords = [[coord[1], coord[0]] for coord in settlement['coordinates']]
                    folium.Polygon(
                        locations=coords, popup=f"Settlement: {settlement.get('name', 'Village')}",
                        color=self.color_scheme['settlement'], fillColor=self.color_scheme['settlement'], fillOpacity=0.5
                    ).add_to(settlement_group)
                elif settlement['coordinates'] and len(settlement['coordinates']) == 2:
                    folium.Marker(
                        [settlement['coordinates'][1], settlement['coordinates'][0]],
                        popup=f"Settlement: {settlement.get('name', 'Village')}",
                        icon=folium.Icon(color='orange', icon='home', prefix='fa')
                    ).add_to(settlement_group)
            settlement_group.add_to(m)
        
        if features.get('roads'):
            road_group = folium.FeatureGroup(name="🛣️ Roads")
            for road in features['roads']:
                if road['coordinates'] and len(road['coordinates']) > 1:
                    coords = [[coord[1], coord[0]] for coord in road['coordinates']]
                    road_type = road.get('feature_type', 'track')
                    if road_type in ['primary', 'trunk']: weight, color = 5, '#FF0000'
                    elif road_type in ['secondary']: weight, color = 4, '#FF8C00'
                    elif road_type in ['tertiary']: weight, color = 3, '#FFD700'
                    else: weight, color = 2, '#808080'
                    folium.PolyLine(
                        locations=coords, popup=f"Road: {road.get('name', road_type.title())}",
                        color=color, weight=weight, opacity=0.7
                    ).add_to(road_group)
            road_group.add_to(m)
        
        folium.LayerControl().add_to(m)
        
        legend_html = """
        <div style="position: fixed; bottom: 50px; left: 50px; width: 150px; height: 120px; 
                     background-color: white; border:2px solid grey; z-index:9999; 
                     font-size:14px; padding: 10px; border-radius: 5px;">
        <p><b>Legend</b></p>
        <p><i class="fa fa-square" style="color:#1E90FF"></i> Water Bodies</p>
        <p><i class="fa fa-square" style="color:#228B22"></i> Forest Areas</p>
        <p><i class="fa fa-square" style="color:#FFD700"></i> Agriculture</p>
        <p><i class="fa fa-square" style="color:#FF6347"></i> Settlements</p>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))
        
        return m._repr_html_()

    def _create_feature_distribution_plot(self, processed_features: Dict) -> str:
        stats = processed_features['statistics']
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Feature Counts', 'Water Resources', 'Land Use Distribution', 'Infrastructure'),
            specs=[[{"type": "bar"}, {"type": "pie"}], [{"type": "bar"}, {"type": "bar"}]]
        )
        
        feature_names = ['Water Bodies', 'Streams', 'Forests', 'Farms', 'Settlements', 'Roads']
        feature_counts = [
            stats['total_water_bodies'], stats['total_rivers_streams'], stats['total_forest_areas'],
            stats['total_agricultural_areas'], stats['total_settlements'], stats['total_roads']
        ]
        fig.add_trace(go.Bar(x=feature_names, y=feature_counts, name="Feature Counts", 
                             marker_color=['#1E90FF', '#4682B4', '#228B22', '#FFD700', '#FF6347', '#808080']), row=1, col=1)
        
        water_data = ['Lakes/Ponds', 'Rivers/Streams']
        water_values = [stats['total_water_bodies'], stats['total_rivers_streams']]
        fig.add_trace(go.Pie(labels=water_data, values=water_values, name="Water Resources"), row=1, col=2)
        
        coverage = processed_features['coverage_estimates']
        land_use_types = list(coverage.keys())
        land_use_values = list(coverage.values())
        fig.add_trace(go.Bar(x=land_use_types, y=land_use_values, name="Land Use %",
                             marker_color=['#228B22', '#1E90FF', '#FFD700', '#FF6347', '#D3D3D3']), row=2, col=1)
        
        infra_types = ['Settlements', 'Roads', 'Buildings']
        infra_counts = [stats['total_settlements'], stats['total_roads'], stats['total_buildings']]
        fig.add_trace(go.Bar(x=infra_types, y=infra_counts, name="Infrastructure",
                             marker_color=['#FF6347', '#808080', '#8B4513']), row=2, col=2)
        
        fig.update_layout(title_text="Geographic Feature Analysis Dashboard", showlegend=False, height=600)
        return fig.to_html(full_html=False, include_plotlyjs='cdn')

    def _create_fra_suitability_visualization(self, fra_analysis: Dict, lat: float, lon: float) -> str:
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('FRA Suitability Score', 'Component Breakdown', 'Rights Eligibility', 'Implementation Priority'),
            specs=[[{"type": "indicator"}, {"type": "bar"}], [{"type": "bar"}, {"type": "pie"}]]
        )
        
        suitability_colors = {'very_high': 'green', 'high': 'lightgreen', 'medium': 'yellow', 'low': 'orange', 'very_low': 'red'}
        fig.add_trace(go.Indicator(
            mode="gauge+number", value=fra_analysis['total_score'],
            title={'text': "FRA Suitability Score"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': suitability_colors.get(fra_analysis['overall_suitability'], 'gray')},
                'steps': [
                    {'range': [0, 45], 'color': "orange"},
                    {'range': [45, 65], 'color': "yellow"},
                    {'range': [65, 100], 'color': "lightgreen"}
                ],
            }
        ), row=1, col=1)
        
        components = [c.replace('_', ' ').title() for c in fra_analysis['component_scores'].keys()]
        scores = list(fra_analysis['component_scores'].values())
        fig.add_trace(go.Bar(x=components, y=scores, name="Component Scores",
                             marker_color=['#228B22', '#9932CC', '#FFD700', '#FF6347']), row=1, col=2)
        
        rights_types = ['Individual Forest Rights', 'Community Forest Resources', 'Community Rights']
        rights_eligible = [fra_analysis['suitable_for_ifr'], fra_analysis['suitable_for_cfr'], fra_analysis['suitable_for_cr']]
        rights_colors = ['green' if eligible else 'red' for eligible in rights_eligible]
        rights_values = [1 if eligible else 0 for eligible in rights_eligible]
        fig.add_trace(go.Bar(x=rights_types, y=rights_values, name="Rights Eligibility", marker_color=rights_colors,
                             text=['Eligible' if eligible else 'Not Eligible' for eligible in rights_eligible],
                             textposition='auto'), row=2, col=1)
        
        priority_levels = ['High Priority', 'Medium Priority', 'Low Priority']
        if fra_analysis['overall_suitability'] in ['very_high', 'high']: priority_values = [70, 20, 10]
        elif fra_analysis['overall_suitability'] == 'medium': priority_values = [30, 50, 20]
        else: priority_values = [10, 30, 60]
        fig.add_trace(go.Pie(labels=priority_levels, values=priority_values, name="Implementation Priority"), row=2, col=2)
        
        fig.update_layout(title_text=f"FRA Suitability Assessment - {fra_analysis['overall_suitability'].replace('_', ' ').title()}", height=700)
        return fig.to_html(full_html=False, include_plotlyjs='cdn')

    def _create_land_use_chart(self, land_use_breakdown: Dict) -> str:
        fig = go.Figure(data=[go.Pie(
            labels=[k.title() for k in land_use_breakdown.keys()],
            values=list(land_use_breakdown.values()),
            hole=0.3,
            marker_colors=['#228B22', '#1E90FF', '#FFD700', '#FF6347', '#D3D3D3']
        )])
        fig.update_layout(
            title_text="Land Use Distribution",
            annotations=[dict(text='Land Use', x=0.5, y=0.5, font_size=20, showarrow=False)]
        )
        return fig.to_html(full_html=False, include_plotlyjs='cdn')

    def _generate_location_based_recommendations(self, processed_features: Dict, fra_analysis: Dict) -> Dict:
        features = processed_features['features']
        coverage = fra_analysis['land_use_breakdown']
        recommendations = {
            'immediate_actions': [], 'infrastructure_development': [],
            'conservation_priorities': [], 'livelihood_opportunities': [],
            'location_specific_notes': []
        }
        
        if fra_analysis['overall_suitability'] in ['very_high', 'high']:
            recommendations['immediate_actions'].extend([
                f"Form Village Forest Rights Committee in {len(features.get('settlements', []))} identified settlements",
                "Conduct community meetings in all mapped village locations",
                f"Document forest use in {len(features.get('forests', []))} identified forest areas"
            ])
        
        if processed_features['statistics']['total_water_bodies'] < 2:
            recommendations['infrastructure_development'].append(
                f"Water infrastructure development needed - only {processed_features['statistics']['total_water_bodies']} water bodies detected")
        
        if len(features.get('roads', [])) < 3:
            recommendations['infrastructure_development'].append("Improve road connectivity - current road network limited")
        
        if coverage['forest'] > 40:
            recommendations['conservation_priorities'].extend([
                f"High conservation priority - {coverage['forest']:.1f}% forest coverage detected",
                f"Protect {len(features.get('forests', []))} mapped forest areas",
                "Establish community forest protection measures"
            ])
        
        if coverage['water'] > 10:
            recommendations['livelihood_opportunities'].append(
                f"Water-based livelihoods possible - {len(features.get('water_bodies', []))} water bodies + {len(features.get('rivers_streams', []))} streams")
        
        if coverage['agriculture'] > 25:
            recommendations['livelihood_opportunities'].append(
                f"Agricultural enhancement opportunities in {len(features.get('agricultural_areas', []))} mapped farm areas")
        
        settlement_names = [s.get('name', 'Unnamed') for s in features.get('settlements', [])]
        if settlement_names:
            recommendations['location_specific_notes'].append(
                f"Key settlements for community organization: {', '.join(settlement_names[:3])}")
        
        water_features = len(features.get('water_bodies', [])) + len(features.get('rivers_streams', []))
        if water_features > 0:
            recommendations['location_specific_notes'].append(f"Water resource management needed for {water_features} mapped water features")
        
        return recommendations


class FRAMappingAPI:
    """Simple API for FRA mapping system"""
    
    def __init__(self):
        self.system = FRAMappingSystem()
    
    def analyze_location(self, latitude: float, longitude: float, radius_km: float = 2.0) -> Dict:
        return self.system.analyze_and_map(latitude, longitude, radius_km)
    
    def get_interactive_map(self, latitude: float, longitude: float, radius_km: float = 2.0) -> str:
        result = self.analyze_location(latitude, longitude, radius_km)
        if result['status'] == 'success':
            return result['maps']['interactive_map_html']
        return "<p>Map generation failed</p>"
    
    def export_maps(self, result: Dict, output_dir: str = "fra_maps") -> Dict:
        import os
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        exported_files = {}
        if result['status'] == 'success':
            maps = result['maps']
            coords = result['coordinates']
            filename_base = f"fra_analysis_{coords['lat']:.4f}_{coords['lon']:.4f}"
            
            if maps['interactive_map_html']:
                map_file = os.path.join(output_dir, f"{filename_base}_interactive_map.html")
                with open(map_file, 'w', encoding='utf-8') as f:
                    f.write(maps['interactive_map_html'])
                exported_files['interactive_map'] = map_file
            
            for viz_type in ['feature_distribution_plot', 'fra_suitability_map', 'land_use_chart']:
                if maps.get(viz_type):
                    viz_file = os.path.join(output_dir, f"{filename_base}_{viz_type}.html")
                    with open(viz_file, 'w', encoding='utf-8') as f:
                        f.write(maps[viz_type])
                    exported_files[viz_type] = viz_file
        return exported_files

#
# ==============================================================================
#  NEW: FastAPI Application
# ==============================================================================
#

# 1. Create a FastAPI app instance
app = FastAPI(
    title="FRA Mapping API",
    description="An API for conducting Forest Rights Act (FRA) suitability analysis and generating interactive maps.",
    version="1.0.0"
)

# 2. Instantiate your mapping API
mapping_api = FRAMappingAPI()

# 3. Define the API endpoints (routes)

@app.get("/", response_class=HTMLResponse)
def read_root():
    """
    Root endpoint that provides a welcome message and links to the documentation.
    """
    return """
    <html>
        <head>
            <title>FRA Mapping API</title>
        </head>
        <body>
            <h1>Welcome to the FRA Mapping API!</h1>
            <p>This API provides tools for Forest Rights Act analysis.</p>
            <p>Visit <a href="/docs">/docs</a> for the interactive API documentation (Swagger UI).</p>
            <p>Visit <a href="/redoc">/redoc</a> for alternative API documentation.</p>
        </body>
    </html>
    """

@app.get("/analyze", response_class=JSONResponse)
def analyze_location_endpoint(latitude: float, longitude: float, radius_km: float = 2.0):
    """
    Performs a full FRA analysis for a given location and returns the results
    as a JSON object, including HTML for maps and charts.
    """
    print(f"API call to /analyze for lat={latitude}, lon={longitude}")
    result = mapping_api.analyze_location(latitude, longitude, radius_km)
    return result

@app.get("/map", response_class=HTMLResponse)
def get_interactive_map_endpoint(latitude: float, longitude: float, radius_km: float = 2.0):
    """
    Generates and returns only the interactive Folium map as an HTML response,
    which can be directly viewed in a browser or embedded in an iframe.
    """
    print(f"API call to /map for lat={latitude}, lon={longitude}")
    map_html = mapping_api.get_interactive_map(latitude, longitude, radius_km)
    return map_html

#
# ==============================================================================
#  MODIFIED: Main Execution Block
#  This will now run the FastAPI server instead of the command-line demo.
# ==============================================================================
#

if __name__ == "__main__":
    print("🗺️ Starting FRA Mapping FastAPI Server...")
    # This runs the FastAPI application using the Uvicorn server.
    # 'main:app' refers to the 'app' instance in the 'main.py' file.

    
    # --reload makes the server restart after code changes.
    # You can change host to "0.0.0.0" to make it accessible on your network.
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
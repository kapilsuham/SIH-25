# test_fra_backend.py
"""
Complete testing script for FRA DSS Backend
Run this to verify everything is working correctly
"""

import requests
import json
import time
import os
from pathlib import Path

class FRABackendTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/v1"
        
    def test_health_check(self):
        """Test if backend is running"""
        print("1. Testing Backend Health...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Backend is healthy: {data.get('message')}")
                return True
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("   ❌ Cannot connect to backend. Is it running on port 8000?")
            return False
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
            return False
    
    def test_analysis_endpoint(self, lat=23.3441, lon=85.3096, radius=2.0):
        """Test the main analysis endpoint"""
        print(f"\n2. Testing Analysis Endpoint with coordinates: {lat}, {lon}...")
        
        payload = {
            "latitude": lat,
            "longitude": lon,
            "radius_km": radius,
            "save_to_db": True
        }
        
        try:
            print("   📡 Sending analysis request...")
            start_time = time.time()
            
            response = requests.post(
                f"{self.api_url}/analyze/",
                json=payload,
                timeout=120  # Analysis can take time
            )
            
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Analysis completed in {execution_time:.2f} seconds")
                print(f"   📊 FRA Suitability: {data.get('fra_analysis', {}).get('overall_suitability', 'Unknown')}")
                print(f"   🏆 Score: {data.get('fra_analysis', {}).get('total_score', 0)}/100")
                print(f"   🗺️ Maps generated: {len(data.get('maps', {}))}")
                return data
            else:
                print(f"   ❌ Analysis failed: {response.status_code}")
                print(f"   📄 Response: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("   ⏰ Analysis timed out (this is normal for first run)")
            return None
        except Exception as e:
            print(f"   ❌ Analysis error: {e}")
            return None
    
    def test_different_coordinates(self):
        """Test different regional coordinates"""
        print("\n3. Testing Different Regional Coordinates...")
        
        test_coordinates = [
            {"name": "Jharkhand (Forest Rich)", "lat": 23.3441, "lon": 85.3096},
            {"name": "Chhattisgarh (Tribal Area)", "lat": 20.5937, "lon": 81.9629},
            {"name": "Odisha (Coastal)", "lat": 20.2961, "lon": 85.8245},
        ]
        
        results = []
        for coord in test_coordinates:
            print(f"   🌍 Testing {coord['name']}...")
            result = self.test_analysis_endpoint(coord["lat"], coord["lon"], 1.5)
            if result:
                results.append({
                    "name": coord["name"],
                    "suitability": result.get('fra_analysis', {}).get('overall_suitability'),
                    "score": result.get('fra_analysis', {}).get('total_score'),
                })
            time.sleep(2)  # Rate limiting
        
        if results:
            print("\n   📈 Comparison Results:")
            for result in results:
                print(f"      {result['name']}: {result['suitability']} ({result['score']}/100)")
        
        return results
    
    def test_map_generation(self):
        """Test if maps are generated correctly"""
        print("\n4. Testing Map Generation...")
        
        # Check backend maps directory
        backend_maps_dir = "fra_maps"
        if os.path.exists(backend_maps_dir):
            map_files = [f for f in os.listdir(backend_maps_dir) if f.endswith('.html')]
            print(f"   📁 Backend maps directory: {len(map_files)} files")
        else:
            print("   ⚠️ Backend maps directory not found")
            map_files = []
        
        # Check frontend maps directory
        frontend_paths = [
            "../frontend/public/fra_maps",
            "../../frontend/public/fra_maps", 
            "../public/fra_maps"
        ]
        
        frontend_found = False
        for path in frontend_paths:
            if os.path.exists(path):
                frontend_files = [f for f in os.listdir(path) if f.endswith('.html')]
                print(f"   🌐 Frontend maps directory: {len(frontend_files)} files")
                frontend_found = True
                break
        
        if not frontend_found:
            print("   ⚠️ Frontend maps directory not found")
            print("   💡 Maps will only be saved to backend directory")
        
        return len(map_files) > 0
    
    def test_api_endpoints(self):
        """Test various API endpoints"""
        print("\n5. Testing API Endpoints...")
        
        endpoints = [
            {"url": f"{self.api_url}/health", "name": "API Health"},
            {"url": f"{self.api_url}/analyze/health", "name": "Analysis Health"},
            {"url": f"{self.api_url}/analyze/regions", "name": "Supported Regions"},
            {"url": f"{self.api_url}/analyze/maps", "name": "Generated Maps List"},
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint["url"], timeout=10)
                if response.status_code == 200:
                    print(f"   ✅ {endpoint['name']}: OK")
                else:
                    print(f"   ⚠️ {endpoint['name']}: {response.status_code}")
            except Exception as e:
                print(f"   ❌ {endpoint['name']}: Error")
    
    def test_coordinate_validation(self):
        """Test coordinate validation"""
        print("\n6. Testing Coordinate Validation...")
        
        test_cases = [
            {"lat": 23.3441, "lon": 85.3096, "expected": True, "name": "Valid coordinates"},
            {"lat": 91, "lon": 85.3096, "expected": False, "name": "Invalid latitude > 90"},
            {"lat": 23.3441, "lon": 181, "expected": False, "name": "Invalid longitude > 180"},
            {"lat": -91, "lon": 85.3096, "expected": False, "name": "Invalid latitude < -90"},
        ]
        
        for case in test_cases:
            try:
                payload = {"latitude": case["lat"], "longitude": case["lon"]}
                response = requests.post(f"{self.api_url}/analyze/validate-coordinates", json=payload, timeout=5)
                
                if case["expected"]:
                    if response.status_code == 200:
                        print(f"   ✅ {case['name']}: Correctly validated as valid")
                    else:
                        print(f"   ❌ {case['name']}: Should be valid but got {response.status_code}")
                else:
                    if response.status_code == 400:
                        print(f"   ✅ {case['name']}: Correctly rejected as invalid")
                    else:
                        print(f"   ❌ {case['name']}: Should be invalid but got {response.status_code}")
            except Exception as e:
                print(f"   ❌ {case['name']}: Error - {e}")
    
    def run_full_test_suite(self):
        """Run the complete test suite"""
        print("=" * 60)
        print("FRA DSS Backend - Complete Test Suite")
        print("=" * 60)
        
        # Test 1: Health Check
        if not self.test_health_check():
            print("\n❌ Backend is not running. Please start the backend first:")
            print("   cd fra-dss-backend")
            print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
            return False
        
        # Test 2: Analysis
        analysis_result = self.test_analysis_endpoint()
        
        # Test 3: Multiple coordinates
        self.test_different_coordinates()
        
        # Test 4: Map generation
        maps_generated = self.test_map_generation()
        
        # Test 5: API endpoints
        self.test_api_endpoints()
        
        # Test 6: Validation
        self.test_coordinate_validation()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        if analysis_result:
            print("✅ Core functionality: WORKING")
        else:
            print("❌ Core functionality: FAILED")
            
        if maps_generated:
            print("✅ Map generation: WORKING")
        else:
            print("⚠️ Map generation: CHECK MANUALLY")
        
        print("\n🔗 Frontend Integration:")
        print("   1. Update your HTML file's JavaScript")
        print("   2. Remove example button functionality")
        print("   3. Make analysis user-input based")
        print("   4. Update iframe sources to use generated maps")
        
        print("\n📊 API Documentation:")
        print("   Swagger UI: http://localhost:8000/docs")
        print("   ReDoc: http://localhost:8000/redoc")
        
        return analysis_result is not None

if __name__ == "__main__":
    # Run the test suite
    tester = FRABackendTester()
    
    # Check if backend is specified differently
    import sys
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
        tester = FRABackendTester(base_url)
    
    success = tester.run_full_test_suite()
    
    if success:
        print("\n🎉 All tests completed! Backend is ready for use.")
    else:
        print("\n❌ Some tests failed. Please check the backend setup.")
    
    print("\n💡 Next Steps:")
    print("   1. Update your frontend HTML to use user input coordinates")
    print("   2. Test with different locations across India")
    print("   3. Verify maps appear correctly in your frontend")
    print("   4. Check that analysis results are relevant to user coordinates")
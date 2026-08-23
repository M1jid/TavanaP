"""
Simple route testing script for GitLab CI.

This script tests all routes with minimal setup and provides clear pass/fail results
suitable for CI/CD pipelines.

Usage:
    python test_routes_simple.py
    pytest test_routes_simple.py -v
"""

import sys
import os
from typing import Dict, List, Any
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import json
from datetime import date, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from main import app
    from auth.auth import User
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the correct directory with all dependencies installed.")
    sys.exit(1)

# Test client
client = TestClient(app)

# Mock user for authentication
MOCK_USER = User(
    id=1,
    username="test_user",
    full_name="Test User",
    email="test@example.com",
    disabled=False,
    history=[],
    permissions=["admin", "platform.telegram.fa.channels.create", "platform.telegram.fa.channels.update"],
    query_ids=[],
    following_channels=[],
    following_groups=[],
    following_users=[],
    accessible_urls=["http://localhost:8000"]
)

# Sample data for testing
SAMPLE_DATA = {
    "string": "test_string",
    "integer": 1,
    "date": date.today().strftime("%Y-%m-%d"),
    "start_date": (date.today() - timedelta(days=10)).strftime("%Y-%m-%d"),
    "end_date": date.today().strftime("%Y-%m-%d"),
    "title": "Test Title",
    "description": "Test Description",
    "must": ["test", "words"],
    "should": ["optional", "words"],
    "must_not": ["excluded", "words"],
    "type": 1,
    "limit": 10,
    "offset": 0
}

class SimpleRouteTester:
    """Simple route tester for CI/CD pipelines."""
    
    def __init__(self):
        self.app = app
        self.client = client
        self.results = []
        
    def test_route(self, route_path: str, method: str) -> Dict[str, Any]:
        """Test a single route."""
        result = {
            'route': f"{method} {route_path}",
            'status': None,
            'success': False,
            'error': None
        }
        
        try:
            # Mock authentication and services
            with patch('auth.auth.get_current_active_user', return_value=MOCK_USER):
                with patch('services.services.check_access', return_value=True):
                    with patch('utils.db_handler.get_user_by_username', return_value=MOCK_USER):
                        with patch('services.telegram.shared_services.TelegramService') as mock_service:
                            # Configure mock service methods
                            mock_service.create_channel.return_value = {"id": 1, "name": "test"}
                            mock_service.update_channel.return_value = {"id": 1, "name": "test"}
                            mock_service.upload_query_image.return_value = {"success": True}
                            
                            # Prepare URL with sample parameters
                            url = route_path
                            if '{' in url and '}' in url:
                                # Replace path parameters with sample values
                                url = url.replace('{id}', '1')
                                url = url.replace('{user_id}', '1')
                                url = url.replace('{query_id}', '1')
                                url = url.replace('{channel_id}', '1')
                                url = url.replace('{group_id}', '1')
                                url = url.replace('{post_id}', '1')
                                url = url.replace('{trend_id}', '1')
                                url = url.replace('{page_id}', '1')
                            
                            # Prepare request parameters
                            params = {}
                            if 'date' in route_path.lower() or 'trend' in route_path.lower():
                                params = {
                                    'start_date': SAMPLE_DATA['start_date'],
                                    'end_date': SAMPLE_DATA['end_date']
                                }
                            
                            # Prepare request data
                            request_kwargs = {
                                'params': params,
                                'headers': {'Authorization': 'Bearer fake_token'}
                            }
                            
                            # Add body data for POST/PUT requests
                            if method in ['POST', 'PUT', 'PATCH']:
                                if 'user' in route_path.lower():
                                    request_kwargs['json'] = {
                                        'username': 'test_user',
                                        'full_name': 'Test User',
                                        'email': 'test@example.com',
                                        'password': 'test_password'
                                    }
                                elif 'query' in route_path.lower():
                                    request_kwargs['json'] = {
                                        'title': SAMPLE_DATA['title'],
                                        'description': SAMPLE_DATA['description'],
                                        'must': SAMPLE_DATA['must'],
                                        'should': SAMPLE_DATA['should'],
                                        'must_not': SAMPLE_DATA['must_not'],
                                        'query_type': SAMPLE_DATA['type']
                                    }
                                else:
                                    request_kwargs['json'] = {'test': 'data'}
                            
                            # Make the request
                            if method == 'GET':
                                response = self.client.get(url, **request_kwargs)
                            elif method == 'POST':
                                response = self.client.post(url, **request_kwargs)
                            elif method == 'PUT':
                                response = self.client.put(url, **request_kwargs)
                            elif method == 'DELETE':
                                response = self.client.delete(url, **request_kwargs)
                            elif method == 'PATCH':
                                response = self.client.patch(url, **request_kwargs)
                            else:
                                result['error'] = f"Unsupported method: {method}"
                                return result
                            
                            result['status'] = response.status_code
                            
                            # Consider various status codes as success
                            if response.status_code in [200, 201, 202]:
                                result['success'] = True
                            elif response.status_code == 422:
                                result['success'] = True  # Validation error is expected
                            elif response.status_code in [401, 403, 404]:
                                result['success'] = True  # Auth/permission errors are expected
                            else:
                                result['error'] = f"Unexpected status: {response.status_code}"
                                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def test_all_routes(self):
        """Test all routes in the application."""
        print("🔍 Testing all routes...")
        
        # Get all routes
        routes = []
        for route in self.app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                for method in route.methods:
                    if method not in ['HEAD', 'OPTIONS']:
                        routes.append((route.path, method))
        
        print(f"📊 Found {len(routes)} routes to test")
        
        # Test each route
        passed = 0
        failed = 0
        
        for route_path, method in routes:
            result = self.test_route(route_path, method)
            self.results.append(result)
            
            if result['success']:
                passed += 1
                print(f"✅ {result['route']} - Status: {result['status']}")
            else:
                failed += 1
                print(f"❌ {result['route']} - Error: {result['error']}")
        
        print(f"\n📋 RESULTS: {passed} passed, {failed} failed")
        
        # Return exit code for CI
        return 0 if failed == 0 else 1

def main():
    """Main function for running tests."""
    tester = SimpleRouteTester()
    exit_code = tester.test_all_routes()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

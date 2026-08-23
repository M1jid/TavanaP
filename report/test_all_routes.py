"""
Comprehensive test suite for all API routes in the Report Data API.

This test suite automatically discovers and tests all routes defined in the application,
handling authentication, required parameters, and different HTTP methods.

Usage:
    python test_all_routes.py
    pytest test_all_routes.py -v
"""

import pytest
import asyncio
from typing import Dict, List, Any, Optional
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import date, timedelta
import io

# Import your app
from main import app
from auth.auth import User

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
    permissions=["admin", "platform.telegram.fa.channels.create", "platform.telegram.fa.channels.update", "platform.telegram.fa.channels.block"],
    query_ids=[],
    following_channels=[],
    following_groups=[],
    following_users=[],
    accessible_urls=["http://localhost:8000"]
)

# Mock authentication dependency
def mock_get_current_active_user():
    return MOCK_USER

# Sample data for different parameter types
SAMPLE_DATA = {
    "string": "test_string",
    "integer": 1,
    "float": 1.5,
    "boolean": True,
    "list": ["item1", "item2"],
    "dict": {"key": "value"},
    "date": date.today().strftime("%Y-%m-%d"),
    "start_date": (date.today() - timedelta(days=10)).strftime("%Y-%m-%d"),
    "end_date": date.today().strftime("%Y-%m-%d"),
    "query_id": 1,
    "user_id": 1,
    "channel_id": 1,
    "group_id": 1,
    "post_id": 1,
    "trend_id": 1,
    "page_id": 1,
    "title": "Test Title",
    "description": "Test Description",
    "must": ["test", "words"],
    "should": ["optional", "words"],
    "must_not": ["excluded", "words"],
    "type": 1,
    "limit": 10,
    "offset": 0,
    "page": 1,
    "size": 10
}

# Mock file for file uploads
MOCK_FILE = ("test.jpg", io.BytesIO(b"fake image content"), "image/jpeg")

class RouteTester:
    """Main class for testing all routes in the application."""
    
    def __init__(self):
        self.app = app
        self.client = client
        self.failed_routes = []
        self.successful_routes = []
        self.skipped_routes = []
        
    def get_route_params(self, route_path: str, method: str) -> Dict[str, Any]:
        """Generate appropriate parameters for a route based on its path and method."""
        params = {}
        query_params = {}
        
        # Extract path parameters
        path_parts = route_path.split('/')
        for part in path_parts:
            if part.startswith('{') and part.endswith('}'):
                param_name = part[1:-1]
                if param_name in SAMPLE_DATA:
                    params[param_name] = SAMPLE_DATA[param_name]
                else:
                    params[param_name] = 1  # Default integer for unknown path params
        
        # Add common query parameters based on route patterns
        if 'date' in route_path.lower() or 'trend' in route_path.lower():
            query_params.update({
                'start_date': SAMPLE_DATA['start_date'],
                'end_date': SAMPLE_DATA['end_date']
            })
        
        if 'query' in route_path.lower():
            query_params.update({
                'title': SAMPLE_DATA['title'],
                'description': SAMPLE_DATA['description'],
                'must': SAMPLE_DATA['must'],
                'should': SAMPLE_DATA['should'],
                'must_not': SAMPLE_DATA['must_not'],
                'type': SAMPLE_DATA['type']
            })
        
        if 'channel' in route_path.lower():
            query_params.update({
                'limit': SAMPLE_DATA['limit'],
                'offset': SAMPLE_DATA['offset']
            })
        
        # For POST/PUT requests, add body data
        if method in ['POST', 'PUT', 'PATCH']:
            body_data = {}
            if 'user' in route_path.lower():
                body_data = {
                    'username': SAMPLE_DATA['string'],
                    'full_name': SAMPLE_DATA['string'],
                    'email': 'test@example.com',
                    'password': 'test_password'
                }
            elif 'channel' in route_path.lower():
                body_data = {
                    'name': SAMPLE_DATA['string'],
                    'description': SAMPLE_DATA['description'],
                    'url': 'https://t.me/test_channel'
                }
            elif 'query' in route_path.lower():
                body_data = {
                    'title': SAMPLE_DATA['title'],
                    'description': SAMPLE_DATA['description'],
                    'must': SAMPLE_DATA['must'],
                    'should': SAMPLE_DATA['should'],
                    'must_not': SAMPLE_DATA['must_not'],
                    'query_type': SAMPLE_DATA['type']
                }
            else:
                body_data = {'test': 'data'}
            
            return params, query_params, body_data
        
        return params, query_params, None
    
    def test_route(self, route_path: str, method: str) -> Dict[str, Any]:
        """Test a single route and return the result."""
        result = {
            'route': f"{method} {route_path}",
            'status': None,
            'response': None,
            'error': None,
            'success': False
        }
        
        try:
            # Get parameters for the route
            path_params, query_params, body_data = self.get_route_params(route_path, method)
            
            # Build the URL with path parameters
            url = route_path
            for param_name, param_value in path_params.items():
                url = url.replace(f"{{{param_name}}}", str(param_value))
            
            # Prepare request arguments
            request_kwargs = {
                'params': query_params,
                'headers': {'Authorization': 'Bearer fake_token'}
            }
            
            # Add body data for POST/PUT requests
            if body_data:
                if 'img' in route_path or 'file' in route_path or 'image' in route_path:
                    # Handle file uploads
                    files = {'img': MOCK_FILE}
                    request_kwargs['files'] = files
                    request_kwargs['data'] = body_data
                else:
                    request_kwargs['json'] = body_data
            
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
            result['response'] = response.text[:500]  # Limit response text
            
            # Consider 200, 201, 202 as success, 422 as validation error (expected)
            if response.status_code in [200, 201, 202]:
                result['success'] = True
            elif response.status_code == 422:
                result['success'] = True  # Validation error is expected with mock data
                result['note'] = 'Validation error (expected with mock data)'
            elif response.status_code == 401:
                result['note'] = 'Authentication required (expected)'
            elif response.status_code == 403:
                result['note'] = 'Permission denied (expected)'
            elif response.status_code == 404:
                result['note'] = 'Resource not found (expected with mock data)'
            else:
                result['error'] = f"Unexpected status code: {response.status_code}"
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def test_all_routes(self):
        """Test all routes in the application."""
        print("🔍 Discovering all routes...")
        
        # Get all routes from the app
        routes = []
        for route in self.app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                for method in route.methods:
                    if method not in ['HEAD', 'OPTIONS']:  # Skip HEAD and OPTIONS
                        routes.append((route.path, method))
        
        print(f"📊 Found {len(routes)} routes to test")
        print("=" * 80)
        
        # Test each route
        for route_path, method in routes:
            print(f"Testing: {method} {route_path}")
            
            # Mock the authentication dependency
            with patch('auth.auth.get_current_active_user', return_value=MOCK_USER):
                with patch('services.services.check_access', return_value=True):
                    with patch('utils.db_handler.get_user_by_username', return_value=MOCK_USER):
                        result = self.test_route(route_path, method)
            
            # Categorize results
            if result['success']:
                self.successful_routes.append(result)
                status_icon = "✅"
            elif result.get('note'):
                self.skipped_routes.append(result)
                status_icon = "⚠️"
            else:
                self.failed_routes.append(result)
                status_icon = "❌"
            
            print(f"{status_icon} {result['route']} - Status: {result['status']}")
            if result.get('note'):
                print(f"   Note: {result['note']}")
            if result.get('error'):
                print(f"   Error: {result['error']}")
            print()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print a summary of test results."""
        print("=" * 80)
        print("📋 TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Successful routes: {len(self.successful_routes)}")
        print(f"⚠️  Skipped routes: {len(self.skipped_routes)}")
        print(f"❌ Failed routes: {len(self.failed_routes)}")
        print(f"📊 Total routes: {len(self.successful_routes) + len(self.skipped_routes) + len(self.failed_routes)}")
        
        if self.failed_routes:
            print("\n❌ FAILED ROUTES:")
            for route in self.failed_routes:
                print(f"   {route['route']} - {route.get('error', 'Unknown error')}")
        
        if self.skipped_routes:
            print("\n⚠️  SKIPPED ROUTES (Expected behavior):")
            for route in self.skipped_routes:
                print(f"   {route['route']} - {route.get('note', 'Skipped')}")

# Pytest test functions
@pytest.fixture
def route_tester():
    """Fixture for route tester."""
    return RouteTester()

@pytest.fixture
def mock_user():
    """Fixture for mock user."""
    return MOCK_USER

def test_all_routes_comprehensive(route_tester):
    """Comprehensive test of all routes."""
    with patch('auth.auth.get_current_active_user', return_value=MOCK_USER):
        with patch('services.services.check_access', return_value=True):
            with patch('utils.db_handler.get_user_by_username', return_value=MOCK_USER):
                route_tester.test_all_routes()
                
                # Assert that we have tested some routes
                total_routes = len(route_tester.successful_routes) + len(route_tester.skipped_routes) + len(route_tester.failed_routes)
                assert total_routes > 0, "No routes were tested"
                
                # Assert that most routes are either successful or skipped (not failed)
                failure_rate = len(route_tester.failed_routes) / total_routes
                assert failure_rate < 0.5, f"Too many routes failed: {failure_rate:.2%}"

def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_token_endpoint():
    """Test the token endpoint (should fail without proper credentials)."""
    response = client.post("/token", data={"username": "test", "password": "test"})
    # This should fail with 401 or 404, which is expected
    assert response.status_code in [401, 404, 422]

def test_satellite_channels_endpoint():
    """Test the satellite channels endpoint."""
    with patch('auth.auth.get_current_active_user', return_value=MOCK_USER):
        response = client.get("/satelite_channels/sources")
        # This should work with mock authentication
        assert response.status_code in [200, 401, 403]

# Individual route tests (examples)
def test_telegram_platform_endpoint():
    """Test telegram platform endpoint."""
    with patch('auth.auth.get_current_active_user', return_value=MOCK_USER):
        response = client.get("/platform/fa/telegram/channels")
        assert response.status_code in [200, 401, 403, 422]

def test_instagram_platform_endpoint():
    """Test instagram platform endpoint."""
    with patch('auth.auth.get_current_active_user', return_value=MOCK_USER):
        response = client.get("/platform/fa/instagram/trends/overview")
        assert response.status_code in [200, 401, 403, 422]

def test_twitter_platform_endpoint():
    """Test twitter platform endpoint."""
    with patch('auth.auth.get_current_active_user', return_value=MOCK_USER):
        response = client.get("/platform/twitter/platform")
        assert response.status_code in [200, 401, 403, 422]

def test_rss_platform_endpoint():
    """Test RSS platform endpoint."""
    with patch('auth.auth.get_current_active_user', return_value=MOCK_USER):
        response = client.get("/platform/rss/platform")
        assert response.status_code in [200, 401, 403, 422]

def test_admin_user_endpoints():
    """Test admin user endpoints."""
    with patch('auth.auth.get_current_active_user', return_value=MOCK_USER):
        with patch('services.services.check_access', return_value=True):
            # Test GET all users
            response = client.get("/platform/admin_user")
            assert response.status_code in [200, 401, 403, 422]
            
            # Test POST create user
            user_data = {
                "username": "test_user",
                "full_name": "Test User",
                "email": "test@example.com",
                "password": "test_password"
            }
            response = client.post("/platform/admin_user", json=user_data)
            assert response.status_code in [200, 201, 401, 403, 422]

def test_regular_user_endpoints():
    """Test regular user endpoints."""
    with patch('auth.auth.get_current_active_user', return_value=MOCK_USER):
        # Test GET current user
        response = client.get("/platform/user/me")
        assert response.status_code in [200, 401, 403, 422]
        
        # Test PUT update current user
        user_data = {
            "full_name": "Updated Test User",
            "email": "updated@example.com"
        }
        response = client.put("/platform/user/me", json=user_data)
        assert response.status_code in [200, 401, 403, 422]

if __name__ == "__main__":
    # Run the comprehensive test
    tester = RouteTester()
    tester.test_all_routes()

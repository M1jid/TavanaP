# API Route Testing Guide

This guide explains how to test all routes in your Report Data API project, including best practices for handling authentication, parameters, and different scenarios.

## 🎯 Overview

The testing framework automatically discovers and tests all routes in your FastAPI application, handling:
- Authentication requirements
- Required parameters and payloads
- Different HTTP methods (GET, POST, PUT, DELETE, PATCH)
- File uploads
- Error scenarios

## 📁 Files Created

1. **`test_all_routes.py`** - Comprehensive test suite with detailed reporting
2. **`test_routes_simple.py`** - Simple test script for CI/CD pipelines
3. **`test_requirements.txt`** - Testing dependencies
4. **`.gitlab-ci.yml`** - GitLab CI configuration
5. **`TESTING_GUIDE.md`** - This documentation

## 🚀 Quick Start

### Local Testing

```bash
# Install test dependencies
pip install -r test_requirements.txt

# Run comprehensive tests
python test_all_routes.py

# Run simple tests
python test_routes_simple.py

# Run with pytest
pytest test_routes_simple.py -v
```

### GitLab CI

The CI pipeline will automatically run tests on:
- Main branch
- Develop branch
- Merge requests

## 🔧 How It Works

### 1. Route Discovery

The framework automatically discovers all routes by:
- Scanning the FastAPI app instance
- Extracting route paths and HTTP methods
- Filtering out HEAD and OPTIONS methods

### 2. Authentication Mocking

All routes requiring authentication are tested with a mock user:

```python
MOCK_USER = User(
    id=1,
    username="test_user",
    full_name="Test User",
    email="test@example.com",
    disabled=False,
    permissions=["admin", "platform.telegram.fa.channels.create"],
    query_ids=[],
    following_channels=[],
    following_groups=[],
    following_users=[],
    accessible_urls=["http://localhost:8000"]
)
```

### 3. Parameter Generation

The framework automatically generates appropriate parameters based on route patterns:

- **Path Parameters**: Replaced with sample values (e.g., `{id}` → `1`)
- **Query Parameters**: Added based on route context (dates, limits, etc.)
- **Body Data**: Generated based on route purpose (user data, channel data, etc.)

### 4. Success Criteria

A route is considered successful if it returns:
- `200` - OK
- `201` - Created
- `202` - Accepted
- `422` - Validation Error (expected with mock data)
- `401` - Unauthorized (expected without proper auth)
- `403` - Forbidden (expected without proper permissions)
- `404` - Not Found (expected with mock data)

## 📊 Route Categories

### 1. Platform Routes

**Telegram Routes** (`/platform/fa/telegram/`)
- Channels: CRUD operations, blocking, statistics
- Groups: Similar to channels
- Trends: Overview, analysis
- Users: User management
- Daily reports: Report generation
- Word cloud: Text analysis

**Instagram Routes** (`/platform/fa/instagram/`)
- Trends: Overview analysis
- Pages: Page analysis

**Twitter Routes** (`/platform/twitter/`)
- Platform information

**RSS Routes** (`/platform/rss/`)
- Platform information

### 2. User Management Routes

**Admin Routes** (`/platform/admin_user/`)
- User CRUD operations
- User status management
- Query management

**Regular User Routes** (`/platform/user/me/`)
- Current user information
- User profile updates
- Personal query management

### 3. System Routes

- `/status` - Health check
- `/token` - Authentication
- `/satelite_channels/sources` - Satellite channel sources

## 🛠️ Customization

### Adding New Route Types

To handle new route patterns, update the `get_route_params` method:

```python
def get_route_params(self, route_path: str, method: str) -> Dict[str, Any]:
    # Add your custom parameter logic here
    if 'your_pattern' in route_path.lower():
        query_params.update({
            'your_param': 'your_value'
        })
```

### Modifying Success Criteria

Update the success criteria in the `test_route` method:

```python
# Add new success status codes
if response.status_code in [200, 201, 202, 204]:  # Added 204
    result['success'] = True
```

### Custom Mock Data

Modify the `SAMPLE_DATA` dictionary to include your specific test data:

```python
SAMPLE_DATA = {
    # Add your custom data
    "custom_param": "custom_value",
    "your_id": 123
}
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure you're running from the correct directory
   - Install all dependencies: `pip install -r requirements.txt`

2. **Authentication Errors**
   - The framework mocks authentication automatically
   - Check if your auth module is properly imported

3. **Database Errors**
   - Database operations are mocked in the test framework
   - Ensure your database handlers are properly mocked

4. **Service Errors**
   - External services (Telegram, Instagram, etc.) are mocked
   - Check if service imports are correct

### Debug Mode

For detailed debugging, modify the test script:

```python
# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Print detailed response information
print(f"Response: {response.text}")
print(f"Headers: {response.headers}")
```

## 📈 Best Practices

### 1. Test Coverage

- **Aim for 100% route coverage** - Test every endpoint
- **Test different HTTP methods** - GET, POST, PUT, DELETE, PATCH
- **Test error scenarios** - Invalid data, missing parameters

### 2. CI/CD Integration

- **Run tests on every commit** - Catch issues early
- **Use different test levels** - Unit, integration, end-to-end
- **Generate reports** - Track test results over time

### 3. Maintenance

- **Update tests when adding routes** - Keep coverage current
- **Review test results regularly** - Identify patterns in failures
- **Refactor tests as needed** - Keep them maintainable

### 4. Performance

- **Mock external services** - Avoid real API calls in tests
- **Use test databases** - Isolate test data
- **Parallel execution** - Run tests concurrently when possible

## 🔍 Understanding Test Results

### Success Indicators

- ✅ **Green checkmark**: Route responded as expected
- ⚠️ **Yellow warning**: Expected behavior (auth required, validation error)
- ❌ **Red X**: Unexpected error or failure

### Common Status Codes

- **200**: Success - Route working correctly
- **201**: Created - Resource created successfully
- **401**: Unauthorized - Authentication required (expected)
- **403**: Forbidden - Permission denied (expected)
- **404**: Not Found - Resource not found (expected with mock data)
- **422**: Validation Error - Invalid input (expected with mock data)

### Error Analysis

When routes fail, check:
1. **Route definition** - Is the route properly defined?
2. **Dependencies** - Are all required dependencies available?
3. **Authentication** - Is the auth mock working correctly?
4. **Parameters** - Are the generated parameters appropriate?

## 🚀 Advanced Usage

### Custom Test Scenarios

Create specific test scenarios for critical routes:

```python
def test_critical_user_creation():
    """Test user creation with specific data."""
    with patch('auth.auth.get_current_active_user', return_value=ADMIN_USER):
        response = client.post("/platform/admin_user", json={
            "username": "new_user",
            "full_name": "New User",
            "email": "new@example.com",
            "password": "secure_password"
        })
        assert response.status_code in [200, 201]
```

### Integration Tests

For more comprehensive testing, create integration tests that:
- Use real database connections (test database)
- Test complete workflows
- Verify data persistence
- Test error handling

### Load Testing

For performance testing, consider:
- Using tools like `locust` or `pytest-benchmark`
- Testing with realistic data volumes
- Measuring response times
- Identifying bottlenecks

## 📞 Support

If you encounter issues:

1. **Check the logs** - Look for specific error messages
2. **Review the route definition** - Ensure it's properly configured
3. **Test manually** - Use tools like Postman or curl
4. **Check dependencies** - Ensure all imports are available
5. **Review authentication** - Verify auth requirements

Remember: The goal is to ensure all routes are accessible and respond appropriately, not to test business logic (that's for unit tests).

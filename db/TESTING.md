# Database Service Testing Guide

This document explains how to test the database service without affecting your production data.

## Overview

The testing setup provides:
- **Separate Test Database**: Isolated from production data
- **Automatic Test Data Management**: Creates, uses, and cleans up test data
- **Comprehensive Test Coverage**: Tests all API endpoints
- **Docker Integration**: Easy setup with docker-compose

## Quick Start

### 1. Run Tests with Docker (Recommended)

```bash
# Start the test environment
docker-compose up test_db -d

# Run tests
docker-compose run --rm db_services_test

# Or run tests directly in the db directory
cd services/db
docker-compose run --rm db_services_test python run_tests.py
```

### 2. Run Tests Locally

```bash
cd services/db

# Install dependencies
pip install -r requirements.txt

# Set up test environment
export TESTING=true
export TEST_POSTGRES_DB=test_db
export TEST_POSTGRES_HOST=localhost

# Run tests
python run_tests.py
```

## Test Structure

### Test Files
- `test_telegram_peers.py` - Tests for Telegram Peers API
- `test_telegram_channels.py` - Tests for Telegram Channels API  
- `test_users.py` - Tests for Users API
- `conftest.py` - Test configuration and fixtures

### Test Database
- **Production**: Uses `POSTGRES_DB` from environment
- **Testing**: Uses `test_db` database
- **Isolation**: Each test runs in a transaction that gets rolled back

## Test Data Management

### Automatic Cleanup
- Test data is automatically created before each test
- All changes are rolled back after each test
- No test data persists between test runs

### Test Fixtures
```python
# Sample data fixtures available:
sample_user_data          # User test data
sample_telegram_channel_data  # Telegram channel test data
sample_telegram_peer_data     # Telegram peer test data

# Database fixtures:
sample_user              # Creates user in database
sample_telegram_channel  # Creates channel in database
sample_telegram_peer     # Creates peer in database
```

## Running Specific Tests

### Run All Tests
```bash
python -m pytest
```

### Run Specific Test File
```bash
python -m pytest test_telegram_peers.py
```

### Run Specific Test Class
```bash
python -m pytest test_telegram_peers.py::TestTelegramPeersAPI
```

### Run Specific Test Method
```bash
python -m pytest test_telegram_peers.py::TestTelegramPeersAPI::test_get_telegram_peer_by_id
```

### Run Tests with Coverage
```bash
python -m pytest --cov=. --cov-report=html
```

## Test Coverage

The test suite covers:

### Telegram Peers API
- ✅ GET /telegram/peers (all, by ID, by peer_id, by username, by URL)
- ✅ POST /telegram/peers (create new peer)
- ✅ PUT /telegram/peers (update existing peer)
- ✅ DELETE /telegram/peers (delete peer)
- ✅ Error handling (not found, duplicate data)

### Telegram Channels API
- ✅ GET /telegram/channels (all, by ID, by key, by value, by tag)
- ✅ POST /telegram/channels (create new channel)
- ✅ PUT /telegram/channels (update existing channel)
- ✅ DELETE /telegram/channels (delete channel)
- ✅ Error handling (not found, duplicate data)

### Users API
- ✅ GET /users (all, by ID, by username, by email)
- ✅ POST /users (create new user)
- ✅ PUT /users (update existing user)
- ✅ DELETE /users (delete user)
- ✅ Error handling (not found, duplicate data)

## Environment Variables

### Production
```bash
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_production_db
POSTGRES_HOST=localhost
```

### Testing
```bash
TESTING=true
TEST_POSTGRES_DB=test_db
TEST_POSTGRES_HOST=localhost
```

## Best Practices

### 1. Never Test Against Production Data
- Always use the test database
- Set `TESTING=true` environment variable
- Verify you're connected to test database

### 2. Use Test Fixtures
```python
def test_something(async_client, sample_user):
    # sample_user is automatically created and cleaned up
    response = await async_client.get(f"/users/{sample_user.id}")
    assert response.status_code == 200
```

### 3. Test Both Success and Error Cases
```python
# Test success case
response = await async_client.get("/users/1")
assert response.status_code == 200

# Test error case
response = await async_client.get("/users/99999")
assert response.status_code == 404
```

### 4. Use Descriptive Test Names
```python
def test_create_user_with_duplicate_email_should_fail():
    # Clear test name explains what is being tested
```

### 5. Clean Up After Tests
- Tests automatically clean up via transaction rollback
- No manual cleanup needed
- Each test starts with a clean database state

## Troubleshooting

### Database Connection Issues
```bash
# Check if test database is running
docker-compose ps test_db

# Restart test database
docker-compose restart test_db

# Check database logs
docker-compose logs test_db
```

### Test Failures
```bash
# Run tests with verbose output
python -m pytest -v

# Run specific failing test
python -m pytest test_file.py::TestClass::test_method -v -s

# Check test coverage
python -m pytest --cov=. --cov-report=term-missing
```

### Environment Issues
```bash
# Verify environment variables
echo $TESTING
echo $TEST_POSTGRES_DB
echo $TEST_POSTGRES_HOST

# Reset environment
unset TESTING
unset TEST_POSTGRES_DB
unset TEST_POSTGRES_HOST
```

## Continuous Integration

### GitHub Actions Example
```yaml
name: Test Database Service

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:latest
        env:
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
          
      - name: Install dependencies
        run: |
          cd services/db
          pip install -r requirements.txt
          
      - name: Run tests
        env:
          TESTING: true
          TEST_POSTGRES_DB: test_db
          TEST_POSTGRES_HOST: localhost
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
        run: |
          cd services/db
          python run_tests.py
```

## Security Considerations

### Test Data Isolation
- Test database is completely separate from production
- No production credentials used in tests
- Test data is automatically cleaned up

### Environment Variables
- Never commit real credentials to version control
- Use `.env` files for local development
- Use CI/CD secrets for production credentials

## Performance Testing

### Database Performance
```python
import time

def test_database_performance(async_client):
    start_time = time.time()
    
    # Run database operation
    response = await async_client.get("/users")
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    assert response.status_code == 200
    assert execution_time < 1.0  # Should complete within 1 second
```

### Load Testing
```python
import asyncio

async def test_concurrent_requests(async_client):
    # Test concurrent requests
    tasks = [
        async_client.get("/users") for _ in range(10)
    ]
    
    responses = await asyncio.gather(*tasks)
    
    for response in responses:
        assert response.status_code == 200
```

## Conclusion

This testing setup ensures that:
1. **Your production data is safe** - Tests use a separate database
2. **Tests are reliable** - Each test runs in isolation
3. **Coverage is comprehensive** - All API endpoints are tested
4. **Setup is easy** - Docker integration makes it simple to run tests

Always run tests before deploying to production to ensure your changes work correctly! 
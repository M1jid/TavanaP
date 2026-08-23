#!/usr/bin/env python3
"""
Test runner script for the database service.
This script sets up a test environment and runs all tests with proper database isolation.
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def setup_test_environment():
    """Set up the test environment variables."""
    os.environ["TESTING"] = "true"
    os.environ["TEST_POSTGRES_DB"] = "test_db"
    os.environ["TEST_POSTGRES_HOST"] = "localhost"
    
    # Ensure we're using test database
    print("Setting up test environment...")
    print(f"TESTING: {os.environ.get('TESTING')}")
    print(f"TEST_POSTGRES_DB: {os.environ.get('TEST_POSTGRES_DB')}")
    print(f"TEST_POSTGRES_HOST: {os.environ.get('TEST_POSTGRES_HOST')}")


def wait_for_database(max_retries=30, delay=2):
    """Wait for the test database to be ready."""
    import psycopg2
    from app.config import settings
    
    print("Waiting for test database to be ready...")
    
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(settings.test_database_url)
            conn.close()
            print("Test database is ready!")
            return True
        except psycopg2.OperationalError as e:
            print(f"Attempt {attempt + 1}/{max_retries}: Database not ready yet... ({e})")
            if attempt < max_retries - 1:
                time.sleep(delay)
    
    print("Failed to connect to test database after maximum retries")
    return False


def run_tests():
    """Run the test suite."""
    print("Running tests...")
    
    # Run pytest with coverage
    cmd = [
        sys.executable, "-m", "pytest",
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--cov=.",  # Coverage report
        "--cov-report=term-missing",  # Show missing lines
        "--cov-report=html:htmlcov",  # HTML coverage report
        "--asyncio-mode=auto",  # Auto-detect async tests
        "tests/",  # Test directory
        "--ignore=tests/__pycache__"  # Ignore cache
    ]
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode


def cleanup():
    """Clean up test artifacts."""
    print("Cleaning up test artifacts...")
    
    # Remove coverage files if they exist
    coverage_files = [
        ".coverage",
        "htmlcov",
        ".pytest_cache"
    ]
    
    for file_path in coverage_files:
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                import shutil
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)
            print(f"Removed: {file_path}")


def main():
    """Main function to run the test suite."""
    print("=" * 60)
    print("DATABASE SERVICE TEST SUITE")
    print("=" * 60)
    
    try:
        # Set up test environment
        setup_test_environment()
        
        # Wait for database
        if not wait_for_database():
            print("ERROR: Could not connect to test database")
            sys.exit(1)
        
        # Run tests
        exit_code = run_tests()
        
        # Clean up
        cleanup()
        
        print("=" * 60)
        if exit_code == 0:
            print("✅ ALL TESTS PASSED!")
        else:
            print("❌ SOME TESTS FAILED!")
        print("=" * 60)
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"Error running tests: {e}")
        cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Simple script to run route tests with different options.

Usage:
    python run_tests.py                    # Run simple tests
    python run_tests.py --comprehensive    # Run comprehensive tests
    python run_tests.py --pytest          # Run with pytest
    python run_tests.py --help            # Show help
"""

import argparse
import sys
import subprocess
import os

def run_simple_tests():
    """Run simple route tests."""
    print("🧪 Running simple route tests...")
    try:
        result = subprocess.run([sys.executable, "test_routes_simple.py"], 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        return result.returncode
    except Exception as e:
        print(f"❌ Error running simple tests: {e}")
        return 1

def run_comprehensive_tests():
    """Run comprehensive route tests."""
    print("🧪 Running comprehensive route tests...")
    try:
        result = subprocess.run([sys.executable, "test_all_routes.py"], 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        return result.returncode
    except Exception as e:
        print(f"❌ Error running comprehensive tests: {e}")
        return 1

def run_pytest():
    """Run tests with pytest."""
    print("🧪 Running tests with pytest...")
    try:
        result = subprocess.run([sys.executable, "-m", "pytest", "test_routes_simple.py", "-v"], 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        return result.returncode
    except Exception as e:
        print(f"❌ Error running pytest: {e}")
        return 1

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    try:
        import fastapi
        import pytest
        import httpx
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r test_requirements.txt")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run route tests for the Report Data API")
    parser.add_argument("--comprehensive", action="store_true", 
                       help="Run comprehensive tests with detailed reporting")
    parser.add_argument("--pytest", action="store_true", 
                       help="Run tests using pytest")
    parser.add_argument("--check-deps", action="store_true", 
                       help="Check if dependencies are installed")
    
    args = parser.parse_args()
    
    # Check dependencies first
    if not check_dependencies():
        return 1
    
    if args.check_deps:
        return 0
    
    # Run appropriate tests
    if args.comprehensive:
        return run_comprehensive_tests()
    elif args.pytest:
        return run_pytest()
    else:
        return run_simple_tests()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

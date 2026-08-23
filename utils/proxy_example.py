"""
Example usage of the ProxyHandler class with Xray.
"""

from proxy_handler import ProxyHandler
from proxy_config import get_combined_proxy_configs, get_xray_configs
import time
import json
import requests
from datetime import datetime


def example_basic_usage():
    """Example of basic proxy handler usage."""
    
    print("=== Basic Proxy Handler Usage ===")
    
    # Get Xray configurations
    xray_configs = get_xray_configs()
    print(f"Loaded {len(xray_configs)} Xray configurations")
    
    if not xray_configs:
        print("No Xray configurations available")
        return
    
    # Initialize proxy handler
    with ProxyHandler(xray_configs) as proxy_handler:
        # Start the proxy
        print("\n=== Starting Proxy ===")
        if proxy_handler.start_proxy():
            print("✅ Proxy started successfully!")
            
            # Get proxy information
            proxy_info = proxy_handler.get_current_proxy_info()
            if proxy_info:
                print(f"Current config: {proxy_info['config']}")
                print(f"SOCKS proxy: {proxy_info['socks_proxy']}")
                print(f"HTTP proxy: {proxy_info['http_proxy']}")
                print(f"Is running: {proxy_info['is_running']}")
            
            # Test proxy with a simple request
            print("\n=== Testing Proxy Connection ===")
            try:
                proxies = {
                    'http': proxy_info['http_proxy'],
                    'https': proxy_info['http_proxy']
                }
                response = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=10)
                
                if response.status_code == 200:
                    print("✅ Proxy connection successful!")
                    print(f"Response: {response.json()}")
                else:
                    print("❌ Proxy connection failed!")
            except Exception as e:
                print(f"❌ Proxy connection error: {e}")
        else:
            print("❌ Failed to start proxy!")
            return
        
        # Get proxy statistics
        print("\n=== Proxy Statistics ===")
        stats = proxy_handler.get_proxy_stats()
        print(json.dumps(stats, indent=2, default=str))


def example_with_rotation():
    """Example with proxy rotation enabled."""
    
    print("\n=== Proxy Rotation Example ===")
    
    xray_configs = get_xray_configs()
    if not xray_configs:
        print("No Xray configurations available")
        return
    
    # Initialize with rotation enabled
    with ProxyHandler(
        xray_configs,
        rotation_enabled=True,
        rotation_interval=30  # Rotate every 30 seconds
    ) as proxy_handler:
        
        print("Proxy rotation enabled - will rotate every 30 seconds")
        
        # Start initial proxy
        if not proxy_handler.start_proxy():
            print("❌ Failed to start initial proxy")
            return
        
        # Make requests over time to see rotation in action
        for i in range(6):
            print(f"\n--- Request {i+1} ---")
            
            proxy_info = proxy_handler.get_current_proxy_info()
            if proxy_info and proxy_info['is_running']:
                print(f"Current config: {proxy_info['config']}")
                print(f"Proxy: {proxy_info['http_proxy']}")
                
                # Test the proxy
                try:
                    proxies = {
                        'http': proxy_info['http_proxy'],
                        'https': proxy_info['http_proxy']
                    }
                    response = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"✅ Success - IP: {data.get('origin', 'unknown')}")
                    else:
                        print(f"❌ Request failed: {response.status_code}")
                except Exception as e:
                    print(f"❌ Request error: {e}")
            else:
                print("❌ Proxy not running")
            
            # Show current proxy stats
            stats = proxy_handler.get_proxy_stats()
            print(f"Healthy proxies: {stats['healthy_proxies']}/{stats['total_proxies']}")
            
            time.sleep(10)  # Wait 10 seconds between requests


def example_manual_rotation():
    """Example with manual proxy rotation."""
    
    print("\n=== Manual Rotation Example ===")
    
    xray_configs = get_xray_configs()
    if not xray_configs:
        print("No Xray configurations available")
        return
    
    with ProxyHandler(xray_configs, rotation_enabled=False) as proxy_handler:
        print("Manual rotation mode - rotation disabled")
        
        # Start initial proxy
        if not proxy_handler.start_proxy():
            print("❌ Failed to start initial proxy")
            return
        
        # Test initial proxy
        proxy_info = proxy_handler.get_current_proxy_info()
        print(f"Initial config: {proxy_info['config']}")
        
        # Test the proxy
        try:
            proxies = {
                'http': proxy_info['http_proxy'],
                'https': proxy_info['http_proxy']
            }
            response = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Initial proxy working - IP: {data.get('origin', 'unknown')}")
            else:
                print(f"❌ Initial proxy failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Initial proxy error: {e}")
        
        # Manual rotation
        print("\n--- Manual Rotation ---")
        if proxy_handler.rotate_proxy():
            print("✅ Rotation successful!")
            
            # Test new proxy
            proxy_info = proxy_handler.get_current_proxy_info()
            print(f"New config: {proxy_info['config']}")
            
            try:
                proxies = {
                    'http': proxy_info['http_proxy'],
                    'https': proxy_info['http_proxy']
                }
                response = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ New proxy working - IP: {data.get('origin', 'unknown')}")
                else:
                    print(f"❌ New proxy failed: {response.status_code}")
            except Exception as e:
                print(f"❌ New proxy error: {e}")
        else:
            print("❌ Rotation failed!")


def example_proxy_statistics():
    """Example of monitoring proxy statistics."""
    
    print("\n=== Proxy Statistics Example ===")
    
    xray_configs = get_xray_configs()
    if not xray_configs:
        print("No Xray configurations available")
        return
    
    with ProxyHandler(xray_configs) as proxy_handler:
        print("Testing multiple proxy configurations...")
        
        # Test each configuration
        for i, config in enumerate(xray_configs[:3]):  # Test first 3 configs
            print(f"\nTesting config {i+1}: {config}")
            
            # Start proxy
            if proxy_handler.start_proxy():
                print(f"✅ Started proxy with config: {config}")
                
                # Test the proxy
                proxy_info = proxy_handler.get_current_proxy_info()
                if proxy_info:
                    try:
                        proxies = {
                            'http': proxy_info['http_proxy'],
                            'https': proxy_info['http_proxy']
                        }
                        response = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=5)
                        
                        if response.status_code == 200:
                            print(f"✅ Request successful")
                        else:
                            print(f"❌ Request failed: {response.status_code}")
                    except Exception as e:
                        print(f"❌ Request error: {e}")
            else:
                print(f"❌ Failed to start proxy with config: {config}")
            
            # Rotate to next config
            if i < len(xray_configs) - 1:
                proxy_handler.rotate_proxy()
        
        # Get detailed statistics
        print("\n=== Detailed Statistics ===")
        stats = proxy_handler.get_proxy_stats()
        
        print(f"Total proxies: {stats['total_proxies']}")
        print(f"Healthy proxies: {stats['healthy_proxies']}")
        print(f"Failed proxies: {stats['failed_proxies']}")
        print(f"Current proxy: {stats['current_proxy']}")
        print(f"Rotation enabled: {stats['rotation_enabled']}")
        print(f"Is running: {stats['is_running']}")
        
        print("\n=== Proxy Details ===")
        for config, details in stats['proxy_details'].items():
            print(f"Config: {config}")
            print(f"  Success count: {details['success_count']}")
            print(f"  Failure count: {details['failure_count']}")
            print(f"  Is healthy: {details['is_healthy']}")
            print(f"  Last success: {details['last_success']}")
            print(f"  Last failure: {details['last_failure']}")
            print()


def example_error_handling():
    """Example with proper error handling."""
    
    print("\n=== Error Handling Example ===")
    
    # Test with invalid configurations
    invalid_configs = [
        "invalid-config.json",
        "nonexistent-config.json"
    ]
    
    try:
        with ProxyHandler(invalid_configs) as proxy_handler:
            if proxy_handler.start_proxy():
                print("✅ Unexpected success with invalid configs")
            else:
                print("❌ Expected failure with invalid configs")
                
    except Exception as e:
        print(f"❌ Error as expected: {e}")
    
    # Test with valid configurations
    xray_configs = get_xray_configs()
    if not xray_configs:
        print("No valid Xray configurations available")
        return
    
    try:
        with ProxyHandler(xray_configs) as proxy_handler:
            # Test proxy startup
            if proxy_handler.start_proxy():
                print("✅ Proxy started successfully")
                
                # Test proxy info
                proxy_info = proxy_handler.get_current_proxy_info()
                if proxy_info:
                    print(f"✅ Proxy info available: {proxy_info['config']}")
                else:
                    print("❌ No proxy info available")
            else:
                print("❌ Failed to start proxy")
                
    except Exception as e:
        print(f"❌ Proxy handler error: {e}")


def example_proxy_recovery():
    """Example of proxy recovery mechanism."""
    
    print("\n=== Proxy Recovery Example ===")
    
    xray_configs = get_xray_configs()
    if not xray_configs:
        print("No Xray configurations available")
        return
    
    with ProxyHandler(
        xray_configs,
        rotation_enabled=False,
        failure_threshold=1  # Mark as failed after 1 failure
    ) as proxy_handler:
        
        print("Testing proxy recovery mechanism...")
        
        # Start proxy
        if proxy_handler.start_proxy():
            print("✅ Initial proxy started")
            
            # Get initial stats
            stats = proxy_handler.get_proxy_stats()
            print(f"Initial healthy proxies: {stats['healthy_proxies']}")
            
            # Simulate failures by stopping the proxy
            print("Simulating proxy failure...")
            proxy_handler.stop_proxy()
            
            # Check stats after failure
            stats = proxy_handler.get_proxy_stats()
            print(f"After failure - healthy proxies: {stats['healthy_proxies']}")
            
            # Try to recover failed proxies
            recovered = proxy_handler.recover_failed_proxies()
            print(f"Recovered proxies: {recovered}")
            
            # Check stats after recovery
            stats = proxy_handler.get_proxy_stats()
            print(f"After recovery - healthy proxies: {stats['healthy_proxies']}")
        else:
            print("❌ Failed to start initial proxy")


if __name__ == "__main__":
    print("Xray Proxy Handler Example Usage")
    print("=" * 50)
    
    # Run basic examples
    example_basic_usage()
    
    print("\n" + "=" * 50)
    print("Rotation Example")
    print("=" * 50)
    example_with_rotation()
    
    print("\n" + "=" * 50)
    print("Manual Rotation Example")
    print("=" * 50)
    example_manual_rotation()
    
    print("\n" + "=" * 50)
    print("Statistics Example")
    print("=" * 50)
    example_proxy_statistics()
    
    print("\n" + "=" * 50)
    print("Error Handling Example")
    print("=" * 50)
    example_error_handling()
    
    print("\n" + "=" * 50)
    print("Proxy Recovery Example")
    print("=" * 50)
    example_proxy_recovery()
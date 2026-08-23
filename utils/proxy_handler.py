"""
Proxy handler class for managing Xray proxy connections with rotation.
"""

import subprocess
import logging
import time
import random
import threading
import signal
import os
from typing import Optional, Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ProxyHandler:
    """
    Proxy handler class using Xray subprocess to manage proxy connections.
    
    This class provides methods to:
    - Manage multiple Xray proxy configurations
    - Rotate between proxies automatically
    - Monitor proxy health and performance
    - Handle proxy failures and recovery
    - Provide proxy information (IP and port)
    """
    
    def __init__(
        self,
        xray_configs: List[str],
        rotation_enabled: bool = True,
        timeout: int = 30,
        max_retries: int = 3,
        rotation_interval: int = 300,
        pool_size: int = 5,
        failure_threshold: int = 3,
        xray_executable_path: str = './proxy/xray',
        xray_config_dir: str = './proxy',
        socks_port: int = 1080,
        http_port: int = 8080
    ):
        """
        Initialize proxy handler with connection parameters.
        
        Args:
            xray_configs: List of Xray configuration file names
            rotation_enabled: Whether to enable automatic proxy rotation
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            rotation_interval: Time interval for proxy rotation (seconds)
            pool_size: Maximum number of active proxies
            failure_threshold: Number of failures before marking proxy as failed
            xray_executable_path: Path to Xray executable
            xray_config_dir: Directory containing Xray configuration files
            socks_port: SOCKS proxy port
            http_port: HTTP proxy port
        """
        self.xray_configs = xray_configs
        self.rotation_enabled = rotation_enabled
        self.timeout = timeout
        self.max_retries = max_retries
        self.rotation_interval = rotation_interval
        self.pool_size = pool_size
        self.failure_threshold = failure_threshold
        self.xray_executable_path = xray_executable_path
        self.xray_config_dir = xray_config_dir
        self.socks_port = socks_port
        self.http_port = http_port
        
        # Internal state
        self.current_config = None
        self.current_process = None
        self.proxy_stats = {}
        self.failed_proxies = {}
        self.last_rotation = time.time()
        self.running = False
        self.rotation_thread = None
        
        # Initialize proxy pool
        self._initialize_proxy_pool()
        
        # Start rotation thread if enabled
        if self.rotation_enabled:
            self._start_rotation_thread()
    
    def _initialize_proxy_pool(self):
        """Initialize the proxy pool with available configurations."""
        # Filter valid configurations
        valid_configs = []
        for config in self.xray_configs:
            config_path = os.path.join(self.xray_config_dir, config)
            if os.path.exists(config_path):
                valid_configs.append(config)
                self.proxy_stats[config] = {
                    'success_count': 0,
                    'failure_count': 0,
                    'last_used': None,
                    'last_success': None,
                    'last_failure': None,
                    'is_healthy': True
                }
            else:
                logger.warning(f"Configuration file not found: {config_path}")
        
        # Shuffle and limit pool size
        random.shuffle(valid_configs)
        self.xray_configs = valid_configs[:]
        
        if self.xray_configs:
            self.current_config = self.xray_configs[0]
            logger.info(f"Initialized proxy pool with {len(self.xray_configs)} configurations")
        else:
            logger.error("No valid Xray configurations found")
    
    def _start_rotation_thread(self):
        """Start the rotation monitoring thread."""
        if self.rotation_thread and self.rotation_thread.is_alive():
            return
        
        self.running = True
        self.rotation_thread = threading.Thread(target=self._rotation_monitor, daemon=True)
        self.rotation_thread.start()
        logger.info("Started proxy rotation monitoring thread")
    
    def _rotation_monitor(self):
        """Monitor and handle automatic proxy rotation."""
        while self.running:
            try:
                if self.should_rotate():
                    logger.info("Automatic rotation triggered")
                    self.rotate_proxy()
                time.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logger.error(f"Error in rotation monitor: {e}")
                time.sleep(30)  # Wait longer on error
    
    def get_current_proxy_info(self) -> Optional[Dict[str, Any]]:
        """
        Get current proxy information (IP and port).
        
        Returns:
            Dict[str, Any]: Proxy information with IP and ports
        """
        if not self.current_config:
            return None
        
        return {
            'config': self.current_config,
            'socks_port': self.socks_port,
            'http_port': self.http_port,
            'socks_proxy': f'127.0.0.1:{10808}',
            'http_proxy': f'127.0.0.1:{10808}',
            'is_running': True #self.current_process is not None and self.current_process.poll() is None
        }
    
    def start_proxy(self) -> bool:
        """
        Start the current proxy configuration.
        
        Returns:
            bool: True if proxy started successfully
        """
        if not self.current_config:
            logger.error("No proxy configuration available")
            return False
        
        # Stop existing proxy if running
        self.stop_proxy()
        
        try:
            config_path = os.path.join(self.xray_config_dir, self.current_config)
            
            # Start Xray process
            self.current_process = subprocess.Popen(
                [self.xray_executable_path, '-config', config_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            # Wait a moment for startup
            time.sleep(2)
            
            # Check if process is still running
            if self.current_process.poll() is None:
                logger.info(f"Started Xray proxy with config: {self.current_config}")
                self.mark_proxy_success(self.current_config)
                return True
            else:
                logger.error(f"Failed to start Xray proxy with config: {self.current_config}")
                self.mark_proxy_failure(self.current_config)
                return False
                
        except Exception as e:
            logger.error(f"Error starting proxy: {e}")
            self.mark_proxy_failure(self.current_config)
            return False
    
    def stop_proxy(self):
        """Stop the current proxy process."""
        if self.current_process:
            try:
                # Terminate the process group
                if os.name != 'nt':
                    os.killpg(os.getpgid(self.current_process.pid), signal.SIGTERM)
                else:
                    self.current_process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.current_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown fails
                    if os.name != 'nt':
                        os.killpg(os.getpgid(self.current_process.pid), signal.SIGKILL)
                    else:
                        self.current_process.kill()
                
                logger.info("Stopped Xray proxy")
            except Exception as e:
                logger.error(f"Error stopping proxy: {e}")
            finally:
                self.current_process = None
    
    def rotate_proxy(self) -> bool:
        """
        Rotate to the next available proxy configuration.
        
        Returns:
            bool: True if rotation was successful
        """
        if not self.xray_configs:
            logger.error("No proxy configurations available")
            return False
        
        try:
            # Find next healthy proxy
            current_index = self.xray_configs.index(self.current_config) if self.current_config in self.xray_configs else -1
            next_index = (current_index + 1) % len(self.xray_configs)
            
            # Update current config
            self.current_config = self.xray_configs[next_index]
            self.last_rotation = time.time()
            
            # Start new proxy
            success = self.start_proxy()
            
            if success:
                logger.info(f"Rotated to proxy config: {self.current_config}")
                return True
            else:
                logger.error(f"Failed to start proxy with config: {self.current_config}")
                return False
                
        except Exception as e:
            logger.error(f"Error rotating proxy: {e}")
            return False
    
    def should_rotate(self) -> bool:
        """
        Check if proxy should be rotated based on time interval.
        
        Returns:
            bool: True if rotation is needed
        """
        if not self.rotation_enabled:
            return False
        
        time_since_rotation = time.time() - self.last_rotation
        return time_since_rotation >= self.rotation_interval
    
    def mark_proxy_failure(self, config: str):
        """
        Mark a proxy configuration as failed and update statistics.
        
        Args:
            config: Failed proxy configuration name
        """
        if config in self.proxy_stats:
            self.proxy_stats[config]['failure_count'] += 1
            self.proxy_stats[config]['last_failure'] = datetime.now()
            self.proxy_stats[config]['is_healthy'] = False
            
            if self.proxy_stats[config]['failure_count'] >= self.failure_threshold:
                self.failed_proxies[config] = datetime.now()
                logger.warning(f"Proxy marked as failed: {config}")
    
    def mark_proxy_success(self, config: str):
        """
        Mark a proxy configuration as successful and update statistics.
        
        Args:
            config: Successful proxy configuration name
        """
        if config in self.proxy_stats:
            self.proxy_stats[config]['success_count'] += 1
            self.proxy_stats[config]['last_success'] = datetime.now()
            self.proxy_stats[config]['last_used'] = datetime.now()
            self.proxy_stats[config]['is_healthy'] = True
            
            # Remove from failed list if it was there
            if config in self.failed_proxies:
                del self.failed_proxies[config]
                logger.info(f"Proxy recovered: {config}")
    
    def get_proxy_stats(self) -> Dict[str, Any]:
        """
        Get proxy statistics and health information.
        
        Returns:
            Dict[str, Any]: Proxy statistics
        """
        healthy_count = sum(1 for stats in self.proxy_stats.values() if stats['is_healthy'])
        
        return {
            'total_proxies': len(self.xray_configs),
            'healthy_proxies': healthy_count,
            'failed_proxies': len(self.failed_proxies),
            'current_proxy': self.current_config,
            'last_rotation': self.last_rotation,
            'rotation_enabled': self.rotation_enabled,
            'is_running': self.current_process is not None and self.current_process.poll() is None,
            'proxy_details': self.proxy_stats
        }
    
    def get_available_proxies(self) -> List[str]:
        """
        Get list of available proxy configurations (all except failed ones).
        
        Returns:
            List[str]: List of available proxy configuration names
        """
        available_proxies = []
        for config in self.xray_configs:
            if config not in self.failed_proxies and self.proxy_stats.get(config, {}).get('is_healthy', True):
                available_proxies.append(config)
        return available_proxies
    
    def recover_failed_proxies(self) -> int:
        """
        Attempt to recover failed proxies by removing them from failed list.
        
        Returns:
            int: Number of proxies recovered
        """
        recovered = 0
        current_time = datetime.now()
        
        for config, failure_time in list(self.failed_proxies.items()):
            # Check if enough time has passed for recovery
            if (current_time - failure_time).total_seconds() >= self.failure_threshold * 60:  # 1 minute per failure
                del self.failed_proxies[config]
                if config in self.proxy_stats:
                    self.proxy_stats[config]['is_healthy'] = True
                recovered += 1
                logger.info(f"Recovered proxy: {config}")
        
        return recovered
    
    def stop(self):
        """Stop all proxies and cleanup resources."""
        self.running = False
        
        # Stop rotation thread
        if self.rotation_thread and self.rotation_thread.is_alive():
            self.rotation_thread.join(timeout=5)
        
        # Stop current proxy
        self.stop_proxy()
        
        logger.info("Proxy handler stopped")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
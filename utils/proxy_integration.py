"""
Integration examples for ProxyHandler with various services and applications using Xray.
"""

import requests
import json
import time
import logging
from typing import Optional, Dict, List, Any
from proxy_handler import ProxyHandler
from proxy_config import get_combined_proxy_configs, get_xray_configs

logger = logging.getLogger(__name__)


class TwitterProxyIntegration:
    """Integration class for Twitter API with Xray proxy support."""
    
    def __init__(self, proxy_handler: ProxyHandler):
        """
        Initialize Twitter integration with proxy handler.
        
        Args:
            proxy_handler: ProxyHandler instance
        """
        self.proxy_handler = proxy_handler
        self.base_url = "https://api.x.com"
        self.guest_token = None
        self.token_created_time = None
    
    def get_guest_token(self) -> Optional[str]:
        """
        Get a fresh guest token from Twitter's guest token endpoint.
        
        Returns:
            str: Guest token or None if failed
        """
        url = f"{self.base_url}/1.1/guest/activate.json"
        headers = {
            "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
            "content-type": "application/x-www-form-urlencoded",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
        }
        
        try:
            # Get proxy info
            proxy_info = self.proxy_handler.get_current_proxy_info()
            if not proxy_info or not proxy_info['is_running']:
                logger.error("No proxy available")
                return None
            
            proxies = {
                'http': proxy_info['http_proxy'],
                'https': proxy_info['http_proxy']
            }
            
            response = requests.post(url, headers=headers, proxies=proxies, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.guest_token = data.get('guest_token')
                self.token_created_time = time.time()
                logger.info(f"Got guest token: {self.guest_token}")
                return self.guest_token
            else:
                logger.error(f"Failed to get guest token: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting guest token: {e}")
            return None
    
    def get_user_tweets(self, user_id: str, count: int = 20) -> Optional[Dict]:
        """
        Fetch tweets for a specific user ID using proxy.
        
        Args:
            user_id: Twitter user ID
            count: Number of tweets to fetch
            
        Returns:
            Dict: JSON response containing tweets
        """
        # Get or refresh guest token
        if not self.guest_token or (time.time() - self.token_created_time) > 7200:
            self.get_guest_token()
        
        if not self.guest_token:
            logger.error("No guest token available")
            return None
        
        url = f"{self.base_url}/graphql/Z15UW_bggbnuLrrt0-jOGA/UserTweets"
        
        variables = {
            "userId": user_id,
            "count": min(count, 100),
            "includePromotedContent": True,
            "withQuickPromoteEligibilityTweetFields": True,
            "withVoice": True
        }
        
        params = {
            "variables": json.dumps(variables),
            "features": '{"rweb_video_screen_enabled":false,"payments_enabled":false,"profile_label_improvements_pcf_label_in_post_enabled":true,"responsive_web_profile_redirect_enabled":false,"rweb_tipjar_consumption_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"premium_content_api_read_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"responsive_web_grok_analyze_button_fetch_trends_enabled":false,"responsive_web_grok_analyze_post_followups_enabled":false,"responsive_web_jetfuel_frame":true,"responsive_web_grok_share_attachment_enabled":true,"articles_preview_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"responsive_web_grok_show_grok_translated_post":false,"responsive_web_grok_analysis_button_from_backend":true,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_grok_image_annotation_enabled":true,"responsive_web_grok_imagine_annotation_enabled":true,"responsive_web_grok_community_note_auto_translation_is_enabled":false,"responsive_web_enhance_cards_enabled":false}',
            "fieldToggles": '{"withArticlePlainText":false}'
        }
        
        headers = {
            "accept": "*/*",
            "accept-language": "en-GB,en;q=0.9,fa-IR;q=0.8,fa;q=0.7,en-US;q=0.6",
            "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
            "content-type": "application/json",
            "cookie": "guest_id_marketing=v1%3A176017871023898634; guest_id_ads=v1%3A176017871023898634; guest_id=v1%3A176017871023898634; __cuid=a700bacd36b6444f92bdf8c6740304f8; gt=1979780046685388973; att=1-9K8EjpdMZe3jlmoEUyoJ9U4WYcK52YUoW4pZ6ga9; _ga=GA1.1.1370086502.1760856812; _ga_BLY4P7T5KW=GS2.1.s1760856812$o1$g0$t1760856820$j52$l0$h0; personalization_id=\"v1_Pg5RJqysUoCIkGoQuISPWA==\"; __cf_bm=YexL4.v8y1CCL6QCI_PXfYQPt96_2gde.Prn_R4MsnU-1760856506.4704006-1.0.1.1-z4aPcUzOnlYDP8LB5KhBhICFWzmiOrzJYfdkAyNrb8Hg_gwSITqw9_N9.FJ7ikuD5QqZaEbq5wj8v3eREsPyLMQIIuQR5oRYaDCGtAqHWXm3u3HXY0EQqhGCMYYlGsAo",
            "origin": "https://x.com",
            "priority": "u=1, i",
            "referer": "https://x.com/",
            "sec-ch-ua": "\"Google Chrome\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            "x-client-transaction-id": "FkyXgERkdvcGJoc7RQL2nB4/c5Fvz4NtCUZVqMIew66iObPHde+zBChSYHF0M4KOFZ4tsxIvr76GLXBNKv5zlB/K4G52FQ",
            "x-guest-token": self.guest_token,
            "x-twitter-active-user": "yes",
            "x-twitter-client-language": "en-GB",
            "x-xp-forwarded-for": "738544498585baa438ce988b3c2d5ceef99a057105216f62b1e0205274b9a8748d473c2ddc88656b173f991e824537ceb80c6317852c81d3c60efc2f03ca0b22bb4fe069269409e35819de9e2105a200e94efb60e8ac01072abc5486bc1c263556eb2d4c124c4c89f1247def113fc5aee6cc6fec6e2766bffd56359cbdafbbfba41bf6c99b42cf785fd87972691ff824989b3b1395a33d9031fba5651be1efe3c4f4172639f8526bc8d9e6bee7cc9449f04681e0041da152815968ba06c635d4da33b5a02ac5f19953f8a8e1cafc21f8e61993a75ad726d6840bd61179cbbea50b38d6598d60a4d2e9aaf890c53b7eeaf21da928f438d56225c7"
        }
        
        try:
            # Get proxy info
            proxy_info = self.proxy_handler.get_current_proxy_info()
            if not proxy_info or not proxy_info['is_running']:
                logger.error("No proxy available")
                return None
            
            proxies = {
                'http': proxy_info['http_proxy'],
                'https': proxy_info['http_proxy']
            }
            
            response = requests.get(url, headers=headers, params=params, proxies=proxies, timeout=15)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                logger.warning("403 Forbidden - Token may be expired, refreshing...")
                self.get_guest_token()
                return None
            else:
                logger.error(f"Request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching tweets: {e}")
            return None


class InstagramProxyIntegration:
    """Integration class for Instagram API with Xray proxy support."""
    
    def __init__(self, proxy_handler: ProxyHandler):
        """
        Initialize Instagram integration with proxy handler.
        
        Args:
            proxy_handler: ProxyHandler instance
        """
        self.proxy_handler = proxy_handler
        self.base_url = "https://www.instagram.com"
        self.csrf_token = None
        self.token_created_time = None
    
    def get_csrf_token(self) -> Optional[str]:
        """
        Get a fresh CSRF token from Instagram's main page.
        
        Returns:
            str: CSRF token or None if failed
        """
        url = f"{self.base_url}/"
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-GB,en;q=0.9,fa-IR;q=0.8,fa;q=0.7,en-US;q=0.6",
            "accept-encoding": "gzip, deflate, br",
            "sec-ch-ua": "\"Google Chrome\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1"
        }
        
        try:
            # Get proxy info
            proxy_info = self.proxy_handler.get_current_proxy_info()
            if not proxy_info or not proxy_info['is_running']:
                logger.error("No proxy available")
                return None
            
            proxies = {
                'http': proxy_info['http_proxy'],
                'https': proxy_info['http_proxy']
            }
            
            response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
            if response.status_code == 200:
                # Extract CSRF token from cookies
                cookies = response.cookies
                csrf_token = cookies.get('csrftoken')
                if csrf_token:
                    self.csrf_token = csrf_token
                    self.token_created_time = time.time()
                    logger.info(f"Got CSRF token: {csrf_token}")
                    return csrf_token
                else:
                    logger.error("Failed to extract CSRF token from response")
                    return None
            else:
                logger.error(f"Failed to get CSRF token: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting CSRF token: {e}")
            return None
    
    def get_profile(self, username: str) -> Optional[Dict]:
        """
        Fetch Instagram profile information for a specific username.
        
        Args:
            username: Instagram username
            
        Returns:
            Dict: JSON response containing profile information
        """
        # Get or refresh CSRF token
        if not self.csrf_token or (time.time() - self.token_created_time) > 3600:
            self.get_csrf_token()
        
        if not self.csrf_token:
            logger.error("No CSRF token available")
            return None
        
        url = f"{self.base_url}/api/v1/users/web_profile_info/"
        params = {"username": username}
        
        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-GB,en;q=0.9,fa-IR;q=0.8,fa;q=0.7,en-US;q=0.6",
            "cookie": f"ig_did=1FAB74AB-66C5-433F-B843-C67071E157F5; csrftoken={self.csrf_token}; datr=77n0aEMGsoEwuclc0uSNVR7V; mid=aPS57wALAAHS28ICa2T1EgDFFXXg; wd=1920x953; ps_l=1; ps_n=1",
            "origin": "https://www.instagram.com",
            "priority": "u=1, i",
            "referer": f"https://www.instagram.com/{username}/",
            "sec-ch-ua": "\"Google Chrome\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            "x-asbd-id": "359341",
            "x-csrftoken": self.csrf_token,
            "x-ig-app-id": "936619743392459",
            "x-ig-www-claim": "0",
            "x-requested-with": "XMLHttpRequest",
            "x-web-session-id": "h038o5:oemjy9:puqj70"
        }
        
        try:
            # Get proxy info
            proxy_info = self.proxy_handler.get_current_proxy_info()
            if not proxy_info or not proxy_info['is_running']:
                logger.error("No proxy available")
                return None
            
            proxies = {
                'http': proxy_info['http_proxy'],
                'https': proxy_info['http_proxy']
            }
            
            response = requests.get(url, headers=headers, params=params, proxies=proxies, timeout=15)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching profile: {e}")
            return None


class GenericAPIIntegration:
    """Generic API integration class with Xray proxy support."""
    
    def __init__(self, proxy_handler: ProxyHandler, base_url: str):
        """
        Initialize generic API integration with proxy handler.
        
        Args:
            proxy_handler: ProxyHandler instance
            base_url: Base URL for the API
        """
        self.proxy_handler = proxy_handler
        self.base_url = base_url.rstrip('/')
    
    def make_request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        timeout: int = 30
    ) -> Optional[requests.Response]:
        """
        Make a generic API request through proxy.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            headers: Request headers
            params: Query parameters
            data: Form data
            json_data: JSON data
            timeout: Request timeout
            
        Returns:
            requests.Response: Response object or None if failed
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Get proxy info
        proxy_info = self.proxy_handler.get_current_proxy_info()
        if not proxy_info or not proxy_info['is_running']:
            logger.error("No proxy available")
            return None
        
        proxies = {
            'http': proxy_info['http_proxy'],
            'https': proxy_info['http_proxy']
        }
        
        kwargs = {
            'headers': headers or {},
            'params': params,
            'proxies': proxies,
            'timeout': timeout
        }
        
        if data:
            kwargs['data'] = data
        elif json_data:
            kwargs['json'] = json_data
        
        try:
            if method.upper() == 'GET':
                return requests.get(url, **kwargs)
            elif method.upper() == 'POST':
                return requests.post(url, **kwargs)
            else:
                return requests.request(method, url, **kwargs)
        except Exception as e:
            logger.error(f"Error making {method} request to {url}: {e}")
            return None


def example_twitter_integration():
    """Example of Twitter integration with Xray proxy."""
    
    print("=== Twitter Integration Example ===")
    
    xray_configs = get_xray_configs()
    if not xray_configs:
        print("No Xray configurations available")
        return
    
    with ProxyHandler(xray_configs) as proxy_handler:
        # Start proxy
        if not proxy_handler.start_proxy():
            print("❌ Failed to start proxy")
            return
        
        twitter_integration = TwitterProxyIntegration(proxy_handler)
        
        # Test guest token
        print("Getting guest token...")
        token = twitter_integration.get_guest_token()
        if token:
            print(f"✅ Guest token obtained: {token}")
        else:
            print("❌ Failed to get guest token")
            return
        
        # Test fetching tweets
        print("\nFetching tweets for user ID: 19701628")
        tweets = twitter_integration.get_user_tweets("19701628", 5)
        
        if tweets:
            print("✅ Tweets fetched successfully!")
            print(f"Response keys: {list(tweets.keys())}")
        else:
            print("❌ Failed to fetch tweets")


def example_instagram_integration():
    """Example of Instagram integration with Xray proxy."""
    
    print("\n=== Instagram Integration Example ===")
    
    xray_configs = get_xray_configs()
    if not xray_configs:
        print("No Xray configurations available")
        return
    
    with ProxyHandler(xray_configs) as proxy_handler:
        # Start proxy
        if not proxy_handler.start_proxy():
            print("❌ Failed to start proxy")
            return
        
        instagram_integration = InstagramProxyIntegration(proxy_handler)
        
        # Test CSRF token
        print("Getting CSRF token...")
        token = instagram_integration.get_csrf_token()
        if token:
            print(f"✅ CSRF token obtained: {token}")
        else:
            print("❌ Failed to get CSRF token")
            return
        
        # Test fetching profile
        print("\nFetching profile for username: cristiano")
        profile = instagram_integration.get_profile("cristiano")
        
        if profile:
            print("✅ Profile fetched successfully!")
            print(f"Response keys: {list(profile.keys())}")
        else:
            print("❌ Failed to fetch profile")


def example_generic_api_integration():
    """Example of generic API integration with Xray proxy."""
    
    print("\n=== Generic API Integration Example ===")
    
    xray_configs = get_xray_configs()
    if not xray_configs:
        print("No Xray configurations available")
        return
    
    with ProxyHandler(xray_configs) as proxy_handler:
        # Start proxy
        if not proxy_handler.start_proxy():
            print("❌ Failed to start proxy")
            return
        
        # Test with httpbin.org
        api_integration = GenericAPIIntegration(proxy_handler, "https://httpbin.org")
        
        # Test GET request
        print("Testing GET request...")
        response = api_integration.make_request("GET", "/ip")
        if response and response.status_code == 200:
            print("✅ GET request successful!")
            print(f"Response: {response.json()}")
        else:
            print("❌ GET request failed")
        
        # Test POST request
        print("\nTesting POST request...")
        test_data = {"test": "data", "timestamp": time.time()}
        response = api_integration.make_request("POST", "/post", json_data=test_data)
        if response and response.status_code == 200:
            print("✅ POST request successful!")
            print(f"Response: {response.json()}")
        else:
            print("❌ POST request failed")


def example_batch_requests():
    """Example of making batch requests with Xray proxy rotation."""
    
    print("\n=== Batch Requests Example ===")
    
    xray_configs = get_xray_configs()
    if not xray_configs:
        print("No Xray configurations available")
        return
    
    with ProxyHandler(
        xray_configs,
        rotation_enabled=True,
        rotation_interval=10  # Rotate every 10 seconds
    ) as proxy_handler:
        
        # Start initial proxy
        if not proxy_handler.start_proxy():
            print("❌ Failed to start initial proxy")
            return
        
        # Make multiple requests to see rotation in action
        urls = [
            "https://httpbin.org/ip",
            "https://httpbin.org/user-agent",
            "https://httpbin.org/headers",
            "https://httpbin.org/get",
            "https://httpbin.org/json"
        ]
        
        print("Making batch requests with proxy rotation...")
        for i, url in enumerate(urls):
            print(f"\nRequest {i+1}: {url}")
            
            # Get current proxy info
            proxy_info = proxy_handler.get_current_proxy_info()
            if proxy_info and proxy_info['is_running']:
                proxies = {
                    'http': proxy_info['http_proxy'],
                    'https': proxy_info['http_proxy']
                }
                
                try:
                    response = requests.get(url, proxies=proxies, timeout=10)
                    
                    if response.status_code == 200:
                        print("✅ Success")
                        data = response.json()
                        if 'origin' in data:
                            print(f"IP: {data['origin']}")
                        elif 'user-agent' in data:
                            print(f"User-Agent: {data['user-agent']}")
                    else:
                        print(f"❌ Failed: {response.status_code}")
                except Exception as e:
                    print(f"❌ Error: {e}")
            else:
                print("❌ No proxy available")
            
            time.sleep(2)  # Wait between requests
        
        # Show final statistics
        print("\n=== Final Proxy Statistics ===")
        stats = proxy_handler.get_proxy_stats()
        print(f"Total proxies: {stats['total_proxies']}")
        print(f"Healthy proxies: {stats['healthy_proxies']}")
        print(f"Failed proxies: {stats['failed_proxies']}")
        print(f"Current proxy: {stats['current_proxy']}")


if __name__ == "__main__":
    print("Xray Proxy Integration Examples")
    print("=" * 50)
    
    # Run integration examples
    example_twitter_integration()
    example_instagram_integration()
    example_generic_api_integration()
    example_batch_requests()
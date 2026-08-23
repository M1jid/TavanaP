#!/usr/bin/env python3
"""
Twitter Scraper using Playwright
A modern, reliable approach to scraping Twitter/X data
"""

import os
import sys
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
import re


class PlaywrightTwitterScraper:
    def __init__(self):
        """Initialize the Playwright Twitter scraper"""
        self.load_environment()
        self.browser = None
        self.page = None
        
    def load_environment(self):
        """Load configuration from .env file"""
        env_path = Path(__file__).parent.parent / ".env"
        
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✓ Loaded environment from {env_path}")
        else:
            print(f"⚠️  No .env file found at {env_path}")
            print("Using default configuration...")
            
        # Load configuration
        self.username = os.getenv('TWITTER_USERNAME', 'elonmusk')
        self.limit = int(os.getenv('TWITTER_LIMIT', '5'))
        self.since = os.getenv('TWITTER_SINCE', '2024-01-01')
        self.until = os.getenv('TWITTER_UNTIL', '')
        self.output_format = os.getenv('TWITTER_OUTPUT_FORMAT', 'json')
        
        # Proxy configuration
        self.proxy_host = os.getenv('PROXY_HOST', '')
        self.proxy_port = int(os.getenv('PROXY_PORT', '0'))
        self.proxy_type = os.getenv('PROXY_TYPE', 'http')
        self.proxy_username = os.getenv('PROXY_USERNAME', '')
        self.proxy_password = os.getenv('PROXY_PASSWORD', '')
                
        # Login credentials (optional)
        self.twitter_username = os.getenv('TWITTER_LOGIN_USERNAME', '')
        self.twitter_password = os.getenv('TWITTER_LOGIN_PASSWORD', '')
        
        # Twitter login token (from browser local storage)
        self.twitter_login_token = os.getenv('TWITTER_LOGIN_TOKEN', '')
        
        print(f"Configuration loaded:")
        print(f"  - Username: {self.username}")
        print(f"  - Limit: {self.limit}")
        print(f"  - Since: {self.since}")
        print(f"  - Until: {self.until}")
        print(f"  - Output Format: {self.output_format}")
        
        if self.proxy_host:
            print(f"  - Proxy: {self.proxy_type}://{self.proxy_host}:{self.proxy_port}")
        else:
            print(f"  - Proxy: None (direct connection)")
            
        if self.twitter_login_token:
            print(f"  - Login: Using token (authenticated)")
        elif self.twitter_username:
            print(f"  - Login: {self.twitter_username}")
        else:
            print(f"  - Login: Anonymous browsing")

    def setup_browser_options(self):
        """Setup browser options with proxy and other settings"""
        options = {
            'headless': False,  # Set to True for headless mode
        }
        
        # Add proxy configuration if provided
        if self.proxy_host and self.proxy_port:
            proxy_config = {
                'server': f"{self.proxy_type}://{self.proxy_host}:{self.proxy_port}"
            }
            
            if self.proxy_username and self.proxy_password:
                proxy_config['username'] = self.proxy_username
                proxy_config['password'] = self.proxy_password
                
            options['proxy'] = proxy_config
            print(f"Using proxy: {self.proxy_type}://{self.proxy_host}:{self.proxy_port}")
        else:
            print("Using direct connection (no proxy)")
            
        return options

    def setup_page_options(self):
        """Setup page options with viewport and user agent"""
        return {
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    async def authenticate_with_token(self, page):
        """Authenticate using the authentication token as a cookie"""
        if not self.twitter_login_token:
            print("No authentication token provided")
            return True
            
        try:
            print(f"Authenticating with token cookie...")
            
            # Set the authentication token as a cookie before navigating
            await page.context.add_cookies([
                {
                    'name': 'auth_token',
                    'value': self.twitter_login_token,
                    'domain': '.twitter.com',
                    'path': '/',
                    'httpOnly': True,
                    'secure': True,
                    'sameSite': 'None'
                },
                {
                    'name': 'auth_token',
                    'value': self.twitter_login_token,
                    'domain': '.x.com',
                    'path': '/',
                    'httpOnly': True,
                    'secure': True,
                    'sameSite': 'None'
                }
            ])
            
            print("Authentication token set as cookie")
            
            # Navigate to Twitter with the cookie already set
            await page.goto('https://twitter.com', wait_until='domcontentloaded')
            await page.wait_for_timeout(3000)
            
            # Check if we're authenticated by looking for user-specific elements
            try:
                # Look for elements that indicate we're logged in
                user_elements = await page.query_selector_all('[data-testid="SideNav_AccountSwitcher_Button"]')
                if user_elements:
                    print("✅ Authentication successful! User is logged in")
                    return True
                else:
                    # Try alternative authentication check
                    home_elements = await page.query_selector_all('[data-testid="primaryColumn"]')
                    if home_elements:
                        print("✅ Authentication successful! Home timeline accessible")
                        return True
                    else:
                        print("⚠️  Token may be invalid or expired")
                        return False
            except:
                print("⚠️  Could not verify authentication status")
                return True  # Continue anyway
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    async def login_to_twitter(self, page):
        """Login to Twitter if credentials are provided"""
        # Try token authentication first
        if self.twitter_login_token:
            return await self.authenticate_with_token(page)
        
        # Fallback to username/password if no token
        if not self.twitter_username or not self.twitter_password:
            print("🔓 Browsing anonymously (no login credentials provided)")
            return True
            
        try:
            print(f"🔐 Logging in as {self.twitter_username}...")
            
            # Navigate to Twitter login page
            await page.goto('https://twitter.com/login', wait_until='networkidle')
            await page.wait_for_timeout(2000)
            
            # Fill username
            username_input = page.locator('input[name="text"]')
            await username_input.fill(self.twitter_username)
            await page.click('text=Next')
            await page.wait_for_timeout(2000)
            
            # Fill password
            password_input = page.locator('input[name="password"]')
            await password_input.fill(self.twitter_password)
            await page.click('text=Log in')
            await page.wait_for_timeout(5000)
            
            # Check if login was successful
            if 'home' in page.url or 'twitter.com' in page.url:
                print("✅ Login successful!")
                return True
            else:
                print("❌ Login failed")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    async def navigate_to_profile(self, page):
        """Navigate to the target user's profile"""
        try:
            profile_url = f"https://twitter.com/{self.username}"
            print(f"🌐 Navigating to {profile_url}")
            
            # Try with different wait strategies
            try:
                await page.goto(profile_url, wait_until='networkidle', timeout=30000)
            except Exception as e:
                print(f"⚠️  Network idle failed, trying domcontentloaded: {e}")
                await page.goto(profile_url, wait_until='domcontentloaded', timeout=30000)
            
            await page.wait_for_timeout(3000)
            
            # Check if profile exists or if there are errors
            page_content = await page.content()
            if "This account doesn't exist" in page_content or "User not found" in page_content:
                print(f"❌ Profile @{self.username} doesn't exist")
                return False
            elif "Something went wrong" in page_content or "Try again" in page_content:
                print(f"⚠️  Twitter is showing an error page for @{self.username}")
                print("💡 This might be due to:")
                print("   - Twitter's anti-bot measures")
                print("   - Rate limiting")
                print("   - Need for authentication")
                print("🔄 Trying to continue anyway...")
                return True  # Continue to try scraping
                
            print(f"✅ Successfully loaded profile @{self.username}")
            return True
            
        except Exception as e:
            print(f"❌ Error navigating to profile: {e}")
            return False

    async def scroll_and_collect_tweets(self, page):
        """Scroll through the profile and collect tweets from API responses"""
        print(f"Scrolling and collecting tweets from API responses...")
        
        tweets_collected = 0
        scroll_attempts = 0
        max_scroll_attempts = 5
        
        # Set up response interception using Playwright's response events
        print("Setting up response interception...")
        
        # Use response events instead of route interception
        page.on("response", self.handle_response)
        
        print("Response interception set up successfully")
        
        while tweets_collected < self.limit and scroll_attempts < max_scroll_attempts:
            try:
                # Scroll down to trigger more API requests
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.wait_for_timeout(3000)
                
                scroll_attempts += 1
                print(f"Scroll attempt {scroll_attempts}/{max_scroll_attempts}")
                
                # Wait a bit more for API requests to complete
                await page.wait_for_timeout(2000)
                
            except Exception as e:
                print(f"Error during scrolling: {e}")
                break
        
        print(f"Scrolling completed after {scroll_attempts} attempts")
        
    async def handle_response(self, response):
        """Handle HTTP responses and extract tweet data"""
        try:
            url = response.url
            print(f"Response received: {url}")
            
            # Check if this is a relevant Twitter API response
            if any(pattern in url for pattern in ['/2/timeline/', '/2/user/', '/2/tweets/', '/2/users/', '/graphql/', '/i/api/graphql/']):
                print(f"Processing Twitter API response: {url}")
                
                # Special handling for UserTweets GraphQL endpoint
                if 'UserTweets' in url:
                    print(f"Found UserTweets GraphQL response: {url}")
                
                # Check response status and content type
                if response.status != 200:
                    print(f"Response status is not 200: {response.status}")
                    return
                
                # Check content type
                content_type = response.headers.get('content-type', '')
                if 'application/json' not in content_type:
                    print(f"Response is not JSON, content-type: {content_type}")
                    return
                
                try:
                    # Get the response text first to check if it's valid
                    response_text = await response.text()
                    if not response_text.strip():
                        print("Response is empty")
                        return
                    
                    # Try to parse as JSON
                    response_data = await response.json()
                    
                    # Debug: Print API response structure
                    print(f"Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
                    
                    # For UserTweets GraphQL requests, extract from the specific structure
                    if 'UserTweets' in url:
                        self.extract_tweets_from_user_tweets_graphql(response_data)
                    else:
                        self.extract_tweets_from_api_response(response_data)
                        
                except Exception as json_error:
                    print(f"Error parsing JSON response: {json_error}")
                    print(f"Response status: {response.status}")
                    print(f"Response content-type: {response.headers.get('content-type', 'unknown')}")
                    print(f"Response text preview: {response_text[:200] if 'response_text' in locals() else 'N/A'}")
                    # Don't raise the error, just log it and continue
                    
        except Exception as e:
            print(f"Error handling response: {e}")
            # Don't raise the error, just log it and continue

    async def log_all_requests(self, route):
        """Log all requests to help debug what's being intercepted"""
        try:
            url = route.request.url
            method = route.request.method
            
            # Only log relevant requests
            if any(pattern in url for pattern in ['/2/', '/api/', '/graphql/', '/1.1/', '/i/api/']):
                print(f"Request: {method} {url}")
                
                # If it's a Twitter API request, handle it
                if any(pattern in url for pattern in ['/2/timeline/', '/2/user/', '/2/tweets/', '/2/users/', '/graphql/', '/i/api/graphql/']):
                    await self.handle_twitter_api_response(route)
                else:
                    await route.continue_()
            else:
                await route.continue_()
                
        except Exception as e:
            print(f"Error in log_all_requests: {e}")
            await route.continue_()

    async def handle_twitter_api_response(self, route):
        """Handle Twitter API responses and extract tweet data"""
        try:
            url = route.request.url
            print(f"Intercepted request: {url}")
            
            # Check if this is a relevant Twitter API request
            if any(pattern in url for pattern in ['/2/timeline/', '/2/user/', '/2/tweets/', '/2/users/', '/graphql/', '/i/api/graphql/']):
                print(f"Processing Twitter API request: {url}")
                
                # Special handling for UserTweets GraphQL endpoint
                if 'UserTweets' in url:
                    print(f"Found UserTweets GraphQL request: {url}")
                
                # Continue the request and let it complete naturally
                await route.continue_()
                
                # Wait a bit for the response to complete
                await asyncio.sleep(1)
                
                # Try to get the response from the page's network events
                try:
                    # This is a workaround - we'll use a different approach
                    print("Request completed, checking for response data...")
                except Exception as response_error:
                    print(f"Error getting response: {response_error}")
                    
            else:
                print(f"Skipping non-Twitter API request: {url}")
                await route.continue_()
            
        except Exception as e:
            print(f"Error handling API response: {e}")
            # Continue the request even if there's an error
            try:
                await route.continue_()
            except:
                pass

    def extract_tweets_from_api_response(self, response_data):
        """Extract tweet data from Twitter API response"""
        tweets = []
        try:
            # Handle different Twitter API response structures
            if 'data' in response_data:
                data = response_data['data']
                
                # Check for user timeline
                if 'user' in data and 'result' in data['user']:
                    user_result = data['user']['result']
                    
                    # Handle timeline_v2 structure
                    if 'timeline_v2' in user_result:
                        tweets.extend(self.extract_from_timeline_v2(user_result['timeline_v2']))
                    
                    # Handle legacy timeline structure
                    elif 'timeline' in user_result:
                        tweets.extend(self.extract_from_legacy_timeline(user_result['timeline']))
                
                # Handle direct timeline responses
                elif 'timeline' in data:
                    tweets.extend(self.extract_from_legacy_timeline(data['timeline']))
                
                # Handle instructions directly
                elif 'instructions' in data:
                    tweets.extend(self.extract_from_instructions(data['instructions']))
                    
        except Exception as e:
            print(f"Error parsing API response: {e}")
            
        return tweets

    def extract_tweets_from_user_tweets_graphql(self, response_data):
        """Extract tweets from UserTweets GraphQL response"""
        tweets = []
        
        try:
            # Navigate through the GraphQL response structure
            if 'data' in response_data:
                data = response_data['data']
                
                # Check for user timeline
                if 'user' in data and 'result' in data['user']:
                    user_result = data['user']['result']
                    # Get timeline tweets
                    if 'timeline' in user_result:
                        timeline = user_result['timeline']
                        if 'timeline' in timeline:
                            timeline = timeline['timeline']
                            if 'instructions' in timeline:
                                instructions = timeline['instructions']
                                for instruction in instructions:
                                    if instruction.get('type') == 'TimelineAddEntries':
                                        entries = instruction.get('entries', [])
                                        
                                        for entry in entries:
                                            if entry.get('content', {}).get('entryType') == 'TimelineTimelineItem':
                                                item = entry['content']['itemContent']
                                                
                                                if 'tweet_results' in item:
                                                    tweet_result = item['tweet_results']['result']
                                                    if tweet_result.get('__typename') == 'Tweet':
                                                        tweet_data = self.parse_tweet_from_api(tweet_result)
                                                        print(json.dumps(tweet_data, indent=4, ensure_ascii=False))
                                                        if tweet_data:
                                                            tweets.append(tweet_data)
                                                    
        except Exception as e:
            print(f"Error parsing UserTweets GraphQL response: {e}")
            raise e
            
        return tweets

    def extract_from_timeline_v2(self, timeline_v2):
        """Extract tweets from timeline_v2 structure"""
        tweets = []
        
        try:
            if 'timeline' in timeline_v2 and 'instructions' in timeline_v2['timeline']:
                instructions = timeline_v2['timeline']['instructions']
                tweets.extend(self.extract_from_instructions(instructions))
        except Exception as e:
            print(f"Error extracting from timeline_v2: {e}")
            
        return tweets

    def extract_from_legacy_timeline(self, timeline):
        """Extract tweets from legacy timeline structure"""
        tweets = []
        
        try:
            if 'instructions' in timeline:
                instructions = timeline['instructions']
                tweets.extend(self.extract_from_instructions(instructions))
        except Exception as e:
            print(f"Error extracting from legacy timeline: {e}")
            
        return tweets

    def extract_from_instructions(self, instructions):
        """Extract tweets from instructions array"""
        tweets = []
        
        try:
            for instruction in instructions:
                if instruction.get('type') == 'TimelineAddEntries':
                    entries = instruction.get('entries', [])
                    
                    for entry in entries:
                        if entry.get('content', {}).get('entryType') == 'TimelineTimelineItem':
                            item = entry['content']['itemContent']
                            
                            if 'tweet_results' in item:
                                tweet_result = item['tweet_results']['result']
                                print(json.dumps(tweet_result, indent=4, ensure_ascii=False))
                                if tweet_result.get('__typename') == 'Tweet':
                                    tweet_data = self.parse_tweet_from_api(tweet_result)
                                    if tweet_data:
                                        tweets.append(tweet_data)
        except Exception as e:
            print(f"Error extracting from instructions: {e}")
            
        return tweets

    def parse_tweet_from_api(self, tweet_result):
        """Parse individual tweet from API response"""
        try:
            # Extract user info from core.user_results
            user_screen_name = self.username  # Default to target username
            user_name = ''
            user_id = ''
            
            if 'core' in tweet_result and 'user_results' in tweet_result['core']:
                user_result = tweet_result['core']['user_results']['result']
                if 'legacy' in user_result:
                    user_legacy = user_result['legacy']
                    user_screen_name = user_legacy.get('screen_name', self.username)
                    user_name = user_legacy.get('name', '')
                if 'id' in user_result:
                    user_id = user_result['id']
            
            # Get tweet ID
            tweet_id = tweet_result.get('rest_id', tweet_result.get('id_str', ''))
            
            # Construct tweet URL
            tweet_url = f"https://x.com/{user_screen_name}/status/{tweet_id}"
            
            tweet_data = {
                'id': tweet_id,
                'url': tweet_url,
                'date': '',
                'time': '',
                'username': user_screen_name,
                'name': user_name,
                'user_id': user_id,
                'tweet': '',
                'likes_count': 0,
                'retweets_count': 0,
                'replies_count': 0,
                'quote_count': 0,
                'bookmark_count': 0,
                'views_count': 0,
                'hashtags': [],
                'mentions': [],
                'urls': [],
                'images': [],
                'videos': [],
                'is_quote_status': False,
                'is_retweet': False,
                'language': '',
                'conversation_id': '',
                'reply_to_user': '',
                'reply_to_tweet': ''
            }
            
            # Extract tweet text and engagement data
            if 'legacy' in tweet_result:
                legacy = tweet_result['legacy']
                tweet_data['tweet'] = legacy.get('full_text', '')
                tweet_data['likes_count'] = legacy.get('favorite_count', 0)
                tweet_data['retweets_count'] = legacy.get('retweet_count', 0)
                tweet_data['replies_count'] = legacy.get('reply_count', 0)
                tweet_data['quote_count'] = legacy.get('quote_count', 0)
                tweet_data['bookmark_count'] = legacy.get('bookmark_count', 0)
                tweet_data['is_quote_status'] = legacy.get('is_quote_status', False)
                tweet_data['language'] = legacy.get('lang', '')
                tweet_data['conversation_id'] = legacy.get('conversation_id_str', '')
                
                # Extract date
                created_at = legacy.get('created_at', '')
                if created_at:
                    from datetime import datetime
                    try:
                        dt = datetime.strptime(created_at, '%a %b %d %H:%M:%S %z %Y')
                        tweet_data['date'] = dt.strftime('%Y-%m-%d')
                        tweet_data['time'] = dt.strftime('%H:%M:%S')
                    except:
                        pass
                
                # Extract hashtags, mentions, and URLs
                if 'entities' in legacy:
                    entities = legacy['entities']
                    
                    if 'hashtags' in entities:
                        tweet_data['hashtags'] = [f"#{tag['text']}" for tag in entities['hashtags']]
                    
                    if 'user_mentions' in entities:
                        tweet_data['mentions'] = [f"@{mention['screen_name']}" for mention in entities['user_mentions']]
                    
                    if 'urls' in entities:
                        tweet_data['urls'] = [url['expanded_url'] for url in entities['urls']]
                
                # Extract media
                if 'extended_entities' in legacy and 'media' in legacy['extended_entities']:
                    media = legacy['extended_entities']['media']
                    for item in media:
                        if item.get('type') == 'photo':
                            tweet_data['images'].append(item.get('media_url_https', ''))
                        elif item.get('type') == 'video':
                            tweet_data['videos'].append(item.get('media_url_https', ''))
            
            # Extract views count
            if 'views' in tweet_result and 'count' in tweet_result['views']:
                tweet_data['views_count'] = int(tweet_result['views']['count'])
            
            # Extract edit information
            if 'edit_control' in tweet_result:
                edit_control = tweet_result['edit_control']
                tweet_data['is_edited'] = 'edit_tweet_ids' in edit_control
                tweet_data['editable_until'] = edit_control.get('editable_until_msecs', '')
                tweet_data['edits_remaining'] = edit_control.get('edits_remaining', '0')
            
            # Extract reply information
            if 'legacy' in tweet_result and 'in_reply_to_status_id_str' in tweet_result['legacy']:
                reply_to_id = tweet_result['legacy']['in_reply_to_status_id_str']
                if reply_to_id:
                    tweet_data['reply_to_tweet'] = reply_to_id
                    # Try to get reply user info
                    if 'in_reply_to_screen_name' in tweet_result['legacy']:
                        tweet_data['reply_to_user'] = tweet_result['legacy']['in_reply_to_screen_name']
            
            # Handle retweets - extract data from the original tweet
            if 'legacy' in tweet_result and 'retweeted_status_result' in tweet_result['legacy']:
                retweeted_status = tweet_result['legacy']['retweeted_status_result']['result']
                tweet_data['is_retweet'] = True
                
                # Extract original tweet data from retweeted_status_result
                if 'core' in retweeted_status:
                    original_core = retweeted_status['core']
                    
                    # Extract original user info
                    if 'user_results' in original_core:
                        original_user = original_core['user_results']['result']
                        if 'legacy' in original_user:
                            original_user_legacy = original_user['legacy']
                            tweet_data['original_username'] = original_user_legacy.get('screen_name', '')
                            tweet_data['original_name'] = original_user_legacy.get('name', '')
                        if 'id' in original_user:
                            tweet_data['original_user_id'] = original_user['id']
                    
                    # Extract original tweet content and engagement
                    if 'legacy' in retweeted_status:
                        original_legacy = retweeted_status['legacy']
                        tweet_data['original_tweet'] = original_legacy.get('full_text', '')
                        tweet_data['original_likes_count'] = original_legacy.get('favorite_count', 0)
                        tweet_data['original_retweets_count'] = original_legacy.get('retweet_count', 0)
                        tweet_data['original_replies_count'] = original_legacy.get('reply_count', 0)
                        tweet_data['original_quote_count'] = original_legacy.get('quote_count', 0)
                        tweet_data['original_bookmark_count'] = original_legacy.get('bookmark_count', 0)
                        tweet_data['original_language'] = original_legacy.get('lang', '')
                        
                        # Extract original tweet date
                        original_created_at = original_legacy.get('created_at', '')
                        if original_created_at:
                            from datetime import datetime
                            try:
                                dt = datetime.strptime(original_created_at, '%a %b %d %H:%M:%S %z %Y')
                                tweet_data['original_date'] = dt.strftime('%Y-%m-%d')
                                tweet_data['original_time'] = dt.strftime('%H:%M:%S')
                            except:
                                pass
                        
                        # Extract original hashtags, mentions, and URLs
                        if 'entities' in original_legacy:
                            original_entities = original_legacy['entities']
                            
                            if 'hashtags' in original_entities:
                                tweet_data['original_hashtags'] = [f"#{tag['text']}" for tag in original_entities['hashtags']]
                            
                            if 'user_mentions' in original_entities:
                                tweet_data['original_mentions'] = [f"@{mention['screen_name']}" for mention in original_entities['user_mentions']]
                            
                            if 'urls' in original_entities:
                                tweet_data['original_urls'] = [url['expanded_url'] for url in original_entities['urls']]
                        
                        # Extract original media
                        if 'extended_entities' in original_legacy and 'media' in original_legacy['extended_entities']:
                            original_media = original_legacy['extended_entities']['media']
                            tweet_data['original_images'] = []
                            tweet_data['original_videos'] = []
                            for item in original_media:
                                if item.get('type') == 'photo':
                                    tweet_data['original_images'].append(item.get('media_url_https', ''))
                                elif item.get('type') == 'video':
                                    tweet_data['original_videos'].append(item.get('media_url_https', ''))
                    
                    # Extract original tweet views count
                    if 'views' in retweeted_status and 'count' in retweeted_status['views']:
                        tweet_data['original_views_count'] = int(retweeted_status['views']['count'])
                    
                    # Extract original tweet ID and URL
                    original_tweet_id = retweeted_status.get('rest_id', retweeted_status.get('id_str', ''))
                    if original_tweet_id and tweet_data.get('original_username'):
                        tweet_data['original_tweet_url'] = f"https://x.com/{tweet_data['original_username']}/status/{original_tweet_id}"
                        tweet_data['original_tweet_id'] = original_tweet_id
            
            return tweet_data
            
        except Exception as e:
            print(f"Error parsing tweet: {e}")
            return None
                
    async def extract_tweets_from_page(self, page):
        """Extract tweet data from the current page"""
        try:
            # Wait for tweets to load
            await page.wait_for_selector('[data-testid="tweet"]', timeout=10000)
            
            # Extract tweet elements
            tweet_elements = await page.query_selector_all('[data-testid="tweet"]')
            
            tweets = []
            for element in tweet_elements:
                try:
                    tweet_data = await self.extract_tweet_data_from_element(element)
                    if tweet_data:
                        tweets.append(tweet_data)
                except Exception as e:
                    continue
                    
            return tweets
            
        except Exception as e:
            print(f"⚠️  Error extracting tweets: {e}")
            return []

    async def extract_tweet_data_from_element(self, element):
        """Extract data from a single tweet element"""
        try:
            # Extract basic tweet information
            tweet_data = {
                'id': '',
                'date': '',
                'time': '',
                'username': self.username,
                'name': '',
                'tweet': '',
                'likes_count': 0,
                'retweets_count': 0,
                'replies_count': 0,
                'hashtags': [],
                'mentions': [],
                'urls': [],
                'images': [],
                'videos': []
            }
            
            # Extract tweet text
            text_element = await element.query_selector('[data-testid="tweetText"]')
            if text_element:
                tweet_data['tweet'] = await text_element.inner_text()
            
            # Extract user name
            name_element = await element.query_selector('[data-testid="User-Name"]')
            if name_element:
                name_text = await name_element.inner_text()
                tweet_data['name'] = name_text.split('\n')[0] if '\n' in name_text else name_text
            
            # Extract date/time
            time_element = await element.query_selector('time')
            if time_element:
                datetime_attr = await time_element.get_attribute('datetime')
                if datetime_attr:
                    tweet_data['date'] = datetime_attr.split('T')[0]
                    tweet_data['time'] = datetime_attr.split('T')[1].split('.')[0]
            
            # Extract engagement metrics
            try:
                # Likes
                likes_element = await element.query_selector('[data-testid="like"]')
                if likes_element:
                    likes_text = await likes_element.inner_text()
                    tweet_data['likes_count'] = self.extract_number(likes_text)
                
                # Retweets
                retweets_element = await element.query_selector('[data-testid="retweet"]')
                if retweets_element:
                    retweets_text = await retweets_element.inner_text()
                    tweet_data['retweets_count'] = self.extract_number(retweets_text)
                
                # Replies
                replies_element = await element.query_selector('[data-testid="reply"]')
                if replies_element:
                    replies_text = await replies_element.inner_text()
                    tweet_data['replies_count'] = self.extract_number(replies_text)
                    
            except Exception as e:
                pass  # Continue if engagement metrics can't be extracted
            
            # Extract hashtags and mentions from tweet text
            if tweet_data['tweet']:
                tweet_data['hashtags'] = re.findall(r'#\w+', tweet_data['tweet'])
                tweet_data['mentions'] = re.findall(r'@\w+', tweet_data['tweet'])
                tweet_data['urls'] = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', tweet_data['tweet'])
            
            # Extract images
            images = await element.query_selector_all('img[alt*="Image"]')
            for img in images:
                src = await img.get_attribute('src')
                if src:
                    tweet_data['images'].append(src)
            
            # Extract videos
            videos = await element.query_selector_all('video')
            for video in videos:
                src = await video.get_attribute('src')
                if src:
                    tweet_data['videos'].append(src)
            
            # Generate a simple ID if not available
            if not tweet_data['id']:
                tweet_data['id'] = f"tweet_{int(time.time())}_{hash(tweet_data['tweet'][:50])}"
            
            return tweet_data
            
        except Exception as e:
            print(f"⚠️  Error extracting tweet data: {e}")
            return None

    def extract_number(self, text):
        """Extract number from text like '1.2K' or '123'"""
        if not text:
            return 0
            
        # Remove non-numeric characters except K, M, B
        clean_text = re.sub(r'[^\d.KMB]', '', text.upper())
        
        if 'K' in clean_text:
            number = float(clean_text.replace('K', '')) * 1000
        elif 'M' in clean_text:
            number = float(clean_text.replace('M', '')) * 1000000
        elif 'B' in clean_text:
            number = float(clean_text.replace('B', '')) * 1000000000
        else:
            try:
                number = float(clean_text)
            except:
                number = 0
                
        return int(number)

    def print_tweet_data(self, tweet_data, index):
        """Print formatted tweet data"""
        print(f"\nTweet #{index + 1}")
        print("-" * 50)
        print(f"URL: {tweet_data.get('url', 'N/A')}")
        print(f"ID: {tweet_data['id']}")
        print(f"Date: {tweet_data['date']} {tweet_data['time']}")
        print(f"User: @{tweet_data['username']} ({tweet_data['name']})")
        print(f"User ID: {tweet_data.get('user_id', 'N/A')}")
        print(f"Content: {tweet_data['tweet']}")
        print(f"Language: {tweet_data.get('language', 'N/A')}")
        
        print(f"\nEngagement:")
        print(f"  Likes: {tweet_data['likes_count']}")
        print(f"  Retweets: {tweet_data['retweets_count']}")
        print(f"  Replies: {tweet_data['replies_count']}")
        print(f"  Quotes: {tweet_data.get('quote_count', 0)}")
        print(f"  Bookmarks: {tweet_data.get('bookmark_count', 0)}")
        print(f"  Views: {tweet_data.get('views_count', 0)}")
        
        if tweet_data.get('is_quote_status'):
            print(f"  Quote Tweet: Yes")
        
        if tweet_data.get('is_edited'):
            print(f"  Edited: Yes (Edits remaining: {tweet_data.get('edits_remaining', 'N/A')})")
        
        if tweet_data.get('reply_to_user'):
            print(f"  Reply to: @{tweet_data['reply_to_user']} (Tweet: {tweet_data.get('reply_to_tweet', 'N/A')})")
        
        if tweet_data.get('conversation_id'):
            print(f"  Conversation ID: {tweet_data['conversation_id']}")
        
        if tweet_data['hashtags']:
            print(f"\nHashtags: {', '.join(tweet_data['hashtags'])}")
        
        if tweet_data['mentions']:
            print(f"Mentions: {', '.join(tweet_data['mentions'])}")
        
        if tweet_data['urls']:
            print(f"URLs: {', '.join(tweet_data['urls'])}")
        
        if tweet_data['images']:
            print(f"Images: {len(tweet_data['images'])} image(s)")
            for i, img in enumerate(tweet_data['images'][:3]):  # Show first 3 images
                print(f"  {i+1}: {img}")
        
        if tweet_data['videos']:
            print(f"Videos: {len(tweet_data['videos'])} video(s)")
            for i, vid in enumerate(tweet_data['videos'][:3]):  # Show first 3 videos
                print(f"  {i+1}: {vid}")

    def save_to_file(self, data, filename):
        """Save data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            print(f"\n💾 Data saved to {filename}")
        except Exception as e:
            print(f"❌ Error saving to file: {e}")

    async def scrape_tweets_async(self):
        """Main async method to scrape tweets"""
        print(f"\n🚀 Starting Playwright Twitter scraping for @{self.username}")
        print(f"📊 Target: https://x.com/{self.username}")
        print(f"📈 Limit: {self.limit} tweets")
        print(f"📅 Since: {self.since}")
        
        try:
            async with async_playwright() as p:
                # Try without proxy first (more reliable)
                browser_options_no_proxy = {
                    'headless': False,
                    'args': [
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor'
                    ]
                }
                
                try:
                    self.browser = await p.chromium.launch(**browser_options_no_proxy)
                    print("✅ Browser launched without proxy")
                except Exception as e:
                    print(f"⚠️  Direct connection failed: {e}")
                    print("🔄 Trying with proxy...")
                    
                    # Fallback: try with proxy
                    browser_options = self.setup_browser_options()
                    self.browser = await p.chromium.launch(**browser_options)
                    print("✅ Browser launched with proxy")
                
                # Create new page with page options
                page_options = self.setup_page_options()
                self.page = await self.browser.new_page(**page_options)
                
                # Add stealth measures
                await self.page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                """)
                
                # Set additional headers to look more like a real browser
                await self.page.set_extra_http_headers({
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                })
                
                # Login if credentials provided
                if not await self.login_to_twitter(self.page):
                    print("⚠️  Continuing without login...")
                
                # Navigate to profile
                if not await self.navigate_to_profile(self.page):
                    return
                
                # Scroll and collect tweets
                await self.scroll_and_collect_tweets(self.page)
                
                print(f"\n✅ Scraping completed for @{self.username}")
                print("Tweets were extracted and printed as they were received from API responses")
                
        except Exception as e:
            print(f"❌ Error during scraping: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.browser:
                await self.browser.close()

    def run(self):
        """Main entry point"""
        print("🐦 Playwright Twitter Scraper")
        print("=" * 50)
        
        try:
            asyncio.run(self.scrape_tweets_async())
        except KeyboardInterrupt:
            print("\n\n⏹️  Scraping interrupted by user")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            raise e


if __name__ == "__main__":
    # Create and run the Playwright Twitter scraper
    scraper = PlaywrightTwitterScraper()
    scraper.run()

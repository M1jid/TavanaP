import requests
import json
import time
import random
import zlib

# Global variables for token management
current_csrf_token = None
token_created_time = None
session_cookies = None

def get_csrf_token():
    """
    Get a fresh CSRF token from Instagram's main page
    """
    url = "https://www.instagram.com/"
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-GB,en;q=0.9,fa-IR;q=0.8,fa;q=0.7,en-US;q=0.6",
        "accept-encoding": "gzip, deflate, br, zstd",
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
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            # Extract CSRF token from cookies
            cookies = response.cookies
            csrf_token = cookies.get('csrftoken')
            if csrf_token:
                return csrf_token, cookies
            else:
                print("Failed to extract CSRF token from response")
                return None, None
        else:
            print(f"Failed to get CSRF token: {response.status_code}")
            return None, None
    except Exception as e:
        print(f"Error getting CSRF token: {e}")
        return None, None

def get_valid_csrf_token():
    """
    Get a valid CSRF token, either from cache or by requesting a new one
    Returns the current valid token or None if failed
    """
    global current_csrf_token, token_created_time, session_cookies
    
    # Check if we have a valid token (less than 1 hour old)
    if current_csrf_token and token_created_time:
        token_age = time.time() - token_created_time
        if token_age < 3600:  # 1 hour in seconds
            print(f"Using cached CSRF token (age: {token_age/60:.1f} minutes)")
            return current_csrf_token, session_cookies
    
    # Get a new token
    print("Getting new CSRF token...")
    new_token, cookies = get_csrf_token()
    if new_token:
        current_csrf_token = new_token
        token_created_time = time.time()
        session_cookies = cookies
        print(f"New CSRF token obtained: {new_token}")
        return new_token, cookies
    else:
        print("Failed to get new CSRF token")
        return None, None

def get_instagram_profile(username):
    """
    Fetch Instagram profile information for a specific username
    
    Args:
        username (str): Instagram username
    
    Returns:
        dict: JSON response containing profile information
    """
    url = "https://www.instagram.com/api/v1/users/web_profile_info/"
    
    # Get a valid CSRF token (cached or new)
    csrf_token, cookies = get_valid_csrf_token()
    if not csrf_token:
        print("Failed to get valid CSRF token")
        return None

    params = {
        "username": username
    }

    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",  # Remove zstd to avoid compression issues
        "accept-language": "en-GB,en;q=0.9,fa-IR;q=0.8,fa;q=0.7,en-US;q=0.6",
        "cookie": f"ig_did=1FAB74AB-66C5-433F-B843-C67071E157F5; csrftoken={csrf_token}; datr=77n0aEMGsoEwuclc0uSNVR7V; mid=aPS57wALAAHS28ICa2T1EgDFFXXg; wd=1920x953; ps_l=1; ps_n=1",
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
        "x-csrftoken": csrf_token,
        "x-ig-app-id": "936619743392459",
        "x-ig-www-claim": "0",
        "x-requested-with": "XMLHttpRequest",
        "x-web-session-id": "h038o5:oemjy9:puqj70"
    }

    response = requests.get(url, headers=headers, params=params, cookies=cookies)
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            return response.json()
        except json.JSONDecodeError:
            print("Response is not valid JSON")
            print("Content-Type:", response.headers.get("Content-Type"))
            print("Content-Encoding:", response.headers.get("Content-Encoding"))
            print("Response text (first 1000 chars):")
            print(response.text[:1000])
            return None
    elif response.status_code == 403 or response.status_code == 429:
        print(f"Response status code: {response.status_code}")
        # Invalidate current token
        global current_csrf_token, token_created_time, session_cookies
        current_csrf_token = None
        token_created_time = None
        session_cookies = None
        
        # Get a new token
        new_csrf_token, new_cookies = get_csrf_token()
        if new_csrf_token:
            # Update global variables
            current_csrf_token = new_csrf_token
            token_created_time = time.time()
            session_cookies = new_cookies
            print(f"Got new CSRF token: {new_csrf_token}")
            
            # Update headers with new token
            headers["x-csrftoken"] = new_csrf_token
            headers["cookie"] = f"ig_did=1FAB74AB-66C5-433F-B843-C67071E157F5; csrftoken={new_csrf_token}; datr=77n0aEMGsoEwuclc0uSNVR7V; mid=aPS57wALAAHS28ICa2T1EgDFFXXg; wd=1920x953; ps_l=1; ps_n=1"
            headers["accept-encoding"] = "gzip, deflate, br"  # Ensure no zstd
            
            # Retry the request with new token
            response = requests.get(url, headers=headers, params=params, cookies=new_cookies)
            print(f"Retry with new token - Status: {response.status_code}")
            
            # Check if retry was successful
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    print("Retry response is not valid JSON")
                    return None
            else:
                print(f"Retry failed with status: {response.status_code}")
                return None
        else:
            print("Failed to get new CSRF token")
            return None
    else:
        print(f"Error: Status code {response.status_code}")
        print("Response:", response.text)
        return None

def parse_instagram_profile(json_response):
    """
    Parse Instagram profile from the JSON response and extract useful information
    
    Args:
        json_response (dict): JSON response from Instagram API
    
    Returns:
        dict: Parsed profile information
    """
    try:
        data = json_response.get('data', {}).get('user', {})
        
        profile_data = {
            'id': data.get('id'),
            'username': data.get('username'),
            'full_name': data.get('full_name'),
            'biography': data.get('biography'),
            'external_url': data.get('external_url'),
            'followers_count': data.get('edge_followed_by', {}).get('count', 0),
            'following_count': data.get('edge_follow', {}).get('count', 0),
            'posts_count': data.get('edge_owner_to_timeline_media', {}).get('count', 0),
            'is_verified': data.get('is_verified', False),
            'is_private': data.get('is_private', False),
            'is_business_account': data.get('is_business_account', False),
            'profile_pic_url': data.get('profile_pic_url'),
            'profile_pic_url_hd': data.get('profile_pic_url_hd')
        }
        
        return profile_data
    except Exception as e:
        print(f"Error parsing Instagram profile: {e}")
        return {}

# Main execution
if __name__ == "__main__":
    # Example usage - you can change the usernames
    usernames = [
        "cristiano",
        "therock",
        "selenagomez",
        "kyliejenner",
        "kimkardashian",
        "leomessi",
        "neymarjr",
        "arianagrande",
        "beyonce",
        "taylorswift",
        "justinbieber",
        "drake",
        "theweeknd",
        "badgalriri",
        "nickiminaj",
        "kendalljenner",
        "khloekardashian",
        "kourtneykardash",
        "virat.kohli",
        "robertdowneyjr"
    ]
    
    while True:
        for i, username in enumerate(usernames):
            print(f"Fetching Instagram profile for: @{username} ({i+1}/{len(usernames)})")
            
            # # Add random delay between requests to avoid rate limits
            # if i > 0:  # Skip delay for first request
            #     delay = random.uniform(2, 5)  # Random delay between 2-5 seconds
            #     print(f"Waiting {delay:.1f} seconds before next request...")
            #     time.sleep(delay)
            
            response = get_instagram_profile(username)

            if response:
                print("Status: Success")
                
                # Write response to file
                filename = f"instagram_profile_{username}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(response, f, indent=2, ensure_ascii=False)
                print(f"Response saved to: {filename}")
                
                # Also save a readable text version
                text_filename = f"instagram_profile_{username}.txt"
                with open(text_filename, 'w', encoding='utf-8') as f:
                    f.write(f"Instagram Profile for: @{username}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    # Parse and write profile in readable format
                    profile = parse_instagram_profile(response)
                    if profile:
                        f.write(f"Username: @{profile.get('username', 'N/A')}\n")
                        f.write(f"Full Name: {profile.get('full_name', 'N/A')}\n")
                        f.write(f"Biography: {profile.get('biography', 'N/A')}\n")
                        f.write(f"External URL: {profile.get('external_url', 'N/A')}\n")
                        f.write(f"Followers: {profile.get('followers_count', 0):,}\n")
                        f.write(f"Following: {profile.get('following_count', 0):,}\n")
                        f.write(f"Posts: {profile.get('posts_count', 0):,}\n")
                        f.write(f"Verified: {profile.get('is_verified', False)}\n")
                        f.write(f"Private: {profile.get('is_private', False)}\n")
                        f.write(f"Business Account: {profile.get('is_business_account', False)}\n")
                        f.write(f"Profile Pic: {profile.get('profile_pic_url', 'N/A')}\n")
                    
                    # Also write the raw JSON at the end
                    f.write("\n" + "=" * 50 + "\n")
                    f.write("RAW JSON RESPONSE:\n")
                    f.write("=" * 50 + "\n")
                    f.write(json.dumps(response, indent=2, ensure_ascii=False))
                
                print(f"Readable format saved to: {text_filename}")
            else:
                print(f"Failed to fetch profile for: @{username}")
                # Still create an error file
                error_filename = f"instagram_error_{username}.txt"
                with open(error_filename, 'w', encoding='utf-8') as f:
                    f.write(f"Failed to fetch Instagram profile for: @{username}\n")
                    f.write("This could be due to:\n")
                    f.write("- Invalid username\n")
                    f.write("- Rate limiting\n")
                    f.write("- Network issues\n")
                    f.write("- API changes\n")
                print(f"Error log saved to: {error_filename}")

import requests
import json
import time
import logging

from utils.proxy_handler import ProxyHandler
from utils.proxy_config import get_xray_configs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for token management
current_guest_token = None
token_created_time = None


def get_guest_token(proxy_handler=None):
    url = "https://api.x.com/1.1/guest/activate.json"
    headers = {
        "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
        "content-type": "application/x-www-form-urlencoded",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
    }
    
    try:
        # Use proxy handler if available, otherwise use direct requests
        if proxy_handler:
            try:
                # Get proxy info and use with requests
                proxy_info = proxy_handler.get_current_proxy_info()
                logger.info(f"Proxy info: {proxy_info['http_proxy']}")
                if proxy_info and proxy_info['is_running']:
                    proxies = {
                        'http': proxy_info['http_proxy'],
                        'https': proxy_info['http_proxy']
                    }
                    response = requests.post(url, headers=headers, proxies=proxies, timeout=10)
                else:
                    logger.error("Proxy not running, falling back to direct request")
                    response = requests.post(url, headers=headers, timeout=10)
            except Exception as e:
                logger.error(f"Proxy guest token request failed: {e}")
                logger.info("Falling back to direct request for guest token...")
                response = requests.post(url, headers=headers, timeout=10)
        else:
            response = requests.post(url, headers=headers, timeout=10)
        
        if response and response.status_code == 200:
            data = response.json()
            token = data.get('guest_token')
            if token:
                logger.info(f"Got guest token via {'proxy' if proxy_handler else 'direct'}: {token}")
            return token
        else:
            logger.info(f"Failed to get guest token: {response.status_code if response else 'No response'}")
            return None
    except Exception as e:
        logger.info(f"Error getting guest token: {e}")
        return None


def get_valid_guest_token(proxy_handler=None):
    global current_guest_token, token_created_time
    
    # Check if we have a valid token (less than 2 hours old)
    if current_guest_token and token_created_time:
        token_age = time.time() - token_created_time
        if token_age < 7200:  # 2 hours in seconds
            logger.info(f"Using cached guest token (age: {token_age/60:.1f} minutes)")
            return current_guest_token
    
    # Get a new token using the same proxy
    logger.info("Getting new guest token...")
    new_token = get_guest_token(proxy_handler)
    if new_token:
        current_guest_token = new_token
        token_created_time = time.time()
        logger.info(f"New guest token obtained: {new_token}")
        return new_token
    else:
        logger.info("Failed to get new guest token")
        return None

def get_user_profile(screen_name, proxy_handler: ProxyHandler):
    url = "https://api.x.com/graphql/6ND0OKRCgPajU_yJbcWSVw/UserByScreenName"
    
    # Build variables with the provided screen_name
    variables = {
        "screen_name": screen_name,
        "withGrokTranslatedBio": False
    }
    
    params = {
        "variables": json.dumps(variables),
        "features": '{"hidden_profile_subscriptions_enabled":true,"payments_enabled":false,"profile_label_improvements_pcf_label_in_post_enabled":true,"responsive_web_profile_redirect_enabled":false,"rweb_tipjar_consumption_enabled":true,"verified_phone_label_enabled":false,"subscriptions_verification_info_is_identity_verified_enabled":true,"subscriptions_verification_info_verified_since_enabled":true,"highlights_tweets_tab_ui_enabled":true,"responsive_web_twitter_article_notes_tab_enabled":true,"subscriptions_feature_can_gift_premium":true,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"responsive_web_graphql_timeline_navigation_enabled":true}',
        "fieldToggles": '{"withAuxiliaryUserLabels":true}'
    }

    # Get a valid guest token (cached or new) using the same proxy
    guest_token = get_valid_guest_token(proxy_handler)
    if not guest_token:
        logger.info("Failed to get valid guest token")
        return None
    
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
        "content-type": "application/json",
        "cookie": "guest_id=v1%3A175895382677414348; __cuid=c591bd35ae514cb39b6f04f1bb662cd2; gt=1980497421584027663; __cf_bm=MezAQTaFf3ahZggLfKwlqNFFGLyCgriI1Z.GyRZRwpo-1761022477.2995093-1.0.1.1-r9Yuk6ULqGLtl72FMCL_mK7yXTjQawnbLuj1tkUXOfL3DSkyrsMe8zrhZgwOB7zriZfRHE2l1KOKO5SdbCafTSSOnpYAosN_gFfGwXI7_aZN5_Jmy3Nm5QR1tRsuREq_",
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
        "x-client-transaction-id": "UwHoheU4n/sJddnouxyeNI2XrUhe3MDmeEImw+7pGnQQ3nzEJDNbfPJORgaDj7eNAYiQ9FcnXcxvy4D1Ogqmns89lg+5UA",
        "x-guest-token": guest_token,  # Use the cached/valid token
        "x-twitter-active-user": "yes",
        "x-twitter-client-language": "en",
        "x-xp-forwarded-for": "63c97689614fbc705f33244c31d3c2811fe59c7990dea761644b771fa92c5de7c6449201982bebc88894f020b74acff5b2f2696170b31cad17e288fe064aeac92b452bd412bc0b7df9b3efb986d99b2c092200c91bc313a870745ee519d6742307cda111bdb00d2197fff6acc21393b80b1f5f57ce963bea45fbe018dde3c256a7aa4f05421829889f28333529a364c2ceab2c9a1f59ba2e053ba0e9b1f96e68521dd7ffa893c09a66d9bab3c759b6cbeebfdf0153a0ae6bdd6eb8db81823fa07f6fed50605966dbd61ca2680f59ccc303edddfbef1cbfe303475e9f761b654587fd2793764e383d454f9dcfbac63c4ec6870634c8f77e82df4df6"
    }

    # Get proxy info and make request with requests library
    proxy_info = proxy_handler.get_current_proxy_info()
    if proxy_info and proxy_info['is_running']:
        proxies = {
            'http': proxy_info['http_proxy'],
            'https': proxy_info['http_proxy']
        }
        response = requests.get(url, headers=headers, params=params, proxies=proxies, timeout=15)
    else:
        logger.error("Proxy not running, falling back to direct request")
        response = requests.get(url, headers=headers, params=params, timeout=15)
    
    if response and response.status_code == 200:
        try:
            remaining_requests = int(response.headers.get("x-rate-limit-remaining", 0))
            logger.info(f"Remaining requests: {remaining_requests}")
            data = response.json()
            return data
        except json.JSONDecodeError:
            logger.info("Response is not valid JSON")
            logger.info(response.text[:1000])
            return None

    # Handle 403 or 429 errors
    if response and (response.status_code == 403 or response.status_code == 429):
        logger.info(f"Got {response.status_code} error, getting new token and retrying...")
        
        # Invalidate current token
        global current_guest_token, token_created_time
        current_guest_token = None
        token_created_time = None

        # Get new guest token
        new_guest_token = get_guest_token(proxy_handler)
        if new_guest_token:
            # Update global variables
            current_guest_token = new_guest_token
            token_created_time = time.time()
            logger.info(f"Got new guest token: {new_guest_token}")
            
            # Update headers with new guest token
            headers["x-guest-token"] = new_guest_token
            
            # Retry with new token
            proxy_info = proxy_handler.get_current_proxy_info()
            if proxy_info and proxy_info['is_running']:
                proxies = {
                    'http': proxy_info['http_proxy'],
                    'https': proxy_info['http_proxy']
                }
                retry_response = requests.get(url, headers=headers, params=params, proxies=proxies, timeout=15)
            else:
                logger.error("Proxy not running, falling back to direct request")
                retry_response = requests.get(url, headers=headers, params=params, timeout=15)
            
            # Check if retry was successful
            if retry_response and retry_response.status_code == 200:
                try:
                    remaining_requests = int(retry_response.headers.get("x-rate-limit-remaining", 0))
                    logger.info(f"Retry successful! Remaining requests: {remaining_requests}")
                    data = retry_response.json()
                    return data
                except json.JSONDecodeError:
                    logger.info("Retry response is not valid JSON")
                    logger.info(retry_response.text[:1000])
                    return None
            else:
                # Retry failed, rotate proxy and recall function
                logger.info(f"Retry failed with status: {retry_response.status_code if retry_response else 'No response'}")
                logger.info("Rotating proxy and retrying...")
                proxy_handler.rotate_proxy()
                return get_user_profile(screen_name=screen_name, proxy_handler=proxy_handler)
        else:
            # Failed to get new token, rotate proxy and recall function
            logger.info("Failed to get new guest token, rotating proxy and retrying...")
            proxy_handler.rotate_proxy()
            return get_user_profile(screen_name=screen_name, proxy_handler=proxy_handler)
    
    return None

def parse_user_profile(user_by_screen_name, username):
    """
    Parse user profile from the JSON response and extract useful information
    
    Args:
        user_by_screen_name (dict): JSON response from Twitter API
    
    Returns:
        dict: Parsed user profile dictionary
    """
    try:
        # Navigate through the nested JSON structure
        user_data = user_by_screen_name.get('data', {}).get('user', {}).get('result', {})
        
        if user_data.get('__typename') == 'User':
            profile = {
                'id': user_data.get('id'),
                'rest_id': user_data.get('rest_id'),
                'link': 'https://x.com/' + username,
                'avatar_url': user_data.get('avatar', {}).get('image_url', ''),
                'name': user_data.get('core', {}).get('name', ''),
                'screen_name': user_data.get('core', {}).get('screen_name', ''),
                'join_date': user_data.get('core', {}).get('created_at', ''),
                'verified': user_data.get('legacy', {}).get('is_blue_verified') == True,
                'description': user_data.get('legacy', {}).get('description', ''),
                'url': user_data.get('legacy', {}).get('url', ''),
                'favourites_count': user_data.get('legacy', {}).get('favourites_count', 0),
                'followers_count': user_data.get('legacy', {}).get('followers_count', 0),
                'friends_count': user_data.get('legacy', {}).get('friends_count', 0),
                'normal_followers_count': user_data.get('legacy', {}).get('normal_followers_count', 0),
                'profile_banner_url': user_data.get('legacy', {}).get('profile_banner_url', ''),
                'statuses_count': user_data.get('legacy', {}).get('statuses_count', 0),
                'location': user_data.get('legacy', {}).get('location', {}).get('location'),
                'protected': user_data.get('privacy', {}).get('protected', False),
                'listed_count': user_data.get('legacy', {}).get('listed_count', 0),
                'media_count': user_data.get('legacy', {}).get('media_count', 0),
            }
            logger.info(f"User profile: {json.dumps(profile, indent=2, ensure_ascii=False)}")
            return profile
        else:
            logger.info(f"User not found or invalid response type: {user_data.get('__typename', 'Unknown')}")
            return None
    
    except Exception as e:
        logger.info(f"Error parsing user profile: {e}")
        return None


# Main execution
if __name__ == "__main__":
    logger.info("Starting Twitter API Scraper with Proxy Support")
    logger.info("=" * 60)
    
    # Initialize proxy handler
    xray_configs = get_xray_configs()
    logger.info(f"Xray configs: {xray_configs}")
    proxy_handler = None
    
    if xray_configs:
        try:
            proxy_handler = ProxyHandler(xray_configs)
            # Start the proxy
            if proxy_handler.start_proxy():
                logger.info(f"✅ Proxy handler initialized with {len(xray_configs)} configurations")
                logger.info("Using proxy for all requests")
            else:
                logger.error("❌ Failed to start proxy")
                proxy_handler = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize proxy handler: {e}")
            logger.info("Continuing without proxy...")
    else:
        logger.info("No Xray configurations found, running without proxy")
    
    # Example usage - you can change the screen names
    screen_names = [
        "alborz_cthh",
        "MCTH_ir",
        "gilan_cthh",
        "zanjan_cthh",
        "Bushehr_cthh",
        "qazvin_cthh",
        "fars_cthh",
        "ardabil_cthh",
        "kermanshah_cthh",
        "semnan_cthh",
        "Tehran_cthh",
        "Chb_cthh",
        "kb_cthh",
        "yazd_cthh",
        "golestan_cthh",
        "isfahan_cthh",
        "skh_cthh",
        "hormozgan_cthh",
        "Nkhcthh",
        "ea_cthh",
        "kerman_cthh",
        "qom_cthh1",
        "Khuzestan_cthh",
        "Azadshahr_cthh",
        "_kordkuy_",
        "gomishancthh",
        "Gonbad_CTHH",
        "Wa_cthh",
        "sb_cthh",
        "mazandaran_cthh",
        "MCTH_ir",
        "chtniran",
        "bbcpersian",
        "Erfan_khosravi",
        "HajNooredin",
        "s_saffarianpour",
        "Mohammad_kali",
        "jadi",
        "IranianArts",
        "be_a_pointer",
        "Tigress1401",
        "YasharTad114108",
        "JavidShahansha",
        "S67187541Shakil",
        "Black7192Swan",
        "flamingo_irani2",
        "Iran1Asl",
        "peymannarad",
        "MIIran20194",
        "KiMo10626877",
        "unquiet_mind_1",
        "1111aphrodite",
        "atheistChild789",
        "jabijoon26588",
        "avaavaavin",
        "Atista_2023",
        "iranbanoo_",
        "1111aphrodite",
        "JavidShahansha",
        "Ario1401",
        "JamesDeanUFO",
        "pahlaviiran021",
        "alichi1992",
        "unquiet_mind_1",
        "Kamash5014b",
        "avaavaavin",
        "adam_hesabi2",
        "1111aphrodite",
        "BhmnyS87340",
        "JZarif",
        "ir_aref",
        "Khamenei_fa",
        "DrAboutalebi",
        "RezaNasri1",
        "Drvelayati_ir",
        "drpezeshkian",
        "SKhatibzadeh",
        "TakhtRavanchi",
        "SAMOUSAVI9",
        "ebtekarm",
        "araghchi",
        "khamenei_ir",
        "HassanRouhani",
        "Iran_GOV",
        "ASGgars",
        "BBCArdalan",
        "alireza1356",
        "Vesal70680850",
        "_hanayoo_",
        "AzadeMokhtari",
        "ungodsun",
        "seyd_laghar",
        "mostfaqasemii",
        "RasamRostami",
        "sasantabatabae",
        "hamedan_cthh1",
        "Majidxfuture",
        "SKeyvanian",
        "HRKeshavarz",
        "alandi76",
        "CosmikDebriss",
        "hlpstl",
        "abornaei",
        "iranologyscty",
        "Koronmusic",
        "Manaartlover1",
        "TheCyrusPersia",
        "FadaSalar",
        "Zeidabadi_Ahmad",
        "bhrzazdi",
        "DrSadaf_",
        "babakm1912a2510",
        "Morfi",
        "negar_mansouri",
        "woodstory_",
        "JoeAntonio63",
        "xerxesss",
        "Iranland7",
        "manmmdrzam",
        "_maedeeh",
        "BigKayko",
        "smaeel_azari",
        "badman3739",
        "khashayarsefidi",
        "Mahdi_MrEditor",
        "hoshangsherafat",
        "mahsa_iii",
        "nemidunamkiam",
        "Stervende__",
        "KavehFaizolahi",
        "ALIJOONZ121",
        "Eslahatnews_com",
        "Husein6485",
        "fatym2912",
        "bababahdg",
        "gheermez",
        "saraghanavati1",
        "farhadge",
        "jahangiri_biz",
        "mrchichooo",
        "mr_faeghi",
        "abdolah_abdi",
        "Mitra7378",
        "MehdiMohraz",
        "aghmamrez",
        "mamaddooo",
        "abelbalb",
        "saeed_karimi_ir",
        "baran__ahmadi",
        "RashidpourReza",
        "marlik_ir",
        "YousefJafary",
        "noora3155",
        "Iranland7",
        "AhmadrezaGz",
        "Amir60118403",
        "hafezeh_tarikhi",
        "vakilipor",
        "cryptosamz",
        "Badbunnyis",
        "Ms_atiyeh",
        "so_ha_ka",
        "so_ha_ka",
        "HSetareh",
        "realbardia",
    ]

    if proxy_handler:
        stats = proxy_handler.get_proxy_stats()
        proxy_info = proxy_handler.get_current_proxy_info()

    while True:
        logger.info(f"Total users: {len(screen_names)}")
        
        try:
            for i, screen_name in enumerate(screen_names):
                logger.info(f"Fetching profile for user: @{screen_name}")
                
                # Show proxy status
                # if proxy_handler:
                #     stats = proxy_handler.get_proxy_stats()
                #     proxy_info = proxy_handler.get_current_proxy_info()
                #     logger.info(f"Proxy status: {stats['healthy_proxies']}/{stats['total_proxies']} healthy, current: {stats['current_proxy']}, running: {proxy_info['is_running'] if proxy_info else False}")
                
                response = get_user_profile(screen_name=screen_name, proxy_handler=proxy_handler)

                if response:
                    logger.info("Status: Success")
                    
                    # Write response to file
                    filename = f"twitter_profile_{screen_name}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(response, f, indent=2, ensure_ascii=False)
                    logger.info(f"Response saved to: {filename}")
                    
                    # Also save a readable text version
                    text_filename = f"twitter_profile_{screen_name}.txt"
                    with open(text_filename, 'w', encoding='utf-8') as f:
                        f.write(f"Twitter Profile for @{screen_name}\n")
                        f.write("=" * 50 + "\n\n")
                        
                        # Parse and write profile in readable format
                        profile = parse_user_profile(user_by_screen_name=response, username=screen_name)
                        if profile:
                            f.write(f"Name: {profile['name']}\n")
                            f.write(f"Username: @{profile['screen_name']}\n")
                            f.write(f"ID: {profile['id']}\n")
                            f.write(f"Description: {profile['description']}\n")
                            f.write(f"Location: {profile['location']}\n")
                            f.write(f"Website: {profile['url']}\n")
                            f.write(f"Followers: {profile['followers_count']:,}\n")
                            f.write(f"Following: {profile['friends_count']:,}\n")
                            f.write(f"Tweets: {profile['statuses_count']:,}\n")
                            f.write(f"Likes: {profile['favourites_count']:,}\n")
                            f.write(f"Verified: {'Yes' if profile['verified'] else 'No'}\n")
                            f.write(f"Protected: {'Yes' if profile['protected'] else 'No'}\n")
                            f.write(f"Joined: {profile['join_date']}\n")
                            f.write(f"Profile Image: {profile['avatar_url']}\n")
                            if profile['profile_banner_url']:
                                f.write(f"Banner Image: {profile['profile_banner_url']}\n")
                        else:
                            f.write("Profile not found or could not be parsed\n")
                        
                        # Also write the raw JSON at the end
                        f.write("\n" + "=" * 50 + "\n")
                        f.write("RAW JSON RESPONSE:\n")
                        f.write("=" * 50 + "\n")
                        f.write(json.dumps(response, indent=2, ensure_ascii=False))
                    
                    logger.info(f"Readable format saved to: {text_filename}")
                else:
                    logger.info(f"Failed to fetch profile for user: @{screen_name}")
                    # Still create an error file
                    error_filename = f"twitter_error_{screen_name}.txt"
                    with open(error_filename, 'w', encoding='utf-8') as f:
                        f.write(f"Failed to fetch profile for @{screen_name}\n")
                        f.write("This could be due to:\n")
                        f.write("- Invalid username\n")
                        f.write("- Rate limiting\n")
                        f.write("- Network issues\n")
                        f.write("- API changes\n")
                        f.write("- Proxy issues\n")
                    logger.info(f"Error log saved to: {error_filename}")
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

    if proxy_handler:
        logger.info("Stopping proxy handler...")
        proxy_handler.stop()
    logger.info("Twitter scraper stopped")

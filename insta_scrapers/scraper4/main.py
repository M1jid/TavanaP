import os
import json
import time
import random
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError, Error
from elasticsearch import Elasticsearch
import socket
import warnings
from minio_handler import MinIOHandler
from minio_config import get_minio_config
import requests
from io import BytesIO

# ==============================
# تنظیمات اصلی
# ==============================
INSTAGRAM_USERNAME = "innovationss420"
INSTAGRAM_PASSWORD = "MMMMMmmmmm@12345"

USERS_FILE = "shared/instagram.txt"
DATA_FILE = "data.json"
SESSION_STATE = "session.json"
ES_HOST = "https://192.168.10.60:9200"
ES_INDEX = "instagram_pages_data"

MAX_RETRIES = 300000
RETRY_DELAY = 30

# پروکسی SOCKS5 برای Playwright و requests
PROXY_SERVER = "socks5://192.168.10.50:10808"
PROXIES = {
    "http": "socks5h://192.168.10.50:10808",
    "https": "socks5h://192.168.10.50:10808",
}

warnings.filterwarnings("ignore", category=UserWarning)

# اتصال به Elasticsearch
es = Elasticsearch(
    ES_HOST,
    basic_auth=("elastic", "change-me"),
    verify_certs=False
)

# اتصال به MinIO (بدون پروکسی)
minio_config = get_minio_config(type='channel')
minio_handler = MinIOHandler(**minio_config)

# ==============================
# مپینگ ایندکس Elasticsearch
# ==============================
mapping = {
    "mappings": {
        "properties": {
            "username": {"type": "keyword"},
            "post_count": {"type": "integer"},
            "follower_count": {"type": "integer"},
            "following_count": {"type": "integer"},
            "bio_text": {"type": "text"},
            "bio_links": {"type": "keyword"},
            "join_date": {"type": "text"},
            "location": {"type": "text"},
            "verified": {"type": "boolean"},
            "scraped_at": {"type": "date"},
            "page_photos": {"type": "keyword"}
        }
    }
}

# ==============================
# توابع کمکی
# ==============================
def load_usernames():
    if not os.path.exists(USERS_FILE):
        print(f"⚠️ File {USERS_FILE} not found.")
        return []
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def save_to_local_file(data):
    existing = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
    existing.append(data)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

def parse_count(count_str):
    count_str = count_str.replace(",", "").replace("٫", "").strip()
    if "k" in count_str.lower():
        return int(float(count_str.lower().replace("k", "")) * 1000)
    elif "m" in count_str.lower():
        return int(float(count_str.lower().replace("m", "")) * 1000000)
    try:
        return int(count_str)
    except ValueError:
        return 0

# ==============================
# دانلود عکس پروفایل + آپلود در MinIO
# ==============================
def download_and_upload_photo(username, url):
    try:
        # دانلود عکس از طریق پروکسی
        resp = requests.get(url, timeout=30, proxies=PROXIES)
        resp.raise_for_status()

        file_obj = BytesIO(resp.content)
        object_name = f"{username}.jpg"

        success = minio_handler.upload_fileobj(
            file_obj,
            object_name=object_name,
            bucket_name="instagram-images-avatar",
            content_type="image/jpeg"
        )

        if success:
            return minio_handler.generate_presigned_url(
                object_name=object_name,
                bucket_name="instagram-images-avatar",
                expiration=86400
            )
        else:
            print(f"❌ Upload failed for @{username}")
            return url

    except requests.RequestException as e:
        print(f"⚠️ Request failed for @{username}: {e}")
        return url
    except Exception as e:
        print(f"❌ Unexpected error for @{username}: {e}")
        return url

# ==============================
# اسکرپر اصلی
# ==============================
def run_scraper():
    usernames = load_usernames()
    if not usernames:
        print("⚠️ No usernames to process.")
        return

    if not es.indices.exists(index=ES_INDEX):
        es.indices.create(index=ES_INDEX, body=mapping)
        print(f"📁 Index '{ES_INDEX}' created.")

    with sync_playwright() as p:
        # اجرای مرورگر با پروکسی
        browser = p.chromium.launch(headless=True, proxy={"server": PROXY_SERVER})
        context = browser.new_context(storage_state=SESSION_STATE if os.path.exists(SESSION_STATE) else None)
        page = context.new_page()

        # ورود یا استفاده از سشن
        if not os.path.exists(SESSION_STATE):
            print("🔐 Logging in...")
            page.goto("https://www.instagram.com/accounts/login/")
            time.sleep(random.randint(5, 30))
            page.wait_for_selector("input[name='username']")
            page.fill("input[name='username']", INSTAGRAM_USERNAME)
            time.sleep(random.randint(2, 10))
            page.fill("input[name='password']", INSTAGRAM_PASSWORD)
            page.click("button[type='submit']")
            time.sleep(random.randint(50, 100))
            context.storage_state(path=SESSION_STATE)
            print("✅ Logged in and session saved.")
        else:
            print("✅ Logged in with saved session.")

        for username in usernames:
            try:
                print(f"\n📥 Checking @{username}...")
                page.goto(f"https://www.instagram.com/{username}/", timeout=60000)
                time.sleep(random.randint(20, 40))

                stats = page.locator('//span[@class="x5n08af x1s688f"]')
                text = stats.all_inner_texts()
                post_count = follower_count = following_count = "❓"
                if len(text) >= 3:
                    post_count, follower_count, following_count = text[:3]

                print(f"📊 Posts: {post_count} | Followers: {follower_count} | Following: {following_count}")

                bio_section = page.locator('//section[contains(@class, "x69nqbv")]')
                bio_texts = bio_section.all_inner_texts()
                bio_combined = bio_texts[0] if bio_texts else ""
                bio_links = [word for word in bio_combined.split() if word.startswith("http") or "t.me/" in word]

                photo_xpath = f'//img[@alt="{username}\'s profile picture"]'
                photo_elem = page.locator(photo_xpath)
                photo_url = photo_elem.get_attribute("src")
                final_photo_url = download_and_upload_photo(username, photo_url) if photo_url else None
                print(f"photo url = {final_photo_url}")

                info_element = page.locator('//a[contains(@class,"_a6hd")]').first
                info_element.click()
                time.sleep(random.randint(5, 30))

                spans = page.locator('//span[@data-bloks-name="bk.components.Text"]')
                all_texts = spans.all_inner_texts()
                join_date = location = None
                verified = False

                for i, t in enumerate(all_texts):
                    t = t.strip()
                    if t == "Date joined" and i + 1 < len(all_texts):
                        join_date = all_texts[i + 1].strip()
                    elif t == "Account based in" and i + 1 < len(all_texts):
                        location = all_texts[i + 1].strip()
                    elif t == "Verified":
                        verified = True

                print(f"📅 Join date: {join_date or 'Not found'}")
                print(f"🌍 Location: {location or 'Not found'}")
                print(f"🔰 Verified: {'✅' if verified else '❌'}")

                doc = {
                    "username": username,
                    "post_count": parse_count(post_count) if post_count != "❓" else 0,
                    "follower_count": parse_count(follower_count) if follower_count != "❓" else 0,
                    "following_count": parse_count(following_count) if following_count != "❓" else 0,
                    "bio_text": bio_combined,
                    "bio_links": bio_links,
                    "join_date": join_date,
                    "location": location,
                    "verified": verified,
                    "scraped_at": datetime.utcnow().isoformat(),
                    "page_photos": final_photo_url
                }

                es.index(index=ES_INDEX, document=doc, id=username)
                save_to_local_file(doc)
                print("✅ Data saved to Elasticsearch and local file.")

            except Exception as e:
                print(f"⚠️ Failed to extract information for @{username}: {e}")

        browser.close()

# ==============================
# حلقه اصلی اجرا
# ==============================
if __name__ == "__main__":
    while True:
        retries = 0
        while retries < MAX_RETRIES:
            try:
                print("🔁 Running scraper...")
                run_scraper()
                break
            except (TimeoutError, Error, socket.gaierror) as e:
                retries += 1
                print(f"⚠️ Error occurred: {e}")
                print(f"🔁 Retry {retries}/{MAX_RETRIES} in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            except Exception as e:
                retries += 1
                print(f"❌ Unknown error: {e}")
                print(f"🔁 Retry {retries}/{MAX_RETRIES} in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)

        print("⏳ Sleeping for 1 week...\n")
        time.sleep(604800)

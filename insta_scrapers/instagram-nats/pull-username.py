#!/usr/bin/env python3
import asyncio
import requests
import json
from datetime import datetime
from nats.aio.client import Client as NATS

# ---------------- Configuration ----------------
API_URL = "http://192.168.10.60:9000/instagram/all"
NATS_SERVER = "nats://192.168.10.61:4222"
CHECK_INTERVAL = 3 * 60 * 60  # 3 hours
SEEN_FILE = "seen_usernames.json"

# ---------------- Logger ----------------
def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

# ---------------- Publisher ----------------
async def publish_periodically():
    # Load seen usernames
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            seen_usernames = set(json.load(f))
        log(f"💾 Loaded {len(seen_usernames)} usernames from state file")
    except (FileNotFoundError, json.JSONDecodeError):
        seen_usernames = set()
        log("⚠️ No previous state found, starting fresh")

    # Connect to NATS
    nc = NATS()
    await nc.connect(NATS_SERVER)
    js = nc.jetstream()
    log(f"✅ Connected to NATS server at {NATS_SERVER}")

    # Ensure streams exist
    for stream_name, subject in [
        ("INSTAGRAM", "instagram.scrape"),
        ("INSTAGRAM_LAST_POSTS", "instagram.last_posts")
    ]:
        try:
            await js.add_stream(
                name=stream_name,
                subjects=[subject],
                storage="file"
            )
            log(f"✅ JetStream stream '{stream_name}' created")
        except Exception:
            log(f"ℹ️ Stream '{stream_name}' already exists or could not be created")

    while True:
        try:
            log(f"🌐 Fetching data from API: {API_URL}")
            response = requests.get(API_URL, timeout=15)
            response.raise_for_status()
            data = response.json()
            log(f"🔍 {len(data)} items fetched from API")

            new_usernames = []
            new_last_posts = []

            for item in data:
                username = item.get("username")
                last_post_url = item.get("last_post")

                # Publish new usernames to first stream
                if username and username not in seen_usernames:
                    await js.publish("instagram.scrape", username.encode())
                    new_usernames.append(username)

                # Publish last posts to second stream
                if username and last_post_url:
                    payload = json.dumps({
                        "username": username,
                        "last_post": last_post_url
                    }).encode()
                    await js.publish("instagram.last_posts", payload)
                    new_last_posts.append(username)

            if new_usernames:
                log(f"📣 Published {len(new_usernames)} new usernames to 'instagram.scrape':")
                for u in new_usernames:
                    log(f"   - {u}")
                seen_usernames.update(new_usernames)
                # Save state
                with open(SEEN_FILE, "w", encoding="utf-8") as f:
                    json.dump(list(seen_usernames), f, ensure_ascii=False, indent=2)
                log(f"💾 State file updated with {len(seen_usernames)} usernames")
            else:
                log("✅ No new usernames to publish")

            if new_last_posts:
                log(f"📤 Published last posts for {len(new_last_posts)} users to 'instagram.last_posts'")

        except Exception as e:
            log(f"❌ Error during publish loop: {e}")

        log(f"⏳ Waiting {CHECK_INTERVAL} seconds until next check...\n")
        await asyncio.sleep(CHECK_INTERVAL)

# ---------------- Entry Point ----------------
if __name__ == "__main__":
    asyncio.run(publish_periodically())

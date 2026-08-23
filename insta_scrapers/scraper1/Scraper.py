import os
import random
import asyncio
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
from nats.aio.client import Client as NATS
from nats.js.api import DeliverPolicy
import requests

# ---------------- Configuration ----------------
NATS_SERVER = "nats://192.168.10.61:4222"
SUBJECT = "instagram.scrape"
QUEUE_GROUP = "instagram_scrapers"
DURABLE_NAME = "instagram_scraper_durable"
API_URL = "http://192.168.10.60:9000/instagram"
INSTAGRAM_USERNAME = "innovationss420"
INSTAGRAM_PASSWORD = "MMMMMmmmmm@12345"
SESSION_STATE = "session.json"
STATE_FILE = "scraper_state.json"
WAIT_HOURS = 3

# ---------------- Helpers ----------------
def log(msg):
    """Timestamped logger"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def load_state():
    if Path(STATE_FILE).exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log(f"⚠️ Failed to load state file: {e}")
            return {}
    return {}

def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        log("💾 State saved successfully")
    except Exception as e:
        log(f"⚠️ Failed to save state: {e}")

# ---------------- Playwright Async Scraper ----------------
async def scrape_user(username: str):
    log(f"🚀 Starting scrape for {username}")
    last_link = None
    post_count = None
    PROXY_SERVER = "http://192.168.10.50:10809"
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                proxy={"server": PROXY_SERVER}
            )
            context = await browser.new_context(
                storage_state=SESSION_STATE if os.path.exists(SESSION_STATE) else None
            )
            page = await context.new_page()

            if not os.path.exists(SESSION_STATE):
                log("🔑 Logging into Instagram...")
                await page.goto("https://www.instagram.com/accounts/login/", timeout=60000)
                await page.fill("input[name='username']", INSTAGRAM_USERNAME)
                await page.fill("input[name='password']", INSTAGRAM_PASSWORD)
                await page.click("button[type='submit']")
                await asyncio.sleep(random.randint(5, 10))
                await context.storage_state(path=SESSION_STATE)
                log("✅ Logged in and session saved")

            log(f"🌐 Opening profile: {username}")
            await page.goto(f"https://www.instagram.com/{username}/", timeout=60000)
            await asyncio.sleep(random.randint(3, 7))

            # Get post count
            try:
                locator = page.locator('//span[@class="x5n08af x1s688f"]')
                await locator.nth(0).wait_for(timeout=5000)
                text = (await locator.nth(0).inner_text()).replace(",", "").strip()
                post_count = int(text) if text.isdigit() else None
            except Exception as e:
                log(f"❌ Error getting post count: {e}")

            # Get last post link
            if post_count is not None:
                try:
                    post_divs = page.locator('//div[@class="xg7h5cd x1n2onr6"]')
                    await post_divs.first.wait_for(timeout=5000)
                    a_tags = post_divs.nth(0).locator("a")
                    if await a_tags.count() > 0:
                        href = await a_tags.nth(0).get_attribute("href")
                        if href:
                            last_link = "https://www.instagram.com" + href
                except Exception as e:
                    log(f"⚠️ Could not get last post link: {e}")

            await browser.close()
    except Exception as e:
        log(f"❌ Scrape failed for {username}: {e}")

    log(f"🏁 Finished scrape for {username}")
    return post_count, last_link

# ---------------- API updater ----------------
def update_api(username: str, post_count: int, last_link: str):
    try:
        users = requests.get(f"{API_URL}/all", timeout=15).json()
        user_map = {u["username"]: u["id"] for u in users}
        if username in user_map:
            payload = {
                "username": username,
                "last_post_count": post_count or 0,
                "last_post": last_link or "",
                "last_update": datetime.utcnow().isoformat()
            }
            user_id = user_map[username]
            requests.put(f"{API_URL}/{user_id}", json=payload, timeout=15)
            log(f"✅ Updated {username} on API")
        else:
            log(f"⚠️ Username {username} not found in API list")
    except Exception as e:
        log(f"❌ Failed to update API for {username}: {e}")

# ---------------- Main ----------------
async def main():
    nc = NATS()
    await nc.connect(NATS_SERVER)
    log(f"✅ Connected to NATS server at {NATS_SERVER}")

    js = nc.jetstream()

    try:
        await js.add_stream(
            name="INSTAGRAM",
            subjects=[SUBJECT],
            storage="file"
        )
        log("📦 JetStream stream 'INSTAGRAM' created or already exists")
    except Exception:
        pass

    state = load_state()

    while True:
        users = []

        async def collect(msg):
            users.append(msg.data.decode())

        sub = await js.subscribe(SUBJECT, durable=DURABLE_NAME, cb=collect, deliver_policy=DeliverPolicy.ALL)
        await asyncio.sleep(5)
        await sub.unsubscribe()

        log(f"📂 Collected {len(users)} users from NATS")

        for username in users:
            prev_post_count = state.get(username, {}).get("last_post_count", 0)
            prev_last_link = state.get(username, {}).get("last_post", "")
            post_count, last_link = await scrape_user(username)

            if post_count is None:
                log(f"❌ Failed to get posts for {username}")
                continue

            if post_count != prev_post_count or last_link != prev_last_link:
                log(f"📈 Change detected for {username}, updating API...")
                update_api(username, post_count, last_link)
                state[username] = {
                    "last_post_count": post_count,
                    "last_post": last_link
                }
                save_state(state)
            else:
                log(f"✅ No new posts for {username}")

        log(f"⏳ تمام یوزرها اسکرپ شدن. منتظر {WAIT_HOURS} ساعت بعدی می‌مانیم...")
        await asyncio.sleep(WAIT_HOURS * 3600)

if __name__ == "__main__":
    asyncio.run(main())

import os
import time
import random
from playwright.sync_api import sync_playwright
SESSION_STATE = "session.json"


def like_posts(session_state):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=session_state if os.path.exists(session_state) else None)
        page = context.new_page()
        page.goto("https://www.instagram.com/explore/")
        time.sleep(random.uniform(10, 100))

        for _ in range(5):
            page.mouse.wheel(0, 1000)
            time.sleep(2)

        print("🔍 Scanning posts...")
        posts = page.locator("a[href*='/p/']")
        count = posts.count()
        print(f"📷 Found {count} posts.")

        for i in range(min(count, 100)):
            try:
                post = posts.nth(i)
                post.scroll_into_view_if_needed()
                post.click()
                print(f"\n📥 Opened post {i+1}")

                page.wait_for_selector('div[role="dialog"]', timeout=10000)
                time.sleep(random.uniform(10, 100))

                if random.random() < 0.55:
                    print("💤 Waiting 30 seconds before liking...")
                    time.sleep(random.uniform(20, 30))

                    dialog_box = page.locator('div[role="dialog"]')
                    box = dialog_box.bounding_box()
                    if box:
                        center_x = box["x"] + (box["width"] / 4)  # وسط نیمه چپ
                        center_y = box["y"] + (box["height"] / 2)  # وسط عمودی
                        page.mouse.click(center_x, center_y, click_count=2, delay=100)
                        print("❤️ Double-clicked to like (left-center)!")
                    else:
                        print("❌ Couldn't find dialog box position.")
                else:
                    print("👀 Skipped this post.")

                close_btn = page.locator('svg[aria-label="Close"]').first
                if close_btn.is_visible():
                    close_btn.click()
                else:
                    page.keyboard.press("Escape")

                time.sleep(random.uniform(10, 100))

            except Exception as e:
                print(f"❌ Error in post {i+1}: {e}")
                try:
                    page.keyboard.press("Escape")
                    time.sleep(50)
                except:
                    pass
                continue

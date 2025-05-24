import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

LOGIN_URL = os.getenv("LOGIN_URL")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
STORAGE_STATE = os.getenv("STORAGE_STATE") or "cookies/frieda_state.json"

def login_and_debug():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print(f"[*] Navigating to {LOGIN_URL}")
        page.goto(LOGIN_URL)
        page.wait_for_selector("input#username", timeout=15000)

        print("[*] Filling login form...")
        page.fill("input#username", USERNAME)
        page.fill("input#password", PASSWORD)

        print("[*] Attempting to submit login...")

        login_success = False
        try:
            page.click("button:has-text('Sign In')")
            login_success = True
        except:
            try:
                page.locator("//button[contains(text(), 'Sign In')]").click()
                login_success = True
            except:
                try:
                    page.press("input#password", "Enter")
                    login_success = True
                except Exception as e:
                    print(f"[!] Login failed: {e}")

        page.wait_for_timeout(3000)  # let page settle

        # Screenshot and HTML capture
        print("[*] Saving debug artifacts...")
        os.makedirs("debug", exist_ok=True)
        page.screenshot(path="debug/post_login_attempt.png")
        with open("debug/post_login_page.html", "w", encoding="utf-8") as f:
            f.write(page.content())

        if login_success:
            print("[*] Saving session state...")
            context.storage_state(path=STORAGE_STATE)
            print(f"[*] Login success. Session saved to {STORAGE_STATE}")
        else:
            print("[!] Login action may have failed. Check screenshot and HTML.")

        browser.close()

if __name__ == "__main__":
    login_and_debug()


import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load from .env
load_dotenv()

LOGIN_URL = os.getenv("LOGIN_URL")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
STORAGE_STATE = os.getenv("STORAGE_STATE") or "cookies/frieda_state.json"


def login_and_save_storage():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print(f"[*] Navigating to {LOGIN_URL}")
        page.goto(LOGIN_URL)

        # Wait for login form
        page.wait_for_selector("input#username", timeout=15000)

        # Fill credentials
        print("[*] Filling login form...")
        page.fill("input#username", USERNAME)
        page.fill("input#password", PASSWORD)

        # Dismiss cookie banner if present
        try:
            page.click(
                "text=Cookie Settings >> xpath=../..//button[contains(., '×')]")
        except BaseException:
            pass  # ignore if not found

        # Attempt to click Sign In
        print("[*] Attempting login...")
        try:
            page.click("button:has-text('Sign In')")
        except BaseException:
            try:
                page.locator("//button[contains(text(), 'Sign In')]").click()
            except BaseException:
                page.press("input#password", "Enter")

        # Wait for the result to load
        page.wait_for_timeout(3000)

        # Save session storage state
        os.makedirs(os.path.dirname(STORAGE_STATE), exist_ok=True)
        context.storage_state(path=STORAGE_STATE)

        print(f"✅ Login successful. Session saved to {STORAGE_STATE}")
        browser.close()


if __name__ == "__main__":
    login_and_save_storage()

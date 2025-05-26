import os
import pickle
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load .env file
load_dotenv()

LOGIN_URL = os.getenv(
    "LOGIN_URL") or "https://the-internet.herokuapp.com/login"
USERNAME = os.getenv("USERNAME") or "default_user"
PASSWORD = os.getenv("PASSWORD") or "default_pass"
COOKIES_FILE = os.getenv("COOKIES_FILE") or "cookies.pkl"


def login_and_save_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print(f"[*] Logging in to {LOGIN_URL}")
        page.goto(LOGIN_URL)
        page.fill("#username", USERNAME)
        page.fill("#password", PASSWORD)
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")

        print("[*] Login complete. Saving cookies...")
        cookies = context.cookies()
        with open(COOKIES_FILE, "wb") as f:
            pickle.dump(cookies, f)

        print(f"[*] Saved cookies to {COOKIES_FILE}")
        browser.close()


def load_cookies_and_browse():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()

        if not os.path.exists(COOKIES_FILE):
            print(f"[!] Cookie file '{COOKIES_FILE}' not found.")
            return

        with open(COOKIES_FILE, "rb") as f:
            cookies = pickle.load(f)
            context.add_cookies(cookies)

        page = context.new_page()
        post_login_url = LOGIN_URL.replace("login", "secure")
        page.goto(post_login_url)

        print("[*] Loaded session. Exploring links...")
        links = page.query_selector_all("a")

        for link in links:
            href = link.get_attribute("href")
            if href:
                print("-> Found link:", href)

        browser.close()


if __name__ == "__main__":
    print("1. Running login and cookie saver...")
    login_and_save_cookies()
    print("2. Reopening browser with cookies...")
    load_cookies_and_browse()

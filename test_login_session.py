import pickle
from playwright.sync_api import sync_playwright

LOGIN_URL = "https://the-internet.herokuapp.com/login"
USERNAME = "tomsmith"
PASSWORD = "SuperSecretPassword!"
COOKIES_FILE = "cookies.pkl"

def login_and_save_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("[*] Logging in...")
        page.goto(LOGIN_URL)
        page.fill("#username", USERNAME)
        page.fill("#password", PASSWORD)
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")

        print("[*] Login complete. Saving cookies...")
        cookies = context.cookies()
        with open(COOKIES_FILE, "wb") as f:
            pickle.dump(cookies, f)

        print("[*] Saved cookies to", COOKIES_FILE)
        browser.close()

def load_cookies_and_browse():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()

        with open(COOKIES_FILE, "rb") as f:
            cookies = pickle.load(f)
            context.add_cookies(cookies)

        page = context.new_page()
        page.goto("https://the-internet.herokuapp.com/secure")

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


import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

ACCOUNT_RECOVERY_URL = "https://fsso.ama-assn.org/account-recovery"
STORAGE_STATE = os.getenv("STORAGE_STATE") or "cookies/frieda_state.json"

def skip_account_recovery():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        context = browser.new_context(storage_state=STORAGE_STATE)
        page = context.new_page()

        print(f"[*] Navigating to {ACCOUNT_RECOVERY_URL}")
        page.goto(ACCOUNT_RECOVERY_URL)
        page.wait_for_load_state("networkidle")

        print("[*] Clicking 'Do Not Ask Again'...")
        page.click("text=Do Not Ask Again")
        page.wait_for_timeout(2000)

        browser.close()

if __name__ == "__main__":
    skip_account_recovery()


# Scraper for FREIDA programs list using Playwright (to support JavaScript-rendered content)

import time
import pandas as pd
from playwright.sync_api import sync_playwright

START_URL_TEMPLATE = "https://freida.ama-assn.org/search/list?spec=42771&page={page}"


def extract_program_data(page):
    data = []
    cards = page.query_selector_all(".search-result-card")
    for card in cards:
        try:
            title_elem = card.query_selector(".search-result-card__title")
            footer = card.query_selector(".search-result-card__footer span")

            program_id = footer.inner_text().replace("ID:", "").strip()
            program_name = title_elem.inner_text().strip()
            program_link = f"https://freida.ama-assn.org/program/{program_id}"

            data.append({
                "program_id": program_id,
                "program_name": program_name,
                "program_link": program_link
            })
        except Exception as e:
            print(f"[!] Error parsing card: {e}")
    return data


def scrape_all_pages():
    all_data = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page_num = 1
        while True:
            url = START_URL_TEMPLATE.format(page=page_num)
            print(f"[*] Navigating to {url}")
            try:
                page.goto(url, wait_until="networkidle")
                page.wait_for_selector(".search-result-card", timeout=10000)
            except Exception as e:
                print(f"[!] Failed to load or wait for content on page {page_num}: {e}")
                break

            page_data = extract_program_data(page)
            if not page_data:
                print("[!] No more data found.")
                break

            all_data.extend(page_data)
            page_num += 1
            time.sleep(1.0)

        browser.close()

    return all_data


if __name__ == "__main__":
    try:
        data = scrape_all_pages()
        if data:
            df = pd.DataFrame(data)
            df.to_csv("freida_programs.csv", index=False)
            print("✅ Scrape complete. Saved to freida_programs.csv")
        else:
            print("⚠️ No data scraped.")
    except Exception as e:
        print(f"[!] Unexpected error: {e}")


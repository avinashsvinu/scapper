# Scraper for FREIDA programs list using Playwright (supports JavaScript-rendered content)

import time
import pandas as pd
from playwright.sync_api import sync_playwright
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

START_URL_TEMPLATE = "https://freida.ama-assn.org/search/list?spec=42771&page={page}"


def extract_program_data(page):
    data = []
    cards = page.query_selector_all(".search-result-card")
    logging.info(f"Found {len(cards)} program cards on page.")
    for idx, card in enumerate(cards):
        try:
            id_span = card.query_selector("footer span:nth-of-type(2)")
            if not id_span:
                logging.warning(f"Card {idx}: Missing ID span element.")
                continue

            program_id = id_span.inner_text().replace("ID:", "").strip()
            logging.info(f"Extracted program ID: {program_id}")

            data.append({
                "program_id": program_id
            })
        except Exception as e:
            logging.warning(f"Card {idx}: Error parsing ID: {e}")
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
            logging.info(f"Navigating to {url}")
            try:
                page.goto(url, wait_until="networkidle")
                page.wait_for_selector(".search-result-card", timeout=10000)
            except Exception as e:
                logging.error(f"Failed to load or wait for content on page {page_num}: {e}")
                break

            page_data = extract_program_data(page)
            if not page_data:
                logging.info("No more data found.")
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
            df = pd.DataFrame(data)[["program_id"]]
            df.to_csv("freida_program_ids.csv", index=False)
            logging.info("✅ Scrape complete. Saved to freida_program_ids.csv")
        else:
            logging.warning("⚠️ No data scraped.")
    except Exception as e:
        logging.critical(f"Unexpected error: {e}")

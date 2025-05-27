"""
extract.py

Extracts all FREIDA program IDs by scraping paginated search results.
"""

import logging
import time

import pandas as pd
from playwright.sync_api import sync_playwright

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s')

START_URL_TEMPLATE = "https://freida.ama-assn.org/search/list?spec=42771&page={page}"


def extract_program_data(page):
    """
    Extracts program IDs from all cards on the current page.
    """
    data = []
    cards = page.query_selector_all(".search-result-card")
    logging.info("Found %d program cards on page.", len(cards))
    for idx, card in enumerate(cards):
        try:
            id_span = card.query_selector("footer span:nth-of-type(2)")
            if not id_span:
                logging.warning("Card %d: Missing ID span element.", idx)
                continue
            program_id = id_span.inner_text().replace("ID:", "").strip()
            logging.info("Extracted program ID: %s", program_id)
            data.append({"program_id": program_id})
        except Exception as e:
            logging.warning("Card %d: Error parsing ID: %s", idx, e)
    return data


def scrape_all_pages():
    """
    Scrapes all paginated FREIDA program search result pages and returns a list of program data dicts.
    """
    all_data = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page_num = 1
        while True:
            url = START_URL_TEMPLATE.format(page=page_num)
            logging.info("Navigating to %s", url)
            try:
                page.goto(url, wait_until="networkidle")
                page.wait_for_selector(".search-result-card", timeout=10000)
            except Exception as e:
                logging.error(
                    "Failed to load or wait for content on page %d: %s", page_num, e)
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
        logging.critical("Unexpected error: %s", e)

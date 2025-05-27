"""
acgme_scraper.py

Automates extraction of ACGME accreditation years for FREIDA programs.
Includes OCR fallback and robust error handling.
"""

import argparse
import logging
import os
import random
import re
import sys
import time
from typing import Optional

import pandas as pd
from PIL import Image
import pytesseract
from playwright.sync_api import Page, sync_playwright

ACGME_URL = "https://apps.acgme.org/ads/Public/Programs/Search"
CSV_FILE = "freida_programs_output.csv"
NEW_CSV_FILE = "freida_programs_output_with_academic_year.csv"
SUCCESS_CSV_FILE = "freida_programs_output_success.csv"
FAILED_CSV_FILE = "freida_programs_output_failed.csv"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s')


def human_like_click(page: Page, locator) -> None:
    """
    Simulates a human-like mouse click on a web element using Playwright.
    """
    box = locator.bounding_box()
    if box:
        x_coord = box['x'] + box['width'] / 2
        y_coord = box['y'] + box['height'] / 2
        delay = random.uniform(0.2, 0.7)
        time.sleep(delay)
        page.mouse.move(x_coord, y_coord)
        time.sleep(random.uniform(0.1, 0.3))
        locator.hover()
        time.sleep(random.uniform(0.1, 0.3))
        locator.click(timeout=5000, force=True)
        time.sleep(random.uniform(0.2, 0.5))
    else:
        locator.click(timeout=5000, force=True)


def extract_year_from_image(image_path: str) -> Optional[str]:
    """
    Uses OCR to extract the academic year from a screenshot image.
    Returns the year string if found, else None.
    """
    try:
        text = pytesseract.image_to_string(Image.open(image_path))
        logging.debug("OCR text from %s:\n%s", image_path, text)
        matches = re.findall(r'\b(20\d{2} - 20\d{2})\b', text)
        for match in matches:
            if match and match != '-':
                logging.debug("Extracted academic year from OCR: %s", match)
                return match
        logging.warning(
            "No valid academic year found in OCR text for %s",
            image_path)
        return None
    except (OSError, ValueError) as err:
        logging.error("OCR failed for %s: %s", image_path, err)
        return None


def extract_academic_year_from_table(
    page: Page, program_id: str, screenshot_path: Optional[str] = None
) -> Optional[str]:
    """
    Extracts the academic year from the accreditation table on the ACGME page.
    Falls back to OCR if table extraction fails.
    """
    try:
        page.wait_for_selector('table', timeout=30000)
        rows = page.query_selector_all('table tr')
        logging.debug(
            "Found %d rows in accreditation table for %s",
            len(rows),
            program_id)
        if len(rows) > 1:
            for i in range(1, len(rows)):
                cells = rows[i].query_selector_all('td')
                if cells:
                    year = cells[0].inner_text().strip()
                    if year and year != '-':
                        logging.debug("Extracted academic year: %s", year)
                        return year
                    logging.debug(
                        "Skipping invalid year '%s' in row %d for %s",
                        year,
                        i,
                        program_id)
            logging.error("No valid academic year found for %s", program_id)
            screenshot_path = f"debug_acgme_{program_id}.png"
            try:
                page.screenshot(path=screenshot_path, full_page=True)
                logging.debug("Saved screenshot to %s", screenshot_path)
            except Exception as ss_err:
                logging.error(
                    "Could not save screenshot for %s: %s",
                    program_id,
                    ss_err)
                screenshot_path = None
            if screenshot_path and os.path.exists(screenshot_path):
                ocr_year = extract_year_from_image(screenshot_path)
                if ocr_year:
                    return ocr_year
            return None
        logging.error("No data rows found in table for %s", program_id)
        screenshot_path = f"debug_acgme_{program_id}.png"
        try:
            page.screenshot(path=screenshot_path, full_page=True)
            logging.debug("Saved screenshot to %s", screenshot_path)
        except Exception as ss_err:
            logging.error(
                "Could not save screenshot for %s: %s",
                program_id,
                ss_err)
            screenshot_path = None
        if screenshot_path and os.path.exists(screenshot_path):
            ocr_year = extract_year_from_image(screenshot_path)
            if ocr_year:
                return ocr_year
        return None
    except Exception as err:
        logging.error(
            "Exception in extract_academic_year_from_table for %s: %s",
            program_id,
            err)
        screenshot_path = f"debug_acgme_{program_id}.png"
        try:
            page.screenshot(path=screenshot_path, full_page=True)
            logging.debug("Saved screenshot to %s", screenshot_path)
        except Exception as ss_err:
            logging.error(
                "Could not save screenshot for %s: %s",
                program_id,
                ss_err)
            screenshot_path = None
        if screenshot_path and os.path.exists(screenshot_path):
            ocr_year = extract_year_from_image(screenshot_path)
            if ocr_year:
                return ocr_year
        return None


def get_first_academic_year(page: Page, program_id: str) -> Optional[str]:
    """
    Navigates to the ACGME program page and attempts to extract the first academic year.
    Uses multiple fallback strategies for robustness.
    """
    logging.debug("Navigating to %s for program_id=%s", ACGME_URL, program_id)
    page.goto(ACGME_URL)
    page.fill('input[type="text"]', str(program_id))
    page.press('input[type="text"]', 'Enter')
    page.wait_for_timeout(3500)
    body_text = page.inner_text('body')
    logging.debug("Body text after search: %s", body_text[:200])
    if "No Programs found" in body_text:
        logging.debug("No results for %s", program_id)
        return None
    screenshot_path = None
    try:
        locator = page.locator('text="View Accreditation History"').first
        locator.wait_for(state="attached", timeout=5000)
        locator.scroll_into_view_if_needed(timeout=2000)
        try:
            with page.expect_navigation(timeout=30000):
                human_like_click(page, locator)
            logging.debug(
                "Clicked 'View Accreditation History' for %s (by text locator, human-like)",
                program_id,
            )
        except Exception as click_err:
            logging.warning(
                "Click by text locator failed for %s: %s",
                program_id,
                click_err)
            if "/AccreditationHistoryReport?programId=" in page.url:
                logging.debug(
                    "Already navigated to Accreditation History page for %s, continuing extraction.",
                    program_id,
                )
                return extract_academic_year_from_table(page, program_id, None)
            screenshot_path = f"debug_acgme_{program_id}.png"
            try:
                page.screenshot(path=screenshot_path, full_page=True)
                logging.debug("Saved screenshot to %s", screenshot_path)
            except Exception as ss_err:
                logging.error(
                    "Could not save screenshot for %s: %s",
                    program_id,
                    ss_err)
                screenshot_path = None
            if screenshot_path and os.path.exists(screenshot_path):
                ocr_year = extract_year_from_image(screenshot_path)
                if ocr_year:
                    return ocr_year
            try:
                btn_locator = page.locator(
                    'a.btn.btn-primary:has-text("View Accreditation History")'
                ).first
                btn_locator.wait_for(state="attached", timeout=5000)
                btn_locator.scroll_into_view_if_needed(timeout=2000)
                with page.expect_navigation(timeout=30000):
                    human_like_click(page, btn_locator)
                logging.debug(
                    "Clicked 'View Accreditation History' for %s (by class+text, human-like)",
                    program_id,
                )
            except Exception as btn_err:
                logging.warning(
                    "Click by class+text failed for %s: %s",
                    program_id,
                    btn_err)
                if "/AccreditationHistoryReport?programId=" in page.url:
                    logging.debug(
                        "Already navigated to Accreditation History page for %s, continuing extraction.",
                        program_id,
                    )
                    return extract_academic_year_from_table(
                        page, program_id, None)
                screenshot_path = f"debug_acgme_{program_id}.png"
                try:
                    page.screenshot(path=screenshot_path, full_page=True)
                    logging.debug("Saved screenshot to %s", screenshot_path)
                except Exception as ss_err:
                    logging.error(
                        "Could not save screenshot for %s: %s",
                        program_id,
                        ss_err)
                    screenshot_path = None
                if screenshot_path and os.path.exists(screenshot_path):
                    ocr_year = extract_year_from_image(screenshot_path)
                    if ocr_year:
                        return ocr_year
                try:
                    anchors = page.query_selector_all('a')
                    found = False
                    for anchor in anchors:
                        anchor_text = anchor.inner_text().strip() if anchor else ''
                        anchor_href = anchor.get_attribute(
                            'href') if anchor else ''
                        if (anchor_text == 'View Accreditation History' or (
                                anchor_href and 'AccreditationHistoryReport' in anchor_href)):
                            logging.debug(
                                "Fallback: found <a> with text/href for %s, trying human-like click...",
                                program_id,
                            )
                            anchor.scroll_into_view_if_needed()
                            with page.expect_navigation(timeout=30000):
                                human_like_click(page, anchor)
                            found = True
                            logging.debug(
                                "Clicked 'View Accreditation History' for %s (by <a> parse, human-like)",
                                program_id,
                            )
                            break
                    if not found:
                        logging.warning(
                            "No <a> tag found for fallback click for %s", program_id)
                        if locator:
                            href = locator.get_attribute('href')
                            if href:
                                direct_url = (
                                    f"https://apps.acgme.org{href}" if href.startswith('/') else href)
                                logging.debug(
                                    "Fallback: navigating directly to %s", direct_url)
                                page.goto(direct_url, timeout=30000)
                            else:
                                logging.error(
                                    "No href found for fallback navigation for %s", program_id)
                                return None
                        else:
                            logging.error(
                                "No locator for fallback navigation for %s", program_id)
                            return None
                except Exception as anchor_err:
                    logging.error(
                        "Fallback <a> parse/click failed for %s: %s",
                        program_id,
                        anchor_err)
                    if "/AccreditationHistoryReport?programId=" in page.url:
                        logging.debug(
                            "Already navigated to Accreditation History page for %s, continuing extraction.",
                            program_id,
                        )
                        return extract_academic_year_from_table(
                            page, program_id, None)
                    screenshot_path = f"debug_acgme_{program_id}.png"
                    try:
                        page.screenshot(path=screenshot_path, full_page=True)
                        logging.debug(
                            "Saved screenshot to %s", screenshot_path)
                    except Exception as ss_err:
                        logging.error(
                            "Could not save screenshot for %s: %s", program_id, ss_err)
                        screenshot_path = None
                    if screenshot_path and os.path.exists(screenshot_path):
                        ocr_year = extract_year_from_image(screenshot_path)
                        if ocr_year:
                            return ocr_year
                    return None
        year = extract_academic_year_from_table(page, program_id, None)
        if year is not None:
            return year
        screenshot_path = f"debug_acgme_{program_id}.png"
        try:
            page.screenshot(path=screenshot_path, full_page=True)
            logging.debug("Saved screenshot to %s", screenshot_path)
        except Exception as ss_err:
            logging.error(
                "Could not save screenshot for %s: %s",
                program_id,
                ss_err)
            return extract_academic_year_from_table(
                page, program_id, screenshot_path)
    except Exception as err:
        logging.error("Exception for %s: %s", program_id, err)
        try:
            debug_path = f"debug_acgme_{program_id}.html"
            content = page.content()
            if content and content.strip():
                with open(debug_path, "w", encoding="utf-8") as file_obj:
                    file_obj.write(content)
                logging.debug("Saved debug HTML to %s", debug_path)
            else:
                logging.warning(
                    "Could not save debug HTML for %s: Page content is empty or unavailable.",
                    program_id,
                )
        except Exception as inner_err:
            logging.error(
                "Could not save debug HTML for %s: %s",
                program_id,
                inner_err)
        screenshot_path = f"debug_acgme_{program_id}.png"
        if os.path.exists(screenshot_path):
            ocr_year = extract_year_from_image(screenshot_path)
            if ocr_year:
                return ocr_year
        return None


def get_first_academic_year_with_retry(
    page: Page, program_id: str, max_retries: int = 3
) -> Optional[str]:
    """
    Retries extraction of the first academic year up to max_retries times.
    """
    for attempt in range(1, max_retries + 1):
        logging.debug("Attempt %d for program_id=%s", attempt, program_id)
        year = get_first_academic_year(page, program_id)
        if year:
            return year
        if attempt < max_retries:
            logging.debug(
                "Retrying program_id=%s after failure...",
                program_id)
            time.sleep(2)
    logging.error(
        "All %d attempts failed for program_id=%s",
        max_retries,
        program_id)
    return None


def main() -> None:
    """
    Main entry point for the script. Handles CLI arguments and orchestrates extraction.
    """
    parser = argparse.ArgumentParser(
        description='Scrape ACGME academic years for programs. Supports retrying failed records and OCR fallback.')
    parser.add_argument(
        '--failed-only',
        action='store_true',
        help='Only process records with missing academic year in output CSV (freida_programs_output_with_academic_year.csv).'
    )
    parser.add_argument(
        '--failed-record',
        type=str,
        help='Comma-separated list of program_ids to retry from output CSV (e.g., --failed-record 1405621446,1400500932). Overrides --failed-only if set.'
    )
    args = parser.parse_args()

    logging.info("Starting script. Current working dir: %s", os.getcwd())
    if args.failed_record:
        if not os.path.exists(FAILED_CSV_FILE):
            logging.error(
                "Failed CSV file '%s' not found for --failed-record.",
                FAILED_CSV_FILE)
            sys.exit(1)
        df_failed = pd.read_csv(FAILED_CSV_FILE)
        logging.info("Read %d rows from %s", len(df_failed), FAILED_CSV_FILE)
        id_list = [x.strip()
                   for x in args.failed_record.split(',') if x.strip()]
        failed_df = df_failed[df_failed['program_id'].astype(
            str).isin(id_list)]
        logging.info(
            "Found %d records to retry by --failed-record: %s",
            len(failed_df),
            id_list)
        if len(failed_df) == 0:
            logging.info("No matching records to process. Exiting.")
            return
        process_df = failed_df.copy()
        output_file = FAILED_CSV_FILE
    elif args.failed_only and os.path.exists(FAILED_CSV_FILE):
        df_failed = pd.read_csv(FAILED_CSV_FILE)
        logging.info("Read %d rows from %s", len(df_failed), FAILED_CSV_FILE)
        process_df = df_failed.copy()
        output_file = FAILED_CSV_FILE
    else:
        df_main = pd.read_csv(NEW_CSV_FILE) if os.path.exists(
            NEW_CSV_FILE) else pd.read_csv(CSV_FILE)
        logging.info(
            "Read %d rows from %s", len(df_main),
            'freida_programs_output_with_academic_year.csv' if os.path.exists(NEW_CSV_FILE) else 'freida_programs_output.csv'
        )
        process_df = df_main[df_main['acgme_first_academic_year'].isnull() | (
            df_main['acgme_first_academic_year'].astype(str).str.strip() == '')].copy()
        output_file = NEW_CSV_FILE

    academic_years = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        if args.failed_record:
            iter_df = process_df
        elif args.failed_only:
            iter_df = process_df
        else:
            random_indices = random.sample(
                range(
                    len(process_df)), min(
                    5, len(process_df))) if len(process_df) > 0 else []
            iter_df = process_df.iloc[random_indices] if len(
                random_indices) > 0 else process_df.iloc[[]]
        for idx, row in iter_df.iterrows():
            program_id = row['program_id']
            logging.info(
                "Processing %s (test %d/%d)...",
                program_id,
                idx + 1,
                len(iter_df))
            try:
                year = get_first_academic_year_with_retry(
                    page, program_id, max_retries=3)
            except Exception as err:
                logging.error(
                    "Exception in get_first_academic_year_with_retry: %s", err)
                year = None
            academic_years.append(year)
            time.sleep(1.5)
        browser.close()
    logging.info("Academic years collected: %s", academic_years)
    iter_df = iter_df.copy()
    if 'acgme_first_academic_year' in iter_df.columns:
        iter_df = iter_df.drop(columns=['acgme_first_academic_year'])
    iter_df.insert(0, 'acgme_first_academic_year', academic_years)
    if output_file == FAILED_CSV_FILE:
        if os.path.exists(NEW_CSV_FILE):
            main_df = pd.read_csv(NEW_CSV_FILE)
            for _, row in iter_df.iterrows():
                pid = row['program_id']
                year = row['acgme_first_academic_year'] if 'acgme_first_academic_year' in row else None
                if year and str(year).strip():
                    main_df.loc[main_df['program_id'] == pid,
                                'acgme_first_academic_year'] = year
            main_df.to_csv(NEW_CSV_FILE, index=False)
            df_full = main_df
        else:
            df_full = iter_df
    else:
        full_df = pd.read_csv(output_file)
        for _, row in iter_df.iterrows():
            pid = row['program_id']
            year = row['acgme_first_academic_year'] if 'acgme_first_academic_year' in row else None
            if year and str(year).strip():
                full_df.loc[full_df['program_id'] == pid,
                            'acgme_first_academic_year'] = year
        full_df.to_csv(output_file, index=False)
        df_full = full_df
    success_df = df_full[df_full['acgme_first_academic_year'].notnull() & (
        df_full['acgme_first_academic_year'].astype(str).str.strip() != '')]
    failed_df = df_full[df_full['acgme_first_academic_year'].isnull() | (
        df_full['acgme_first_academic_year'].astype(str).str.strip() == '')]
    success_df.to_csv(SUCCESS_CSV_FILE, index=False)
    failed_df.to_csv(FAILED_CSV_FILE, index=False)
    logging.info(
        "Wrote %d good records to %s and %d failed records to %s",
        len(success_df), SUCCESS_CSV_FILE, len(failed_df), FAILED_CSV_FILE
    )
    logging.info("Script finished.")


if __name__ == "__main__":
    main()

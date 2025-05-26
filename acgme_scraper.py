import csv
import time
from playwright.sync_api import sync_playwright
import pandas as pd
import sys
import os
import random
import argparse
from PIL import Image
import pytesseract
import re

ACGME_URL = "https://apps.acgme.org/ads/Public/Programs/Search"
CSV_FILE = "freida_programs_output.csv"
NEW_CSV_FILE = "freida_programs_output_with_academic_year.csv"
SUCCESS_CSV_FILE = "freida_programs_output_success.csv"
FAILED_CSV_FILE = "freida_programs_output_failed.csv"


def human_like_click(page, locator):
    # Move mouse to the center of the element, add random delay, then click
    box = locator.bounding_box()
    if box:
        x = box['x'] + box['width'] / 2
        y = box['y'] + box['height'] / 2
        delay = random.uniform(0.2, 0.7)
        time.sleep(delay)
        page.mouse.move(x, y)
        time.sleep(random.uniform(0.1, 0.3))
        locator.hover()
        time.sleep(random.uniform(0.1, 0.3))
        locator.click(timeout=5000, force=True)
        time.sleep(random.uniform(0.2, 0.5))
    else:
        locator.click(timeout=5000, force=True)


def extract_year_from_image(image_path):
    try:
        text = pytesseract.image_to_string(Image.open(image_path))
        print(f"[DEBUG] OCR text from {image_path}:\n{text}")
        sys.stdout.flush()
        # Find all possible academic year matches
        matches = re.findall(r'\b(20\d{2} - 20\d{2})\b', text)
        for match in matches:
            if match and match != '-':
                print(f"[DEBUG] Extracted academic year from OCR: {match}")
                sys.stdout.flush()
                return match
        print(f"[WARN] No valid academic year found in OCR text for {image_path}")
        sys.stdout.flush()
        return None
    except Exception as e:
        print(f"[ERROR] OCR failed for {image_path}: {e}")
        sys.stdout.flush()
        return None


def extract_academic_year_from_table(page, program_id, screenshot_path=None):
    try:
        page.wait_for_selector('table', timeout=30000)
        rows = page.query_selector_all('table tr')
        print(f"[DEBUG] Found {len(rows)} rows in accreditation table for {program_id}")
        sys.stdout.flush()
        if len(rows) > 1:
            for i in range(1, len(rows)):
                cells = rows[i].query_selector_all('td')
                if cells:
                    year = cells[0].inner_text().strip()
                    if year and year != '-':
                        print(f"[DEBUG] Extracted academic year: {year}")
                        sys.stdout.flush()
                        return year
                    else:
                        print(f"[DEBUG] Skipping invalid year '{year}' in row {i} for {program_id}")
                        sys.stdout.flush()
            print(f"[ERROR] No valid academic year found for {program_id}")
            sys.stdout.flush()
            # On failure, first take screenshot and try OCR
            screenshot_path = f"debug_acgme_{program_id}.png"
            try:
                page.screenshot(path=screenshot_path, full_page=True)
                print(f"[DEBUG] Saved screenshot to {screenshot_path}")
                sys.stdout.flush()
            except Exception as ss_e:
                print(f"[ERROR] Could not save screenshot for {program_id}: {ss_e}")
                sys.stdout.flush()
                screenshot_path = None
            if screenshot_path and os.path.exists(screenshot_path):
                ocr_year = extract_year_from_image(screenshot_path)
                if ocr_year:
                    return ocr_year
            # If OCR fails, return None (other fallbacks are handled in get_first_academic_year)
            return None
        else:
            print(f"[ERROR] No data rows found in table for {program_id}")
            sys.stdout.flush()
            # On failure, first take screenshot and try OCR
            screenshot_path = f"debug_acgme_{program_id}.png"
            try:
                page.screenshot(path=screenshot_path, full_page=True)
                print(f"[DEBUG] Saved screenshot to {screenshot_path}")
                sys.stdout.flush()
            except Exception as ss_e:
                print(f"[ERROR] Could not save screenshot for {program_id}: {ss_e}")
                sys.stdout.flush()
                screenshot_path = None
            if screenshot_path and os.path.exists(screenshot_path):
                ocr_year = extract_year_from_image(screenshot_path)
                if ocr_year:
                    return ocr_year
            return None
    except Exception as e:
        print(f"[ERROR] Exception in extract_academic_year_from_table for {program_id}: {e}")
        sys.stdout.flush()
        # On failure, first take screenshot and try OCR
        screenshot_path = f"debug_acgme_{program_id}.png"
        try:
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"[DEBUG] Saved screenshot to {screenshot_path}")
            sys.stdout.flush()
        except Exception as ss_e:
            print(f"[ERROR] Could not save screenshot for {program_id}: {ss_e}")
            sys.stdout.flush()
            screenshot_path = None
        if screenshot_path and os.path.exists(screenshot_path):
            ocr_year = extract_year_from_image(screenshot_path)
            if ocr_year:
                return ocr_year
        return None


def get_first_academic_year(page, program_id):
    print(f"[DEBUG] Navigating to {ACGME_URL} for program_id={program_id}")
    sys.stdout.flush()
    page.goto(ACGME_URL)
    page.fill('input[type="text"]', str(program_id))
    page.press('input[type="text"]', 'Enter')
    page.wait_for_timeout(3500)
    body_text = page.inner_text('body')
    print(f"[DEBUG] Body text after search: {body_text[:200]}")
    sys.stdout.flush()
    if "No Programs found" in body_text:
        print(f"[DEBUG] No results for {program_id}")
        sys.stdout.flush()
        return None
    screenshot_path = None
    try:
        locator = page.locator('text="View Accreditation History"').first
        locator.wait_for(state="attached", timeout=5000)
        locator.scroll_into_view_if_needed(timeout=2000)
        try:
            with page.expect_navigation(timeout=30000):
                human_like_click(page, locator)
            print(f"[DEBUG] Clicked 'View Accreditation History' for {program_id} (by text locator, human-like)")
            sys.stdout.flush()
        except Exception as click_e:
            print(f"[WARN] Click by text locator failed for {program_id}: {click_e}")
            sys.stdout.flush()
            # Check if already navigated to Accreditation History page
            if "/AccreditationHistoryReport?programId=" in page.url:
                print(f"[DEBUG] Already navigated to Accreditation History page for {program_id}, continuing extraction.")
                sys.stdout.flush()
                return extract_academic_year_from_table(page, program_id, None)
            # If not navigated, take screenshot and try OCR before other fallbacks
            screenshot_path = f"debug_acgme_{program_id}.png"
            try:
                page.screenshot(path=screenshot_path, full_page=True)
                print(f"[DEBUG] Saved screenshot to {screenshot_path}")
                sys.stdout.flush()
            except Exception as ss_e:
                print(f"[ERROR] Could not save screenshot for {program_id}: {ss_e}")
                sys.stdout.flush()
                screenshot_path = None
            if screenshot_path and os.path.exists(screenshot_path):
                ocr_year = extract_year_from_image(screenshot_path)
                if ocr_year:
                    return ocr_year
            # Fallback 2: Try by button class and text
            try:
                btn_locator = page.locator('a.btn.btn-primary:has-text("View Accreditation History")').first
                btn_locator.wait_for(state="attached", timeout=5000)
                btn_locator.scroll_into_view_if_needed(timeout=2000)
                with page.expect_navigation(timeout=30000):
                    human_like_click(page, btn_locator)
                print(f"[DEBUG] Clicked 'View Accreditation History' for {program_id} (by class+text, human-like)")
                sys.stdout.flush()
            except Exception as btn_e:
                print(f"[WARN] Click by class+text failed for {program_id}: {btn_e}")
                sys.stdout.flush()
                # Check if already navigated to Accreditation History page
                if "/AccreditationHistoryReport?programId=" in page.url:
                    print(f"[DEBUG] Already navigated to Accreditation History page for {program_id}, continuing extraction.")
                    sys.stdout.flush()
                    return extract_academic_year_from_table(page, program_id, None)
                # If not navigated, take screenshot and try OCR before other fallbacks
                screenshot_path = f"debug_acgme_{program_id}.png"
                try:
                    page.screenshot(path=screenshot_path, full_page=True)
                    print(f"[DEBUG] Saved screenshot to {screenshot_path}")
                    sys.stdout.flush()
                except Exception as ss_e:
                    print(f"[ERROR] Could not save screenshot for {program_id}: {ss_e}")
                    sys.stdout.flush()
                    screenshot_path = None
                if screenshot_path and os.path.exists(screenshot_path):
                    ocr_year = extract_year_from_image(screenshot_path)
                    if ocr_year:
                        return ocr_year
                # Fallback 3: Parse all <a> tags and click the one with correct href/text
                try:
                    anchors = page.query_selector_all('a')
                    found = False
                    for a in anchors:
                        a_text = a.inner_text().strip() if a else ''
                        a_href = a.get_attribute('href') if a else ''
                        if (a_text == 'View Accreditation History' or (a_href and 'AccreditationHistoryReport' in a_href)):
                            print(f"[DEBUG] Fallback: found <a> with text/href for {program_id}, trying human-like click...")
                            sys.stdout.flush()
                            a.scroll_into_view_if_needed()
                            with page.expect_navigation(timeout=30000):
                                human_like_click(page, a)
                            found = True
                            print(f"[DEBUG] Clicked 'View Accreditation History' for {program_id} (by <a> parse, human-like)")
                            sys.stdout.flush()
                            break
                    if not found:
                        print(f"[WARN] No <a> tag found for fallback click for {program_id}")
                        sys.stdout.flush()
                        # Fallback 4: Try to navigate directly to the href if found
                        if locator:
                            href = locator.get_attribute('href')
                            if href:
                                direct_url = f"https://apps.acgme.org{href}" if href.startswith('/') else href
                                print(f"[DEBUG] Fallback: navigating directly to {direct_url}")
                                sys.stdout.flush()
                                page.goto(direct_url, timeout=30000)
                            else:
                                print(f"[ERROR] No href found for fallback navigation for {program_id}")
                                sys.stdout.flush()
                                return None
                        else:
                            print(f"[ERROR] No locator for fallback navigation for {program_id}")
                            sys.stdout.flush()
                            return None
                except Exception as a_e:
                    print(f"[ERROR] Fallback <a> parse/click failed for {program_id}: {a_e}")
                    sys.stdout.flush()
                    # Check if already navigated to Accreditation History page
                    if "/AccreditationHistoryReport?programId=" in page.url:
                        print(f"[DEBUG] Already navigated to Accreditation History page for {program_id}, continuing extraction.")
                        sys.stdout.flush()
                        return extract_academic_year_from_table(page, program_id, None)
                    # If not navigated, take screenshot and try OCR before giving up
                    screenshot_path = f"debug_acgme_{program_id}.png"
                    try:
                        page.screenshot(path=screenshot_path, full_page=True)
                        print(f"[DEBUG] Saved screenshot to {screenshot_path}")
                        sys.stdout.flush()
                    except Exception as ss_e:
                        print(f"[ERROR] Could not save screenshot for {program_id}: {ss_e}")
                        sys.stdout.flush()
                        screenshot_path = None
                    if screenshot_path and os.path.exists(screenshot_path):
                        ocr_year = extract_year_from_image(screenshot_path)
                        if ocr_year:
                            return ocr_year
                    return None
        # Only take screenshot if extraction fails or is ambiguous
        year = extract_academic_year_from_table(page, program_id, None)
        if year is not None:
            return year
        # Extraction failed, take screenshot for debugging
        screenshot_path = f"debug_acgme_{program_id}.png"
        try:
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"[DEBUG] Saved screenshot to {screenshot_path}")
            sys.stdout.flush()
        except Exception as ss_e:
            print(f"[ERROR] Could not save screenshot for {program_id}: {ss_e}")
            sys.stdout.flush()
            # Try again with screenshot for OCR fallback
            return extract_academic_year_from_table(page, program_id, screenshot_path)
    except Exception as e:
        print(f"[ERROR] Exception for {program_id}: {e}")
        sys.stdout.flush()
        try:
            debug_path = f"debug_acgme_{program_id}.html"
            content = page.content()
            if content and content.strip():
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"[DEBUG] Saved debug HTML to {debug_path}")
            else:
                print(f"[WARN] Could not save debug HTML for {program_id}: Page content is empty or unavailable.")
            sys.stdout.flush()
        except Exception as inner_e:
            print(f"[ERROR] Could not save debug HTML for {program_id}: {inner_e}")
            sys.stdout.flush()
        # OCR fallback if screenshot exists
        screenshot_path = f"debug_acgme_{program_id}.png"
        if os.path.exists(screenshot_path):
            ocr_year = extract_year_from_image(screenshot_path)
            if ocr_year:
                return ocr_year
        return None


def get_first_academic_year_with_retry(page, program_id, max_retries=3):
    for attempt in range(1, max_retries + 1):
        print(f"[DEBUG] Attempt {attempt} for program_id={program_id}")
        year = get_first_academic_year(page, program_id)
        if year:
            return year
        if attempt < max_retries:
            print(f"[DEBUG] Retrying program_id={program_id} after failure...")
            time.sleep(2)
    print(f"[ERROR] All {max_retries} attempts failed for program_id={program_id}")
    return None


def main():
    parser = argparse.ArgumentParser(
        description='Scrape ACGME academic years for programs. Supports retrying failed records and OCR fallback.'
    )
    parser.add_argument('--failed-only', action='store_true', help='Only process records with missing academic year in output CSV (freida_programs_output_with_academic_year.csv).')
    parser.add_argument('--failed-record', type=str, help='Comma-separated list of program_ids to retry from output CSV (e.g., --failed-record 1405621446,1400500932). Overrides --failed-only if set.')
    args = parser.parse_args()

    print(f"[DEBUG] Starting script. Current working dir: {os.getcwd()}")
    # If --failed-record is set, only process those program_ids from the failed CSV
    if args.failed_record:
        if not os.path.exists(FAILED_CSV_FILE):
            print(f"[ERROR] Failed CSV file '{FAILED_CSV_FILE}' not found for --failed-record.")
            sys.exit(1)
        df = pd.read_csv(FAILED_CSV_FILE)
        print(f"[DEBUG] Read {len(df)} rows from {FAILED_CSV_FILE}")
        id_list = [x.strip() for x in args.failed_record.split(',') if x.strip()]
        failed_df = df[df['program_id'].astype(str).isin(id_list)]
        print(f"[DEBUG] Found {len(failed_df)} records to retry by --failed-record: {id_list}")
        if len(failed_df) == 0:
            print("[DEBUG] No matching records to process. Exiting.")
            return
        process_df = failed_df.copy()
        output_file = FAILED_CSV_FILE
    elif args.failed_only and os.path.exists(FAILED_CSV_FILE):
        df = pd.read_csv(FAILED_CSV_FILE)
        print(f"[DEBUG] Read {len(df)} rows from {FAILED_CSV_FILE}")
        process_df = df.copy()
        output_file = FAILED_CSV_FILE
    else:
        # Always sample from the latest set of records missing an academic year
        df = pd.read_csv(NEW_CSV_FILE) if os.path.exists(NEW_CSV_FILE) else pd.read_csv(CSV_FILE)
        print(f"[DEBUG] Read {len(df)} rows from {'freida_programs_output_with_academic_year.csv' if os.path.exists(NEW_CSV_FILE) else 'freida_programs_output.csv'}")
        process_df = df[df['acgme_first_academic_year'].isnull() | (df['acgme_first_academic_year'].astype(str).str.strip() == '')].copy()
        output_file = NEW_CSV_FILE

    academic_years = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Use non-headless for human-like
        context = browser.new_context()
        page = context.new_page()
        # If --failed-record, process all specified; else, pick 5 random for testing, or all if failed-only
        if args.failed_record:
            iter_df = process_df
        elif args.failed_only:
            iter_df = process_df
        else:
            random_indices = random.sample(range(len(process_df)), min(5, len(process_df))) if len(process_df) > 0 else []
            iter_df = process_df.iloc[random_indices] if len(random_indices) > 0 else process_df.iloc[[]]
        for idx, row in iter_df.iterrows():
            program_id = row['program_id']
            print(f"[DEBUG] Processing {program_id} (test {idx+1}/{len(iter_df)})...")
            sys.stdout.flush()
            try:
                year = get_first_academic_year_with_retry(page, program_id, max_retries=3)
            except Exception as e:
                print(f"[ERROR] Exception in get_first_academic_year_with_retry: {e}")
                sys.stdout.flush()
                year = None
            academic_years.append(year)
            time.sleep(1.5)
        browser.close()
    print(f"[DEBUG] Academic years collected: {academic_years}")
    sys.stdout.flush()
    iter_df = iter_df.copy()
    if 'acgme_first_academic_year' in iter_df.columns:
        iter_df = iter_df.drop(columns=['acgme_first_academic_year'])
    iter_df.insert(0, 'acgme_first_academic_year', academic_years)
    # After updating the output file, always update the main, success, and failed CSVs for consistency
    if output_file == FAILED_CSV_FILE:
        # Update the main output file with any new successes
        if os.path.exists(NEW_CSV_FILE):
            main_df = pd.read_csv(NEW_CSV_FILE)
            # Update main_df with any successes from this run
            for idx, row in iter_df.iterrows():
                pid = row['program_id']
                year = row['acgme_first_academic_year'] if 'acgme_first_academic_year' in row else None
                if year and str(year).strip():
                    main_df.loc[main_df['program_id'] == pid, 'acgme_first_academic_year'] = year
            main_df.to_csv(NEW_CSV_FILE, index=False)
            df_full = main_df
        else:
            df_full = iter_df
    else:
        # Always update the full DataFrame, never just the batch
        full_df = pd.read_csv(output_file)
        for idx, row in iter_df.iterrows():
            pid = row['program_id']
            year = row['acgme_first_academic_year'] if 'acgme_first_academic_year' in row else None
            if year and str(year).strip():
                full_df.loc[full_df['program_id'] == pid, 'acgme_first_academic_year'] = year
        full_df.to_csv(output_file, index=False)
        df_full = full_df
    success_df = df_full[df_full['acgme_first_academic_year'].notnull() & (df_full['acgme_first_academic_year'].astype(str).str.strip() != '')]
    failed_df = df_full[df_full['acgme_first_academic_year'].isnull() | (df_full['acgme_first_academic_year'].astype(str).str.strip() == '')]
    success_df.to_csv(SUCCESS_CSV_FILE, index=False)
    failed_df.to_csv(FAILED_CSV_FILE, index=False)
    print(f"[DEBUG] Wrote {len(success_df)} good records to {SUCCESS_CSV_FILE} and {len(failed_df)} failed records to {FAILED_CSV_FILE}")
    sys.stdout.flush()
    print("[DEBUG] Script finished.")
    sys.stdout.flush()

if __name__ == "__main__":
    main() 
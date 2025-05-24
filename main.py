from scraper import extract_program_detail
from playwright.sync_api import sync_playwright
import pandas as pd
import logging
import time
import sys

DEBUG_MODE = '--debug' in sys.argv
EXIT_ON_ERRORS = '--exit-on-errors' in sys.argv

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    input_csv = "freida_program_ids.csv"
    output_csv = "freida_programs_output.csv"
    partial_csv = "freida_partial_row2.csv"
    checkpoint_interval = 25

    all_results = []
    ids_df = pd.read_csv(input_csv)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        for idx, row in ids_df.iterrows():
            program_id = str(row['program_id'])
            logging.debug(f"Processing row {idx + 1}/{len(ids_df)}: Program ID {program_id}")
            result = extract_program_detail(page, program_id)
            all_results.append(result)

            if (idx + 1) % checkpoint_interval == 0 or idx == 1:
                partial_df = pd.DataFrame(all_results)
                filename = f"freida_partial_{idx + 1}.csv" if (idx + 1) % checkpoint_interval == 0 else partial_csv
                partial_df.to_csv(filename, index=False)
                logging.info(f"Saved checkpoint to {filename}")

            time.sleep(2.0)

        context.close()
        browser.close()

    df = pd.DataFrame(all_results)
    df.to_csv(output_csv, index=False)
    logging.info(f"✅ Completed scrape. Data saved to {output_csv}")

if __name__ == "__main__":
    main()


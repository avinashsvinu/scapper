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
            logging.debug(
                f"Processing row {idx + 1}/{len(ids_df)}: Program ID {program_id}")
            result = extract_program_detail(page, program_id)
            all_results.append(result)

            if (idx + 1) % checkpoint_interval == 0 or idx == 1:
                partial_df = pd.DataFrame(all_results)
                # Ensure columns are always in the same order as
                # EXPECTED_FIELDS
                EXPECTED_FIELDS = [
                    'program_id',
                    'source_url',
                    'program_name_suffix',
                    'city',
                    'state',
                    'data_last_updated',
                    'accredited_training_length',
                    'required_training_length',
                    'affiliated_us_government',
                    'raw_ng_state_json',
                    'specialty_title',
                    'first_year_positions',
                    'interviews_conducted_last_year',
                    'avg_hours_on_duty_y1',
                    'pct_do',
                    'pct_img',
                    'pct_usmd',
                    'program_best_described_as',
                    'website',
                    'special_features_text',
                    'accepting_applications_2025_2026',
                    'accepting_applications_2026_2027',
                    'program_start_dates',
                    'participates_in_eras',
                    'visa_statuses_accepted',
                    'program_director_first_name',
                    'program_director_middle_name',
                    'program_director_last_name',
                    'program_director_suffix',
                    'program_director_degrees',
                    'program_director_organization',
                    'program_director_address_line1',
                    'program_director_address_line2',
                    'program_director_locality',
                    'program_director_administrative_area',
                    'program_director_postal_code',
                    'program_director_email',
                    'program_director_phone',
                    'contact_first_name',
                    'contact_middle_name',
                    'contact_last_name',
                    'contact_suffix',
                    'contact_degrees',
                    'contact_organization',
                    'contact_address_line1',
                    'contact_address_line2',
                    'contact_locality',
                    'contact_administrative_area',
                    'contact_postal_code',
                    'contact_email',
                    'contact_phone']
                for field in EXPECTED_FIELDS:
                    if field not in partial_df.columns:
                        partial_df[field] = None
                partial_df = partial_df[EXPECTED_FIELDS]
                filename = f"freida_partial_{idx + 1}.csv" if (
                    idx + 1) % checkpoint_interval == 0 else partial_csv
                partial_df.to_csv(filename, index=False)
                logging.info(f"Saved checkpoint to {filename}")

            time.sleep(2.0)

        context.close()
        browser.close()

    df = pd.DataFrame(all_results)
    EXPECTED_FIELDS = [
        'program_id',
        'source_url',
        'program_name_suffix',
        'city',
        'state',
        'data_last_updated',
        'accredited_training_length',
        'required_training_length',
        'affiliated_us_government',
        'raw_ng_state_json',
        'specialty_title',
        'first_year_positions',
        'interviews_conducted_last_year',
        'avg_hours_on_duty_y1',
        'pct_do',
        'pct_img',
        'pct_usmd',
        'program_best_described_as',
        'website',
        'special_features_text',
        'accepting_applications_2025_2026',
        'accepting_applications_2026_2027',
        'program_start_dates',
        'participates_in_eras',
        'visa_statuses_accepted',
        'program_director_first_name',
        'program_director_middle_name',
        'program_director_last_name',
        'program_director_suffix',
        'program_director_degrees',
        'program_director_organization',
        'program_director_address_line1',
        'program_director_address_line2',
        'program_director_locality',
        'program_director_administrative_area',
        'program_director_postal_code',
        'program_director_email',
        'program_director_phone',
        'contact_first_name',
        'contact_middle_name',
        'contact_last_name',
        'contact_suffix',
        'contact_degrees',
        'contact_organization',
        'contact_address_line1',
        'contact_address_line2',
        'contact_locality',
        'contact_administrative_area',
        'contact_postal_code',
        'contact_email',
        'contact_phone']
    for field in EXPECTED_FIELDS:
        if field not in df.columns:
            df[field] = None
    df = df[EXPECTED_FIELDS]
    df.to_csv(output_csv, index=False)
    logging.info(f"✅ Completed scrape. Data saved to {output_csv}")


if __name__ == "__main__":
    main()

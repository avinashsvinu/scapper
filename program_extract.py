# Scraper for FREIDA programs list using Playwright (supports JavaScript-rendered content)

import time
import pandas as pd
from playwright.sync_api import sync_playwright
import logging
import re
import sys
import json
from bs4 import BeautifulSoup

# Set default logging level
DEBUG_MODE = '--debug' in sys.argv
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

PROGRAM_DETAIL_URL_TEMPLATE = "https://freida.ama-assn.org/program/{}"


def find_included_node(type_name, node_id, included_list):
    if not type_name or not node_id:
        return None
    for node in included_list:
        if isinstance(node, dict) and node.get('type') == type_name and node.get('id') == node_id:
            return node
    return None


def extract_program_detail(page, program_id):
    url = PROGRAM_DETAIL_URL_TEMPLATE.format(program_id)
    logging.info(f"Visiting detail page: {url}")
    try:
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_selector("div.survey-info", timeout=15000)
        html_content = page.content()
        soup = BeautifulSoup(html_content, 'html.parser')
        script_tag = soup.find('script', {'id': 'ng-state', 'type': 'application/json'})
        if not script_tag or not script_tag.string:
            return {"program_id": program_id, "source_url": url, "error": "Missing ng-state JSON"}

        full_json_data = json.loads(script_tag.string)
        raw_json = json.dumps(full_json_data)
        full_json_payload = None

        for key, value in full_json_data.items():
            if isinstance(value, dict) and 'b' in value and isinstance(value['b'], dict) and 'data' in value['b']:
                full_json_payload = value
                break

        if not full_json_payload:
            return {"program_id": program_id, "source_url": url, "error": "Missing main JSON payload"}

        api_data = full_json_payload.get('b', {})
        program_nodes = api_data.get('data', [])
        if not program_nodes or not isinstance(program_nodes, list):
            return {"program_id": program_id, "source_url": url, "error": "Missing program data"}

        program_node = program_nodes[0]
        included_nodes = api_data.get('included', [])

        prog_attrs = program_node.get('attributes', {})
        prog_rels = program_node.get('relationships', {})

        extracted_data = {
            'program_id': prog_attrs.get('field_program_id'),
            'source_url': url,
            'program_name_suffix': prog_attrs.get('title'),
            'city': prog_attrs.get('field_address', {}).get('locality'),
            'state': prog_attrs.get('field_address', {}).get('administrative_area'),
            'data_last_updated': prog_attrs.get('changed'),
            'accredited_training_length': prog_attrs.get('field_accredited_length'),
            'required_training_length': prog_attrs.get('field_required_length'),
            'affiliated_us_government': prog_attrs.get('field_affiliated_us_gov'),
            'raw_ng_state_json': raw_json if DEBUG_MODE else None
        }

        specialty_ref = prog_rels.get('field_specialty', {}).get('data', {})
        specialty_node = find_included_node(specialty_ref.get('type'), specialty_ref.get('id'), included_nodes) if isinstance(specialty_ref, dict) else None
        extracted_data['specialty_title'] = specialty_node.get('attributes', {}).get('title') if specialty_node else None

        survey_node = None
        survey_ref_data_list = prog_rels.get('field_survey', {}).get('data', [])
        if survey_ref_data_list and isinstance(survey_ref_data_list, list):
            survey_ref_data = survey_ref_data_list[0]
            survey_node = find_included_node(survey_ref_data.get('type'), survey_ref_data.get('id'), included_nodes) if isinstance(survey_ref_data, dict) else None

        if survey_node:
            survey_attrs = survey_node.get('attributes', {})
            survey_rels = survey_node.get('relationships', {})
            extracted_data.update({
                'first_year_positions': survey_attrs.get('field_first_year_positions'),
                'interviews_conducted_last_year': survey_attrs.get('field_interviews_conducted'),
                'avg_hours_on_duty_y1': survey_attrs.get('field_avg_hours_on_duty_y1'),
                'pct_do': survey_attrs.get('field_pct_do'),
                'pct_img': survey_attrs.get('field_pct_img'),
                'pct_usmd': survey_attrs.get('field_pct_usmd'),
                'program_best_described_as': survey_attrs.get('field_program_best_described_as'),
                'website': survey_attrs.get('field_website'),
                'special_features_text': survey_attrs.get('field_special_features', {}).get('value') if isinstance(survey_attrs.get('field_special_features'), dict) else None,
                'accepting_applications_2025_2026': survey_attrs.get('field_accepting_current_year'),
                'accepting_applications_2026_2027': survey_attrs.get('field_accepting_next_year'),
                'program_start_dates': survey_attrs.get('field_program_start_dates'),
                'participates_in_eras': survey_attrs.get('field_participates_in_eras'),
                'visa_statuses_accepted': survey_attrs.get('field_visa_status')
            })

        return extracted_data

    except Exception as e:
        logging.warning(f"Error loading program ID {program_id}: {e}")
        return {"program_id": program_id, "source_url": url, "error": str(e)}


def visit_all_program_ids():
    ids_df = pd.read_csv("freida_program_ids.csv")
    all_programs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        for idx, row in ids_df.iterrows():
            logging.debug(f"Processing row {idx+1}/{len(ids_df)}: Program ID {row['program_id']}")
            result = extract_program_detail(page, row["program_id"])
            all_programs.append(result)

            if (idx + 1) % 25 == 0 or (idx+1) == 1:
                df_partial = pd.DataFrame(all_programs)
                partial_file = f"freida_partial_{idx + 1}.csv"
                df_partial.to_csv(partial_file, index=False)
                logging.info(f"📄 Saved checkpoint to {partial_file}")

            time.sleep(1.0)

        browser.close()

    return all_programs


if __name__ == "__main__":
    try:
        data = visit_all_program_ids()
        if data:
            df = pd.DataFrame(data)
            df.to_csv("freida_program_full_details.csv", index=False)
            logging.info("✅ Scrape complete. Saved to freida_program_full_details.csv")
        else:
            logging.warning("⚠️ No data scraped.")
    except Exception as e:
        logging.critical(f"Unexpected error: {e}")


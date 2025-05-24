# scraper.py
import json
from bs4 import BeautifulSoup
import logging
from utils import find_included_node, extract_contact_details

DEBUG_MODE = '--debug' in __import__('sys').argv
EXIT_ON_ERRORS = '--exit-on-errors' in __import__('sys').argv

PROGRAM_DETAIL_URL_TEMPLATE = "https://freida.ama-assn.org/program/{}"

def extract_program_detail(page, program_id):
    url = PROGRAM_DETAIL_URL_TEMPLATE.format(program_id)
    logging.info(f"Visiting detail page: {url}")
    try:
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_selector("div.survey-info", timeout=15000)
        html_content = page.content()
        soup = BeautifulSoup(html_content, 'html.parser')

        if DEBUG_MODE:
            screenshot_file = f"debug_snapshot_{program_id}.png"
            page.screenshot(path=screenshot_file, full_page=True)
            logging.debug(f"📸 Saved screenshot to {screenshot_file}")

        script_tag = soup.find('script', {'id': 'ng-state', 'type': 'application/json'})
        if not script_tag or not script_tag.string:
            raise ValueError("Missing ng-state JSON")

        full_json_data = json.loads(script_tag.string)
        raw_json = json.dumps(full_json_data)

        full_json_payload = next(
            (value for key, value in full_json_data.items()
             if isinstance(value, dict) and 'b' in value and isinstance(value['b'], dict) and 'data' in value['b']
             and isinstance(value['b']['data'], list) and any(n.get("type") == "node--program" for n in value['b']['data'])),
            None
        )

        if not full_json_payload:
            raise ValueError("Missing or invalid program payload structure")

        api_data = full_json_payload['b']
        program_nodes = api_data.get('data', [])
        included_nodes = api_data.get('included', [])

        program_node = next((node for node in program_nodes if node.get("type") == "node--program"), None)
        if not program_node:
            raise ValueError("No node--program found in JSON")

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

        survey_node = next((n for n in included_nodes if n.get("type", "").startswith("paragraph--survey_data")), None)
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
                'special_features_text': survey_attrs.get('field_special_features', {}).get('value')
                    if isinstance(survey_attrs.get('field_special_features'), dict) else None,
                'accepting_applications_2025_2026': survey_attrs.get('field_accepting_current_year'),
                'accepting_applications_2026_2027': survey_attrs.get('field_accepting_next_year'),
                'program_start_dates': survey_attrs.get('field_program_start_dates'),
                'participates_in_eras': survey_attrs.get('field_participates_in_eras'),
                'visa_statuses_accepted': survey_attrs.get('field_visa_status')
            })

            extract_contact_details('field_program_director', survey_rels, included_nodes, extracted_data)
            extract_contact_details('field_program_contact', survey_rels, included_nodes, extracted_data)

        return extracted_data

    except Exception as e:
        logging.warning(f"Error loading program ID {program_id}: {e}")
        if EXIT_ON_ERRORS:
            raise
        return {"program_id": program_id, "source_url": url, "error": str(e)}


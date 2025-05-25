import json
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional

def find_included_node(type_name: Optional[str], node_id: Optional[str], included_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Searches the 'included' list for a node matching the given type and id.
    """
    if not type_name or not node_id:
        return None
    for node in included_list:
        if node.get('type') == type_name and node.get('id') == node_id:
            return node
    return None

def parse_freida_program_page(html_content: str) -> Dict[str, Any]:
    """
    Parses the HTML content of an individual FREIDA program page to extract detailed program information.
    """
    extracted_data: Dict[str, Any] = {}

    try:
        soup = BeautifulSoup(html_content, 'html.parser')
    except Exception as e:
        return {"error": f"BeautifulSoup parsing failed: {str(e)}"}

    script_tag = soup.find('script', {'id': 'ng-state', 'type': 'application/json'})
    if not script_tag:
        return {"error": "Could not find the <script id=\"ng-state\"> tag."}

    json_text = script_tag.string
    if not json_text:
        return {"error": "The <script id=\"ng-state\"> tag is empty."}

    try:
        full_json_data = json.loads(json_text)
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse JSON from script tag: {str(e)}"}

    # Find the main data payload key (heuristic: it's usually the only top-level key that's a string of digits)
    full_json_payload = None
    for key, value in full_json_data.items():
        if key.isdigit() and isinstance(value, dict) and 'b' in value and 'data' in value['b']:
            full_json_payload = value
            break
        # Fallback: check for a structure that looks like the expected data
        elif isinstance(value, dict) and 'b' in value and 'data' in value.get('b', {}) and isinstance(value['b']['data'], list):
             # Check if it has some expected nested keys
            if value['b']['data'] and 'attributes' in value['b']['data'][0] and 'relationships' in value['b']['data'][0]:
                full_json_payload = value
                break
    
    if not full_json_payload:
        # More robust fallback: iterate through keys and pick the one with the most substantial 'b' > 'data' structure
        max_len = -1
        for key, value in full_json_data.items():
            if isinstance(value, dict) and 'b' in value and 'data' in value['b'] and isinstance(value['b']['data'], list):
                current_len = len(str(value['b']['data'])) # A rough measure of "substantiality"
                if current_len > max_len:
                    max_len = current_len
                    full_json_payload = value
        if not full_json_payload:
             return {"error": "Could not find the main JSON payload object. The structure might have changed."}


    api_data = full_json_payload.get('b', {})
    program_nodes = api_data.get('data', [])
    if not program_nodes or not isinstance(program_nodes, list):
        return {"error": "api_data['data'] is missing or not a list."}
    
    program_node = program_nodes[0]
    included_nodes = api_data.get('included', [])

    prog_attrs = program_node.get('attributes', {})
    prog_rels = program_node.get('relationships', {})

    extracted_data['program_name_suffix'] = prog_attrs.get('title')
    extracted_data['program_id'] = prog_attrs.get('field_program_id')
    field_address = prog_attrs.get('field_address', {})
    extracted_data['city'] = field_address.get('locality')
    extracted_data['state'] = field_address.get('administrative_area')
    extracted_data['data_last_updated'] = prog_attrs.get('changed')
    extracted_data['is_expanded_listing'] = prog_attrs.get('field_expanded_listing')
    extracted_data['accredited_training_length'] = prog_attrs.get('field_accredited_length')
    extracted_data['required_training_length'] = prog_attrs.get('field_required_length')
    extracted_data['affiliated_us_government'] = prog_attrs.get('field_affiliated_us_gov') # From prog_attrs

    # Specialty
    specialty_ref = prog_rels.get('field_specialty', {}).get('data', {})
    if specialty_ref and isinstance(specialty_ref, dict): # Ensure specialty_ref is a dict
        specialty_node = find_included_node(specialty_ref.get('type'), specialty_ref.get('id'), included_nodes)
        if specialty_node:
            extracted_data['specialty_title'] = specialty_node.get('attributes', {}).get('title')
        else:
            extracted_data['specialty_title'] = None
    else:
        extracted_data['specialty_title'] = None


    # Survey Data
    survey_ref_data_list = prog_rels.get('field_survey', {}).get('data', [])
    survey_node = None
    if survey_ref_data_list and isinstance(survey_ref_data_list, list):
        survey_ref_data = survey_ref_data_list[0]
        if survey_ref_data and isinstance(survey_ref_data, dict): # Ensure survey_ref_data is a dict
            survey_node = find_included_node(survey_ref_data.get('type'), survey_ref_data.get('id'), included_nodes)

    if survey_node:
        survey_attrs = survey_node.get('attributes', {})
        survey_rels = survey_node.get('relationships', {})

        extracted_data['first_year_positions'] = survey_attrs.get('field_first_year_positions')
        extracted_data['interviews_conducted_last_year'] = survey_attrs.get('field_interviews_conducted')
        extracted_data['avg_hours_on_duty_y1'] = survey_attrs.get('field_avg_hours_on_duty_y1')
        extracted_data['pct_do'] = survey_attrs.get('field_pct_do')
        extracted_data['pct_img'] = survey_attrs.get('field_pct_img')
        extracted_data['pct_usmd'] = survey_attrs.get('field_pct_usmd')
        extracted_data['program_best_described_as'] = survey_attrs.get('field_program_best_described_as')
        extracted_data['website'] = survey_attrs.get('field_website')
        extracted_data['survey_received_date'] = survey_attrs.get('field_date_received')
        special_features = survey_attrs.get('field_special_features', {})
        extracted_data['special_features_text'] = special_features.get('value') if isinstance(special_features, dict) else None
        extracted_data['accepting_applications_2025_2026'] = survey_attrs.get('field_accepting_current_year')
        extracted_data['accepting_applications_2026_2027'] = survey_attrs.get('field_accepting_next_year')
        extracted_data['program_start_dates'] = survey_attrs.get('field_program_start_dates') # List
        extracted_data['participates_in_eras'] = survey_attrs.get('field_participates_in_eras')
        extracted_data['visa_statuses_accepted'] = survey_attrs.get('field_visa_status') # List

        # Primary Teaching Site
        primary_site_ref = survey_rels.get('field_primary_teaching_site', {}).get('data', {})
        if primary_site_ref and isinstance(primary_site_ref, dict): # Ensure ref is a dict
            site_node = find_included_node(primary_site_ref.get('type'), primary_site_ref.get('id'), included_nodes)
            if site_node:
                extracted_data['primary_teaching_site_name'] = site_node.get('attributes', {}).get('title')
            else:
                extracted_data['primary_teaching_site_name'] = None
        else:
            extracted_data['primary_teaching_site_name'] = None


        # Program Director
        director_ref = survey_rels.get('field_program_director', {}).get('data', {})
        if director_ref and isinstance(director_ref, dict): # Ensure ref is a dict
            director_node = find_included_node(director_ref.get('type'), director_ref.get('id'), included_nodes)
            if director_node:
                dir_attrs = director_node.get('attributes', {})
                extracted_data['program_director_first_name'] = dir_attrs.get('field_first_name')
                extracted_data['program_director_last_name'] = dir_attrs.get('field_last_name')
                extracted_data['program_director_degrees'] = dir_attrs.get('field_degrees')
                dir_address_data = dir_attrs.get('field_address', {})
                if isinstance(dir_address_data, dict):
                    dir_address_parts = [
                        dir_address_data.get('organization', ''),
                        dir_address_data.get('address_line1', ''),
                        dir_address_data.get('address_line2', ''),
                        dir_address_data.get('locality', ''),
                        dir_address_data.get('administrative_area', ''),
                        dir_address_data.get('postal_code', '')
                    ]
                    extracted_data['program_director_address'] = ", ".join(filter(None, dir_address_parts)).replace(" ,", ",").replace("  ", " ").strip(", ")
                else:
                    extracted_data['program_director_address'] = None
                extracted_data['program_director_email_protected'] = dir_attrs.get('field_email')
                extracted_data['program_director_phone'] = dir_attrs.get('field_phone')
            else:
                for key in ['program_director_first_name', 'program_director_last_name', 'program_director_degrees', 'program_director_address', 'program_director_email_protected', 'program_director_phone']:
                    extracted_data[key] = None
        else:
             for key in ['program_director_first_name', 'program_director_last_name', 'program_director_degrees', 'program_director_address', 'program_director_email_protected', 'program_director_phone']:
                    extracted_data[key] = None


        # Contact Person
        contact_ref = survey_rels.get('field_program_contact', {}).get('data', {})
        if contact_ref and isinstance(contact_ref, dict): # Ensure ref is a dict
            contact_node = find_included_node(contact_ref.get('type'), contact_ref.get('id'), included_nodes)
            if contact_node:
                contact_attrs = contact_node.get('attributes', {})
                extracted_data['contact_person_first_name'] = contact_attrs.get('field_first_name')
                extracted_data['contact_person_last_name'] = contact_attrs.get('field_last_name')
                extracted_data['contact_person_degrees'] = contact_attrs.get('field_degrees')
                contact_address_data = contact_attrs.get('field_address', {})
                if isinstance(contact_address_data, dict):
                    contact_address_parts = [
                        contact_address_data.get('organization', ''),
                        contact_address_data.get('address_line1', ''),
                        contact_address_data.get('address_line2', ''),
                        contact_address_data.get('locality', ''),
                        contact_address_data.get('administrative_area', ''),
                        contact_address_data.get('postal_code', '')
                    ]
                    extracted_data['contact_person_address'] = ", ".join(filter(None, contact_address_parts)).replace(" ,", ",").replace("  ", " ").strip(", ")
                else:
                    extracted_data['contact_person_address'] = None
                extracted_data['contact_person_email_protected'] = contact_attrs.get('field_email')
                extracted_data['contact_person_phone'] = contact_attrs.get('field_phone')
            else:
                for key in ['contact_person_first_name', 'contact_person_last_name', 'contact_person_degrees', 'contact_person_address', 'contact_person_email_protected', 'contact_person_phone']:
                    extracted_data[key] = None
        else:
            for key in ['contact_person_first_name', 'contact_person_last_name', 'contact_person_degrees', 'contact_person_address', 'contact_person_email_protected', 'contact_person_phone']:
                extracted_data[key] = None
    else: # If survey_node is not found, set all survey-dependent fields to None
        survey_related_fields = [
            'first_year_positions', 'interviews_conducted_last_year', 'avg_hours_on_duty_y1',
            'pct_do', 'pct_img', 'pct_usmd', 'program_best_described_as', 'website',
            'survey_received_date', 'special_features_text', 'accepting_applications_2025_2026',
            'accepting_applications_2026_2027', 'program_start_dates', 'participates_in_eras',
            'visa_statuses_accepted', 'primary_teaching_site_name',
            'program_director_first_name', 'program_director_last_name', 'program_director_degrees',
            'program_director_address', 'program_director_email_protected', 'program_director_phone',
            'contact_person_first_name', 'contact_person_last_name', 'contact_person_degrees',
            'contact_person_address', 'contact_person_email_protected', 'contact_person_phone'
        ]
        for key in survey_related_fields:
            extracted_data[key] = None
            
    return extracted_data

if __name__ == '__main__':
    # Placeholder for HTML content for testing
    # Replace this with actual HTML content from a FREIDA program page
    sample_html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sample FREIDA Page</title>
    </head>
    <body>
        <script id="ng-state" type="application/json">
        {
            "123456789": { 
                "b": {
                    "data": [
                        {
                            "type": "node--program",
                            "id": "program-uuid-1",
                            "attributes": {
                                "title": "Internal Medicine Residency Program",
                                "field_program_id": "1403521292",
                                "field_address": {
                                    "locality": "Anytown",
                                    "administrative_area": "CA"
                                },
                                "changed": "2023-10-26T12:00:00Z",
                                "field_expanded_listing": true,
                                "field_accredited_length": "3 years",
                                "field_required_length": "3 years",
                                "field_affiliated_us_gov": false
                            },
                            "relationships": {
                                "field_specialty": {
                                    "data": {
                                        "type": "taxonomy_term--specialty",
                                        "id": "specialty-uuid-1"
                                    }
                                },
                                "field_survey": {
                                    "data": [
                                        {
                                            "type": "paragraph--survey_data",
                                            "id": "survey-uuid-1"
                                        }
                                    ]
                                }
                            }
                        }
                    ],
                    "included": [
                        {
                            "type": "taxonomy_term--specialty",
                            "id": "specialty-uuid-1",
                            "attributes": {
                                "title": "Internal Medicine"
                            }
                        },
                        {
                            "type": "paragraph--survey_data",
                            "id": "survey-uuid-1",
                            "attributes": {
                                "field_first_year_positions": 10,
                                "field_interviews_conducted": 100,
                                "field_avg_hours_on_duty_y1": "70",
                                "field_pct_do": 10.5,
                                "field_pct_img": 20.0,
                                "field_pct_usmd": 69.5,
                                "field_program_best_described_as": "Community-based",
                                "field_website": "http://example.com/program",
                                "field_date_received": "2023-09-15",
                                "field_special_features": {"value": "Strong research opportunities."},
                                "field_accepting_current_year": true,
                                "field_accepting_next_year": true,
                                "field_program_start_dates": ["July 1", "August 1"],
                                "field_participates_in_eras": true,
                                "field_visa_status": ["H1B", "J1"]
                            },
                            "relationships": {
                                "field_primary_teaching_site": {
                                    "data": {
                                        "type": "node--institution_profile",
                                        "id": "site-uuid-1"
                                    }
                                },
                                "field_program_director": {
                                    "data": {
                                        "type": "paragraph--program_contact",
                                        "id": "director-uuid-1"
                                    }
                                },
                                "field_program_contact": {
                                    "data": {
                                        "type": "paragraph--program_contact",
                                        "id": "contact-uuid-1"
                                    }
                                }
                            }
                        },
                        {
                            "type": "node--institution_profile",
                            "id": "site-uuid-1",
                            "attributes": {
                                "title": "Main Teaching Hospital"
                            }
                        },
                        {
                            "type": "paragraph--program_contact",
                            "id": "director-uuid-1",
                            "attributes": {
                                "field_first_name": "John",
                                "field_last_name": "Doe",
                                "field_degrees": "MD, PhD",
                                "field_address": {
                                    "organization": "Anytown Medical Center",
                                    "address_line1": "123 Health St",
                                    "address_line2": "Suite 100",
                                    "locality": "Anytown",
                                    "administrative_area": "CA",
                                    "postal_code": "90210"
                                },
                                "field_email": "johndoe@example.com (protected)",
                                "field_phone": "555-123-4567"
                            }
                        },
                        {
                            "type": "paragraph--program_contact",
                            "id": "contact-uuid-1",
                            "attributes": {
                                "field_first_name": "Jane",
                                "field_last_name": "Smith",
                                "field_degrees": "MHA",
                                "field_address": {
                                    "organization": "Anytown Medical Center",
                                    "address_line1": "456 Wellness Ave",
                                    "address_line2": "",
                                    "locality": "Anytown",
                                    "administrative_area": "CA",
                                    "postal_code": "90210"
                                },
                                "field_email": "janesmith@example.com (protected)",
                                "field_phone": "555-987-6543"
                            }
                        }
                    ]
                }
            }
        }
        </script>
        <h1>Program Details</h1>
        <p>Some other content on the page.</p>
    </body>
    </html>
    """
    
    # To test with a real HTML file, you would do:
    with open("/Users/avinash.sridhar/Downloads/freida/view-source_https___freida.ama-assn.org_program_1404121380.html", "r", encoding="utf-8") as f:
        sample_html_content = f.read()

    parsed_data = parse_freida_program_page(sample_html_content)

    if "error" in parsed_data:
        print(f"Error: {parsed_data['error']}")
    else:
        print("Successfully parsed data:")
        for key, value in parsed_data.items():
            print(f"  {key}: {value}")

    # Example of how to test specific error conditions:
    # print("\nTesting missing ng-state tag:")
    # print(parse_freida_program_page("<html><body>No script tag</body></html>"))
    # print("\nTesting empty ng-state tag:")
    # print(parse_freida_program_page("<html><body><script id='ng-state' type='application/json'></script></body></html>"))
    # print("\nTesting invalid JSON:")
    # print(parse_freida_program_page("<html><body><script id='ng-state' type='application/json'>{\"key\": not_json}</script></body></html>"))


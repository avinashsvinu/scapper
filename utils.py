"""
utils.py

Utility functions for extracting nodes and contact details from FREIDA JSON structures.
"""


def find_included_node(type_name, node_id, included_list):
    """
    Finds and returns a node from included_list matching the given type and id.
    """
    for node in included_list:
        if node.get('type') == type_name and node.get('id') == node_id:
            return node
    return None


def extract_contact_details(
        ref_key,
        survey_rels,
        included_nodes,
        extracted_data):
    """
    Extracts contact details for a given ref_key from survey relationships and updates extracted_data dict.
    """
    ref = survey_rels.get(ref_key, {}).get('data', {})
    if isinstance(ref, dict):
        node = find_included_node(
            ref.get('type'),
            ref.get('id'),
            included_nodes)
        if node:
            attrs = node.get('attributes', {})
            extracted_data[f'{ref_key}_first_name'] = attrs.get(
                'field_first_name')
            extracted_data[f'{ref_key}_last_name'] = attrs.get(
                'field_last_name')
            extracted_data[f'{ref_key}_degrees'] = attrs.get('field_degrees')
            address = attrs.get('field_address', {})
            if isinstance(address, dict):
                parts = [
                    address.get('organization'),
                    address.get('address_line1'),
                    address.get('address_line2'),
                    address.get('locality'),
                    address.get('administrative_area'),
                    address.get('postal_code')
                ]
                extracted_data[f'{ref_key}_address'] = ", ".join(
                    filter(None, parts)).replace(" ,", ",").strip(', ')
            else:
                extracted_data[f'{ref_key}_address'] = None
            extracted_data[f'{ref_key}_email'] = attrs.get('field_email')
            extracted_data[f'{ref_key}_phone'] = attrs.get('field_phone')
        else:
            for suffix in [
                'first_name',
                'last_name',
                'degrees',
                'address',
                'email',
                    'phone']:
                extracted_data[f'{ref_key}_{suffix}'] = None
    else:
        for suffix in [
            'first_name',
            'last_name',
            'degrees',
            'address',
            'email',
                'phone']:
            extracted_data[f'{ref_key}_{suffix}'] = None

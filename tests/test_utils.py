import pytest
import utils
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))


def test_find_included_node_found():
    included = [
        {"type": "person", "id": "1", "foo": "bar"},
        {"type": "org", "id": "2"}
    ]
    node = utils.find_included_node("person", "1", included)
    assert node["foo"] == "bar"


def test_find_included_node_not_found():
    included = [
        {"type": "person", "id": "1"}
    ]
    node = utils.find_included_node("org", "2", included)
    assert node is None


def test_extract_contact_details_full():
    survey_rels = {"contact": {"data": {"type": "person", "id": "1"}}}
    included = [
        {"type": "person", "id": "1", "attributes": {
            "field_first_name": "A",
            "field_last_name": "B",
            "field_degrees": "MD",
            "field_email": "a@b.com",
            "field_phone": "123",
            "field_address": {
                "organization": "Org",
                "address_line1": "L1",
                "address_line2": "L2",
                "locality": "Loc",
                "administrative_area": "AA",
                "postal_code": "99999"
            }
        }}
    ]
    extracted = {}
    utils.extract_contact_details("contact", survey_rels, included, extracted)
    assert extracted["contact_first_name"] == "A"
    assert extracted["contact_last_name"] == "B"
    assert extracted["contact_degrees"] == "MD"
    assert extracted["contact_email"] == "a@b.com"
    assert extracted["contact_phone"] == "123"
    assert extracted["contact_address"] == "Org, L1, L2, Loc, AA, 99999"


def test_extract_contact_details_not_found():
    survey_rels = {"contact": {"data": {"type": "person", "id": "2"}}}
    included = [
        {"type": "person", "id": "1", "attributes": {}}
    ]
    extracted = {}
    utils.extract_contact_details("contact", survey_rels, included, extracted)
    for suffix in [
            'first_name', 'last_name', 'degrees', 'address', 'email', 'phone']:
        assert extracted[f"contact_{suffix}"] is None


def test_extract_contact_details_no_data():
    survey_rels = {"contact": {"data": None}}
    included = []
    extracted = {}
    utils.extract_contact_details("contact", survey_rels, included, extracted)
    for suffix in [
            'first_name', 'last_name', 'degrees', 'address', 'email', 'phone']:
        assert extracted[f"contact_{suffix}"] is None

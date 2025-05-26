import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import pytest
import scraper
from unittest.mock import MagicMock
import json

def test_extract_program_detail_minimal(monkeypatch):
    # Mock Playwright page
    page = MagicMock()
    # Minimal HTML with ng-state JSON
    minimal_json = {
        "key": {
            "b": {
                "data": [
                    {
                        "type": "node--program",
                        "attributes": {
                            "field_program_id": "99999",
                            "title": "Test Program",
                            "field_address": {"locality": "Test City", "administrative_area": "TS"},
                            "changed": "2024-01-01",
                            "field_accredited_length": 3,
                            "field_required_length": 3,
                            "field_affiliated_us_gov": False
                        },
                        "relationships": {}
                    }
                ],
                "included": []
            }
        }
    }
    html = '<html><body><script id="ng-state" type="application/json">' + \
        json.dumps(minimal_json) + '</script></body></html>'
    page.content.return_value = html
    page.goto.return_value = None
    page.wait_for_selector.return_value = None
    # Patch find_included_node to always return None
    monkeypatch.setattr('scraper.find_included_node', lambda t, i, n: None)
    # Run
    result = scraper.extract_program_detail(page, "99999")
    assert result["program_id"] == "99999"
    assert result["program_name_suffix"] == "Test Program"
    assert result["city"] == "Test City"
    assert result["state"] == "TS"
    assert result["data_last_updated"] == "2024-01-01"
    assert result["accredited_training_length"] == 3
    assert result["required_training_length"] == 3
    assert result["affiliated_us_government"] is False
    assert result["source_url"].endswith("/program/99999")

def test_extract_program_detail_with_survey(monkeypatch):
    page = MagicMock()
    # JSON with survey relationship
    minimal_json = {
        "key": {
            "b": {
                "data": [
                    {
                        "type": "node--program",
                        "attributes": {
                            "field_program_id": "88888",
                            "title": "Survey Program",
                            "field_address": {"locality": "Survey City", "administrative_area": "SV"},
                            "changed": "2024-02-02",
                            "field_accredited_length": 4,
                            "field_required_length": 4,
                            "field_affiliated_us_gov": True
                        },
                        "relationships": {
                            "field_survey": {"data": [{"type": "survey", "id": "s1"}]}
                        }
                    }
                ],
                "included": []
            }
        }
    }
    html = '<html><body><script id="ng-state" type="application/json">' + \
        json.dumps(minimal_json) + '</script></body></html>'
    page.content.return_value = html
    page.goto.return_value = None
    page.wait_for_selector.return_value = None
    # Patch find_included_node to return a survey node
    def fake_find_included_node(type_, id_, included):
        if type_ == "survey" and id_ == "s1":
            return {
                "attributes": {
                    "field_first_year_positions": 5,
                    "field_interviews_conducted": 10,
                    "field_avg_hours_on_duty_y1": 80,
                    "field_pct_do": 20,
                    "field_pct_img": 30,
                    "field_pct_usmd": 50,
                    "field_program_best_described_as": "Awesome",
                    "field_website": "https://example.com",
                    "field_special_features": {"value": "Special!"},
                    "field_accepting_current_year": True,
                    "field_accepting_next_year": False,
                    "field_program_start_dates": "2024-07-01",
                    "field_participates_in_eras": True,
                    "field_visa_status": "J1"
                },
                "relationships": {}
            }
        return None
    monkeypatch.setattr('scraper.find_included_node', fake_find_included_node)
    result = scraper.extract_program_detail(page, "88888")
    assert result["first_year_positions"] == 5
    assert result["interviews_conducted_last_year"] == 10
    assert result["avg_hours_on_duty_y1"] == 80
    assert result["pct_do"] == 20
    assert result["pct_img"] == 30
    assert result["pct_usmd"] == 50
    assert result["program_best_described_as"] == "Awesome"
    assert result["website"] == "https://example.com"
    assert result["special_features_text"] == "Special!"
    assert result["accepting_applications_2025_2026"] is True
    assert result["accepting_applications_2026_2027"] is False
    assert result["program_start_dates"] == "2024-07-01"
    assert result["participates_in_eras"] is True
    assert result["visa_statuses_accepted"] == "J1"

def test_extract_program_detail_with_director_and_contact(monkeypatch):
    page = MagicMock()
    # JSON with survey, director, and contact relationships
    minimal_json = {
        "key": {
            "b": {
                "data": [
                    {
                        "type": "node--program",
                        "attributes": {
                            "field_program_id": "77777",
                            "title": "Director Program",
                            "field_address": {"locality": "Dir City", "administrative_area": "DR"},
                            "changed": "2024-03-03",
                            "field_accredited_length": 5,
                            "field_required_length": 5,
                            "field_affiliated_us_gov": False
                        },
                        "relationships": {
                            "field_survey": {"data": [{"type": "survey", "id": "s2"}]}
                        }
                    }
                ],
                "included": []
            }
        }
    }
    html = '<html><body><script id="ng-state" type="application/json">' + \
        json.dumps(minimal_json) + '</script></body></html>'
    page.content.return_value = html
    page.goto.return_value = None
    page.wait_for_selector.return_value = None
    # Patch find_included_node to return director/contact nodes as needed
    def fake_find_included_node(type_, id_, included):
        if type_ == "survey" and id_ == "s2":
            return {
                "attributes": {},
                "relationships": {
                    "field_program_director": {"data": {"type": "person", "id": "d1"}},
                    "field_program_contact": {"data": {"type": "person", "id": "c1"}}
                }
            }
        if type_ == "person" and id_ == "d1":
            return {
                "attributes": {
                    "field_first_name": "DirFirst",
                    "field_middle_name": "DirMid",
                    "field_last_name": "DirLast",
                    "field_suffix": "MD",
                    "field_degrees": "PhD",
                    "field_email": "dir@email.com",
                    "field_phone": "123-456-7890",
                    "field_address": {
                        "organization": "DirOrg",
                        "address_line1": "123 Dir St",
                        "address_line2": "Apt 1",
                        "locality": "Dir City",
                        "administrative_area": "DR",
                        "postal_code": "12345"
                    }
                }
            }
        if type_ == "person" and id_ == "c1":
            return {
                "attributes": {
                    "field_first_name": "ConFirst",
                    "field_middle_name": "ConMid",
                    "field_last_name": "ConLast",
                    "field_suffix": "RN",
                    "field_degrees": "MSN",
                    "field_email": "con@email.com",
                    "field_phone": "987-654-3210",
                    "field_address": {
                        "organization": "ConOrg",
                        "address_line1": "456 Con Ave",
                        "address_line2": "Ste 2",
                        "locality": "Con City",
                        "administrative_area": "CN",
                        "postal_code": "54321"
                    }
                }
            }
        return None
    monkeypatch.setattr('scraper.find_included_node', fake_find_included_node)
    result = scraper.extract_program_detail(page, "77777")
    assert result["program_director_first_name"] == "DirFirst"
    assert result["program_director_middle_name"] == "DirMid"
    assert result["program_director_last_name"] == "DirLast"
    assert result["program_director_suffix"] == "MD"
    assert result["program_director_degrees"] == "PhD"
    assert result["program_director_organization"] == "DirOrg"
    assert result["program_director_address_line1"] == "123 Dir St"
    assert result["program_director_address_line2"] == "Apt 1"
    assert result["program_director_locality"] == "Dir City"
    assert result["program_director_administrative_area"] == "DR"
    assert result["program_director_postal_code"] == "12345"
    assert result["program_director_email"] == "dir@email.com"
    assert result["program_director_phone"] == "123-456-7890"
    assert result["contact_first_name"] == "ConFirst"
    assert result["contact_middle_name"] == "ConMid"
    assert result["contact_last_name"] == "ConLast"
    assert result["contact_suffix"] == "RN"
    assert result["contact_degrees"] == "MSN"
    assert result["contact_organization"] == "ConOrg"
    assert result["contact_address_line1"] == "456 Con Ave"
    assert result["contact_address_line2"] == "Ste 2"
    assert result["contact_locality"] == "Con City"
    assert result["contact_administrative_area"] == "CN"
    assert result["contact_postal_code"] == "54321"
    assert result["contact_email"] == "con@email.com"
    assert result["contact_phone"] == "987-654-3210" 
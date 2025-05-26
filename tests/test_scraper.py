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
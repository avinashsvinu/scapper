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
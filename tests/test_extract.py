import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import pytest
import extract
from unittest.mock import MagicMock

def test_extract_program_data_basic():
    page = MagicMock()
    # Mock two cards with IDs
    card1 = MagicMock()
    card2 = MagicMock()
    id_span1 = MagicMock()
    id_span2 = MagicMock()
    id_span1.inner_text.return_value = "ID: 12345"
    id_span2.inner_text.return_value = "ID: 67890"
    card1.query_selector.return_value = id_span1
    card2.query_selector.return_value = id_span2
    page.query_selector_all.return_value = [card1, card2]
    data = extract.extract_program_data(page)
    assert data == [{"program_id": "12345"}, {"program_id": "67890"}]

def test_scrape_all_pages(monkeypatch):
    # Patch sync_playwright to avoid launching a real browser
    mock_playwright = MagicMock()
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_playwright.chromium.launch.return_value = mock_browser
    
    # Patch extract_program_data to simulate two pages, then empty
    call_count = {'count': 0}
    def fake_extract_program_data(page):
        if call_count['count'] == 0:
            call_count['count'] += 1
            return [{"program_id": "11111"}]
        elif call_count['count'] == 1:
            call_count['count'] += 1
            return [{"program_id": "22222"}]
        else:
            return []
    
    monkeypatch.setattr('extract.sync_playwright', lambda: mock_playwright)
    monkeypatch.setattr('extract.extract_program_data', fake_extract_program_data)
    
    result = extract.scrape_all_pages()
    assert result == [{"program_id": "11111"}, {"program_id": "22222"}] 
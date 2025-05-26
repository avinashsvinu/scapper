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
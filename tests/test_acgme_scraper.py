import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import pytest
import types
import acgme_scraper
from unittest.mock import patch, MagicMock


def test_import_acgme_scraper():
    """Test that the acgme_scraper module imports successfully."""
    assert isinstance(acgme_scraper, types.ModuleType)

def test_extract_year_from_image_valid():
    """Test extract_year_from_image returns the correct year from OCR text."""
    with patch('pytesseract.image_to_string', return_value="2021 - 2022") as mock_ocr:
        with patch('PIL.Image.open', return_value=MagicMock()):
            result = acgme_scraper.extract_year_from_image("dummy_path.png")
            assert result == "2021 - 2022"
            mock_ocr.assert_called_once()

def test_extract_year_from_image_no_match():
    """Test extract_year_from_image returns None if no year is found."""
    with patch('pytesseract.image_to_string', return_value="No year here"):
        with patch('PIL.Image.open', return_value=MagicMock()):
            result = acgme_scraper.extract_year_from_image("dummy_path.png")
            assert result is None

def test_extract_year_from_image_exception():
    """Test extract_year_from_image returns None if OCR throws an exception."""
    with patch('pytesseract.image_to_string', side_effect=OSError("OCR error")):
        with patch('PIL.Image.open', return_value=MagicMock()):
            result = acgme_scraper.extract_year_from_image("dummy_path.png")
            assert result is None

# More tests will be added for each function, with mocks for Playwright and file I/O. 
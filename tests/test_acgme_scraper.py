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

def test_human_like_click_with_box():
    """Test human_like_click with a valid bounding box."""
    page = MagicMock()
    locator = MagicMock()
    locator.bounding_box.return_value = {'x': 10, 'y': 20, 'width': 100, 'height': 50}
    acgme_scraper.human_like_click(page, locator)
    assert page.mouse.move.called
    assert locator.hover.called
    assert locator.click.called

def test_human_like_click_without_box():
    """Test human_like_click when bounding_box returns None."""
    page = MagicMock()
    locator = MagicMock()
    locator.bounding_box.return_value = None
    acgme_scraper.human_like_click(page, locator)
    locator.click.assert_called_once()

# More tests will be added for each function, with mocks for Playwright and file I/O. 
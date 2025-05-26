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

def make_mock_page_with_table(years=None, ocr_result=None, raise_on_table=False):
    """Helper to create a mock Playwright page for table extraction tests."""
    page = MagicMock()
    if raise_on_table:
        page.wait_for_selector.side_effect = Exception("Table error")
    else:
        page.wait_for_selector.return_value = None
        rows = []
        if years is not None:
            for year in years:
                cell = MagicMock()
                cell.inner_text.return_value = year
                row = MagicMock()
                row.query_selector_all.return_value = [cell]
                rows.append(row)
            # Add a header row
            header = MagicMock()
            header.query_selector_all.return_value = []
            rows = [header] + rows
        page.query_selector_all.return_value = rows
    page.screenshot.return_value = None
    return page

def test_extract_academic_year_from_table_valid():
    page = make_mock_page_with_table(years=["2020 - 2021"])
    with patch("acgme_scraper.extract_year_from_image", return_value=None):
        result = acgme_scraper.extract_academic_year_from_table(page, "12345")
        assert result == "2020 - 2021"

def test_extract_academic_year_from_table_no_valid_year_triggers_ocr():
    page = make_mock_page_with_table(years=["-"])
    with patch("acgme_scraper.extract_year_from_image", return_value="2019 - 2020") as mock_ocr:
        with patch("os.path.exists", return_value=True):
            result = acgme_scraper.extract_academic_year_from_table(page, "12345")
            assert result == "2019 - 2020"
            mock_ocr.assert_called()

def test_extract_academic_year_from_table_no_rows_triggers_ocr():
    page = make_mock_page_with_table(years=[])
    with patch("acgme_scraper.extract_year_from_image", return_value="2018 - 2019") as mock_ocr:
        with patch("os.path.exists", return_value=True):
            result = acgme_scraper.extract_academic_year_from_table(page, "12345")
            assert result == "2018 - 2019"
            mock_ocr.assert_called()

def test_extract_academic_year_from_table_exception_triggers_ocr():
    page = make_mock_page_with_table(raise_on_table=True)
    with patch("acgme_scraper.extract_year_from_image", return_value="2017 - 2018") as mock_ocr:
        with patch("os.path.exists", return_value=True):
            result = acgme_scraper.extract_academic_year_from_table(page, "12345")
            assert result == "2017 - 2018"
            mock_ocr.assert_called()

def test_get_first_academic_year_with_retry_first_try():
    page = MagicMock()
    with patch("acgme_scraper.get_first_academic_year", return_value="2022 - 2023") as mock_get:
        result = acgme_scraper.get_first_academic_year_with_retry(page, "12345", max_retries=3)
        assert result == "2022 - 2023"
        mock_get.assert_called_once()

def test_get_first_academic_year_with_retry_retries_then_succeeds():
    page = MagicMock()
    # First two calls return None, third returns a value
    with patch("acgme_scraper.get_first_academic_year", side_effect=[None, None, "2021 - 2022"]) as mock_get:
        result = acgme_scraper.get_first_academic_year_with_retry(page, "12345", max_retries=3)
        assert result == "2021 - 2022"
        assert mock_get.call_count == 3

def test_get_first_academic_year_with_retry_all_fail():
    page = MagicMock()
    with patch("acgme_scraper.get_first_academic_year", return_value=None) as mock_get:
        result = acgme_scraper.get_first_academic_year_with_retry(page, "12345", max_retries=3)
        assert result is None
        assert mock_get.call_count == 3

# More tests will be added for each function, with mocks for Playwright and file I/O. 
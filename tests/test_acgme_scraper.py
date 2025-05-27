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

def make_mock_page_for_first_academic_year(click_fails=False, table_year=None, ocr_year=None, fallback_anchor=False, fallback_button=False):
    page = MagicMock()
    page.goto.return_value = None
    page.fill.return_value = None
    page.press.return_value = None
    page.wait_for_timeout.return_value = None
    page.inner_text.return_value = "Some body text"
    locator = MagicMock()
    locator.wait_for.return_value = None
    locator.scroll_into_view_if_needed.return_value = None
    if click_fails:
        locator.click.side_effect = Exception("Click failed")
    else:
        locator.click.return_value = None
    page.locator.return_value.first = locator
    page.expect_navigation.return_value.__enter__.return_value = None
    page.expect_navigation.return_value.__exit__.return_value = None
    page.url = "https://apps.acgme.org/ads/Public/Programs/AccreditationHistoryReport?programId=12345"
    # Fallback anchor simulation
    if fallback_anchor:
        anchor = MagicMock()
        anchor.inner_text.return_value = 'View Accreditation History'
        anchor.get_attribute.return_value = '/ads/Public/Programs/AccreditationHistoryReport?programId=12345'
        anchor.scroll_into_view_if_needed.return_value = None
        def anchor_click_side_effect(*args, **kwargs):
            page.url = "https://apps.acgme.org/ads/Public/Programs/AccreditationHistoryReport?programId=12345"
        anchor.click.side_effect = anchor_click_side_effect
        page.query_selector_all.return_value = [anchor]
    else:
        page.query_selector_all.return_value = []
    # Fallback button simulation
    if fallback_button:
        btn_locator = MagicMock()
        btn_locator.wait_for.return_value = None
        btn_locator.scroll_into_view_if_needed.return_value = None
        def btn_click_side_effect(*args, **kwargs):
            page.url = "https://apps.acgme.org/ads/Public/Programs/AccreditationHistoryReport?programId=12345"
        btn_locator.click.side_effect = btn_click_side_effect
        def locator_side_effect(selector):
            if selector == 'a.btn.btn-primary:has-text("View Accreditation History")':
                return MagicMock(first=btn_locator)
            return MagicMock(first=locator)
        page.locator.side_effect = locator_side_effect
    return page, locator

def test_get_first_academic_year_happy_path():
    page, locator = make_mock_page_for_first_academic_year()
    with patch("acgme_scraper.extract_academic_year_from_table", return_value="2023 - 2024") as mock_table:
        result = acgme_scraper.get_first_academic_year(page, "12345")
        assert result == "2023 - 2024"
        mock_table.assert_called()

def test_get_first_academic_year_click_fails_fallback_table():
    page, locator = make_mock_page_for_first_academic_year(click_fails=True)
    page.url = "https://apps.acgme.org/ads/Public/Programs/Search"
    # Patch page.locator to always return a mock that sets page.url on click
    def locator_side_effect(selector):
        fallback_locator = MagicMock()
        fallback_locator.wait_for.return_value = None
        fallback_locator.scroll_into_view_if_needed.return_value = None
        def click_side_effect(*args, **kwargs):
            page.url = "https://apps.acgme.org/ads/Public/Programs/AccreditationHistoryReport?programId=12345"
        fallback_locator.click.side_effect = click_side_effect
        fallback_locator.get_attribute.return_value = '/ads/Public/Programs/AccreditationHistoryReport?programId=12345'
        return MagicMock(first=fallback_locator)
    page.locator.side_effect = locator_side_effect
    # Patch page.goto to set the URL as well
    def goto_side_effect(url, *args, **kwargs):
        page.url = "https://apps.acgme.org/ads/Public/Programs/AccreditationHistoryReport?programId=12345"
    page.goto.side_effect = goto_side_effect
    with patch("acgme_scraper.extract_academic_year_from_table", side_effect=[None, "2022 - 2023"]) as mock_table:
        with patch("acgme_scraper.extract_year_from_image", return_value=None):
            with patch("os.path.exists", return_value=False):
                result = acgme_scraper.get_first_academic_year(page, "12345")
                assert result == "2022 - 2023"
                assert mock_table.call_count >= 2

def test_get_first_academic_year_click_and_table_fail_fallback_ocr():
    page, locator = make_mock_page_for_first_academic_year(click_fails=True)
    page.url = "https://apps.acgme.org/ads/Public/Programs/Search"
    with patch("acgme_scraper.extract_academic_year_from_table", return_value=None):
        with patch("acgme_scraper.extract_year_from_image", return_value="2021 - 2022") as mock_ocr:
            with patch("os.path.exists", return_value=True):
                result = acgme_scraper.get_first_academic_year(page, "12345")
                assert result == "2021 - 2022"
                mock_ocr.assert_called()

def test_get_first_academic_year_all_fail():
    page, locator = make_mock_page_for_first_academic_year(click_fails=True)
    with patch("acgme_scraper.extract_academic_year_from_table", return_value=None):
        with patch("acgme_scraper.extract_year_from_image", return_value=None):
            with patch("os.path.exists", return_value=True):
                result = acgme_scraper.get_first_academic_year(page, "12345")
                assert result is None

# Test extract_year_from_image with OCR returning a valid year
@patch('acgme_scraper.pytesseract.image_to_string')
def test_extract_year_from_image_valid(mock_ocr):
    mock_ocr.return_value = 'Some text\n2022 - 2023\nMore text'
    with patch('acgme_scraper.Image.open'):
        year = acgme_scraper.extract_year_from_image('dummy.png')
    assert year == '2022 - 2023'

# Test extract_academic_year_from_table returns year from table
def test_extract_academic_year_from_table_success():
    page = MagicMock()
    row = MagicMock()
    cell = MagicMock()
    cell.inner_text.return_value = '2021 - 2022'
    row.query_selector_all.return_value = [cell]
    page.query_selector_all.return_value = [MagicMock(), row]  # header + 1 data row
    page.wait_for_selector.return_value = None
    year = acgme_scraper.extract_academic_year_from_table(page, 'pid')
    assert year == '2021 - 2022'

# Test extract_academic_year_from_table falls back to OCR
@patch('acgme_scraper.extract_year_from_image')
def test_extract_academic_year_from_table_fallback_ocr(mock_ocr):
    page = MagicMock()
    page.query_selector_all.return_value = [MagicMock()]  # only header, no data
    page.wait_for_selector.return_value = None
    page.screenshot.return_value = None
    mock_ocr.return_value = '2020 - 2021'
    with patch('os.path.exists', return_value=True):
        year = acgme_scraper.extract_academic_year_from_table(page, 'pid')
    assert year == '2020 - 2021'

def test_get_first_academic_year_no_programs(monkeypatch):
    page = MagicMock()
    page.inner_text.return_value = 'No Programs found'
    page.goto.return_value = None
    page.fill.return_value = None
    page.press.return_value = None
    page.wait_for_timeout.return_value = None
    result = acgme_scraper.get_first_academic_year(page, 'pid')
    assert result is None

def test_get_first_academic_year_table(monkeypatch):
    page = MagicMock()
    page.inner_text.return_value = 'Some result text'
    page.goto.return_value = None
    page.fill.return_value = None
    page.press.return_value = None
    page.wait_for_timeout.return_value = None
    page.url = '/AccreditationHistoryReport?programId=pid'
    monkeypatch.setattr('acgme_scraper.extract_academic_year_from_table', lambda p, pid, s: '2019 - 2020')
    locator = MagicMock()
    locator.wait_for.return_value = None
    locator.scroll_into_view_if_needed.return_value = None
    page.locator.return_value = locator
    page.expect_navigation.return_value.__enter__.return_value = None
    page.expect_navigation.return_value.__exit__.return_value = None
    result = acgme_scraper.get_first_academic_year(page, 'pid')
    assert result == '2019 - 2020'

@patch('acgme_scraper.extract_year_from_image')
def test_get_first_academic_year_fallback_ocr(mock_ocr):
    page = MagicMock()
    page.inner_text.return_value = 'Some result text'
    page.goto.return_value = None
    page.fill.return_value = None
    page.press.return_value = None
    page.wait_for_timeout.return_value = None
    page.url = '/not-history-url'
    locator = MagicMock()
    locator.wait_for.side_effect = Exception('fail')
    page.locator.return_value = locator
    page.screenshot.return_value = None
    mock_ocr.return_value = '2018 - 2019'
    with patch('os.path.exists', return_value=True):
        result = acgme_scraper.get_first_academic_year(page, 'pid')
    assert result == '2018 - 2019'

def test_extract_academic_year_from_table_none():
    page = MagicMock()
    page.query_selector_all.return_value = [MagicMock()]  # only header, no data
    page.wait_for_selector.return_value = None
    page.screenshot.return_value = None
    with patch('os.path.exists', return_value=True), \
         patch('acgme_scraper.extract_year_from_image', return_value=None):
        year = acgme_scraper.extract_academic_year_from_table(page, 'pid')
    assert year is None

# More tests will be added for each function, with mocks for Playwright and file I/O. 
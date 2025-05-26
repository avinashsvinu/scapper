import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import pytest
import types
import acgme_scraper


def test_import_acgme_scraper():
    """Test that the acgme_scraper module imports successfully."""
    assert isinstance(acgme_scraper, types.ModuleType)

# More tests will be added for each function, with mocks for Playwright and file I/O. 
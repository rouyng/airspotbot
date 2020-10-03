"""
Tests for the adsbget.py module
"""

from .context import airspotbot

import pytest
import sys


class TestPlaceholder:
    def test_our_testing(self):
        """quick sanity check to make sure pytest is working as expected"""
        assert True is not False

    def test_import(self):
        """Test whether module to be tested was successfully imported"""
        assert "airspotbot.adsbget" in sys.modules

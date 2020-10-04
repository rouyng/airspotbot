"""
Tests for the airspotbot.py module
"""

from .context import airspotbot

import pytest
import sys


class TestBasics:
    def test_our_testing(self):
        """quick sanity check to make sure pytest is working as expected"""
        assert True is not False

    def test_import(self):
        """Test whether module to be tested was successfully imported"""
        assert "airspotbot" in sys.modules


class TestTwitterValidation:
    """Tests validation of Twitter bot configuration"""

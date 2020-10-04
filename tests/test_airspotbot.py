"""
Tests for the airspotbot.py module
"""

from .context import airspotbot

import pytest
import sys


def test_import():
    """Test whether module to be tested was successfully imported"""
    assert "airspotbot" in sys.modules


class TestTwitterValidation:
    """Tests validation of Twitter bot configuration"""

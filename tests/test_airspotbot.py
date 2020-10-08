"""
Tests for the airspotbot.py module
"""

from .context import airspotbot

import pytest
import sys

valid_config = "./valid_asb.config"


def test_import():
    """Test whether module to be tested was successfully imported"""
    assert "airspotbot" in sys.modules


def test_read_config():
    """Test that airspotbot.read_config() correctly parses a sample config file"""
    imported_config = airspotbot.airspotbot.read_config(valid_config)
    config_values = {'ADSB': {'lat': '0',
                           'long': '0',
                           'radius': '25',
                           'adsb_interval': '120',
                           'cooldown': '3600',
                           'spot_unknown': 'n',
                           'spot_mil': 'y',
                           'adsb_api': 'adsbx',
                           'adsb_api_key': '2CKHn1MKm7aXj8Eb'},
                    'TWITTER': {'consumer_key': 't7zBuf2DVhM7tWgF',
                                'consumer_secret': 'duiMwaSs9EkcNn4H',
                                'access_token': 'BxkfYCsYkat3fva6',
                                'access_token_secret': 'r6CSsg6egGro81YG',
                                'tweet_interval': '30',
                                'use_descriptions': 'y',
                                'down_tweet': 'y'},
                    'LOCATION': {'location_type': 'manual',
                                 'location_description': 'near somewhere',
                                 'pelias_host': 'http://localhost',
                                 'pelias_port': '4000',
                                 'pelias_area_layer': 'neighbourhood',
                                 'pelias_point_layer': 'venue'},
                    'MISC': {'logging_level': 'info'}
                     }
    # Test that expected sections are parsed
    for s in ('ADSB', 'TWITTER', 'LOCATION', 'MISC'):
        assert s in imported_config.sections()
    # Test that expected values and organization are parsed
    for g, h in config_values.items():
        for j, i in h.items():
            assert i == imported_config[g][j]


class TestTwitterValidation:
    """Tests validation of Twitter bot configuration"""

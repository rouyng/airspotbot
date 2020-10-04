"""
Tests for the location.py module
"""

from .context import airspotbot

import pytest
import sys

"""
[LOCATION]
# options for configuring location description
location_type = manual
location_description = "near somewhere"
pelias_host = http://localhost
pelias_port = 4000
pelias_area_layer = neighbourhood
pelias_point_layer = venue
"""


@pytest.fixture
def generate_manual_location_config():
    import configparser
    dummy_config = configparser.ConfigParser()
    dummy_config['LOCATION'] = {"location_type": "manual",
                                "location_description": "near somewhere",
                                "pelias_host": "http://localhost",
                                "pelias_port": 4000,
                                "pelias_area_layer": "neighbourhood",
                                "pelias_point_layer": "venue"}
    return dummy_config

@pytest.fixture
def generate_pelias_location_config():
    import configparser
    dummy_config = configparser.ConfigParser()
    dummy_config['LOCATION'] = {"location_type": "pelias",
                                "location_description": "near somewhere",
                                "pelias_host": "http://localhost",
                                "pelias_port": 4000,
                                "pelias_area_layer": "neighbourhood",
                                "pelias_point_layer": "venue"}
    return dummy_config


@pytest.fixture
def generate_coordinate_location_config():
    import configparser
    dummy_config = configparser.ConfigParser()
    dummy_config['LOCATION'] = {"location_type": "coordinate",
                                "location_description": "near somewhere",
                                "pelias_host": "http://localhost",
                                "pelias_port": 4000,
                                "pelias_area_layer": "neighbourhood",
                                "pelias_point_layer": "venue"}
    return dummy_config


class TestBasics:
    def test_our_testing(self):
        """quick sanity check to make sure pytest is working as expected"""
        assert True is not False

    def test_import(self):
        """Test whether module to be tested was successfully imported"""
        assert "airspotbot.location" in sys.modules


class TestLocationValidation:
    """Tests validation of location configuration"""
    def test_manual_location(self, generate_manual_location_config):
        """Test that manual location reporting is properly validated"""
        loc = airspotbot.location.Locator(generate_manual_location_config)
        assert loc.location_type == 'MANUAL'
        assert loc.location_manual_description == "near somewhere"
        assert loc.get_location_description(40.0, -76.0) == "near somewhere"

    def test_coordinate_location(self, generate_coordinate_location_config):
        """Test that coordinate location reporting is properly validated"""
        loc = airspotbot.location.Locator(generate_coordinate_location_config)
        assert loc.location_type == "COORDINATE"
        assert loc.location_manual_description == ""
        assert loc.get_location_description(40.0, -76.0) == "near 40.0, -76.0"
        assert loc.get_location_description(40.0000000001, -76.000000001) == "near 40.0, -76.0"
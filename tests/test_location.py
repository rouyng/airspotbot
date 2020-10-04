"""
Tests for the location.py module
"""

from .context import airspotbot

import configparser
import pytest
import random
import sys


@pytest.fixture
def generate_manual_location_config(scope="module"):
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
    dummy_config = configparser.ConfigParser()
    dummy_config['LOCATION'] = {"location_type": "pelias",
                                "location_description": "near somewhere",
                                "pelias_host": "http://localhost",
                                "pelias_port": 4000,
                                "pelias_area_layer": "neighbourhood",
                                "pelias_point_layer": "venue"}
    return dummy_config


@pytest.fixture
def generate_coordinate_location_config(scope="module"):
    dummy_config = configparser.ConfigParser()
    dummy_config['LOCATION'] = {"location_type": "coordinate",
                                "location_description": "near somewhere",
                                "pelias_host": "http://localhost",
                                "pelias_port": 4000,
                                "pelias_area_layer": "neighbourhood",
                                "pelias_point_layer": "venue"}
    return dummy_config


@pytest.fixture
def generate_empty_config():
    dummy_config = configparser.ConfigParser()
    dummy_config['LOCATION'] = {"location_type": "",
                                "location_description": "",
                                "pelias_host": "",
                                "pelias_port": "",
                                "pelias_area_layer": "",
                                "pelias_point_layer": ""}
    return dummy_config


def test_import():
    """Test whether module to be tested was successfully imported"""
    assert "airspotbot.location" in sys.modules


class TestLocationValidation:
    """Tests validation of location configuration"""
    def test_manual_location(self, generate_manual_location_config):
        """Test that manual location reporting is properly validated"""
        loc = airspotbot.location.Locator(generate_manual_location_config)
        assert loc.location_type == 'MANUAL'
        assert loc.location_manual_description == "near somewhere"
        # test 5 random lat/lon pairs
        for _ in range(0, 5):
            random_lat = random.uniform(-90, 90)
            random_lon = random.uniform(-180, 180)
            assert loc.get_location_description(random_lat, random_lon) == "near somewhere"

    def test_coordinate_location(self, generate_coordinate_location_config):
        """Test that coordinate location reporting is properly validated"""
        loc = airspotbot.location.Locator(generate_coordinate_location_config)
        assert loc.location_type == "COORDINATE"
        assert loc.location_manual_description == ""
        # test 5 random lat/lon pairs
        for _ in range(0, 5):
            random_lat = random.uniform(-90, 90)
            random_lon = random.uniform(-180, 180)
            assert loc.get_location_description(random_lat, random_lon) == f"near {round(random_lat, 4)}, {round(random_lon, 4)}"

    def test_empty_location_type(self, generate_empty_config):
        """Test that an empty location type defaults to coordinate description"""
        loc = airspotbot.location.Locator(generate_empty_config)
        assert loc.location_type == 'COORDINATE'

    def test_empty_manual(self, generate_empty_config):
        """Test config that MANUAL location type but no location description defaults to coordinate"""
        generate_empty_config['LOCATION']['location_type'] = 'manual'
        loc = airspotbot.location.Locator(generate_empty_config)
        assert loc.location_type == 'COORDINATE'

    def test_empty_host(self, generate_pelias_location_config):
        generate_pelias_location_config['LOCATION']['pelias_host'] = ""
        with pytest.raises(configparser.NoOptionError):
            airspotbot.location.Locator(generate_pelias_location_config)

    def test_empty_port(self, generate_pelias_location_config):
        generate_pelias_location_config['LOCATION']['pelias_port'] = ""
        with pytest.raises(configparser.NoOptionError):
            airspotbot.location.Locator(generate_pelias_location_config)
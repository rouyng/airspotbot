"""
Tests for the adsbget.py module
"""

from .context import airspotbot

import pytest
import random
import sys
from io import StringIO
import configparser
import string

valid_watchlist = "./valid_watchlist.csv"
invalid_watchlist = "./invalid_watchlist.csv"

@pytest.fixture
def generate_empty_adsb_config(scope="module"):
    dummy_config = configparser.ConfigParser()
    dummy_config['ADSB'] = {"lat": "",
                                "long": "",
                                "radius": "",
                                "adsb_interval": "",
                                "cooldown": "",
                                "spot_unknown": "",
                                "spot_mil": "",
                                "adsb_api": "",
                                "adsb_api_key": ""}
    return dummy_config


@pytest.fixture
def generate_valid_adsb_config(scope="module"):
    dummy_config = configparser.ConfigParser()
    dummy_config['ADSB'] = {"lat": str(random.uniform(-90, 90)),
                                "long": str(random.uniform(-180, 180)),
                                "radius": str(random.choice((1, 5, 10, 25, 100, 250))),
                                "adsb_interval": str(random.randint(1, 20)),
                                "cooldown": str(random.randint(1, 20)),
                                "spot_unknown": "y",
                                "spot_mil": "y",
                                "adsb_api": "adsbx",
                                "adsb_api_key": ''.join(random.choices(string.ascii_letters + string.digits, k=16))}
    return dummy_config


@pytest.fixture
def generate_spotter(generate_valid_adsb_config, scope="module"):
    return airspotbot.adsbget.Spotter(generate_valid_adsb_config, valid_watchlist)


def test_import():
    """Test whether module to be tested was successfully imported"""
    assert "airspotbot.adsbget" in sys.modules


class TestADSBValidation:
    """Tests validation of ADSB configuration"""
    def test_empty_interval(self, generate_empty_adsb_config):
        with pytest.raises(ValueError) as exc_info:
            airspotbot.adsbget.Spotter(generate_empty_adsb_config, valid_watchlist)
        assert "adsb_interval must be an integer value" in str(exc_info.value)

    def test_empty_cooldown(self, generate_empty_adsb_config):
        generate_empty_adsb_config['ADSB']['adsb_interval'] = "10"
        with pytest.raises(ValueError) as exc_info:
            airspotbot.adsbget.Spotter(generate_empty_adsb_config, valid_watchlist)
        assert "cooldown must be an integer value" in str(exc_info.value)

    def test_empty_latitude(self, generate_empty_adsb_config):
        generate_empty_adsb_config['ADSB']['cooldown'] = "10"
        generate_empty_adsb_config['ADSB']['adsb_interval'] = "10"
        with pytest.raises(ValueError) as exc_info:
            airspotbot.adsbget.Spotter(generate_empty_adsb_config, valid_watchlist)
        assert "latitude must be a float value >= -90 and <= 90" in str(exc_info.value)

    def test_invalid_latitudes(self, generate_empty_adsb_config):
        """Test impossible latitudes < -90 or > 90 raising an exception"""
        generate_empty_adsb_config['ADSB']['cooldown'] = "10"
        generate_empty_adsb_config['ADSB']['adsb_interval'] = "10"
        generate_empty_adsb_config['ADSB']['lat'] = str(random.uniform(90.01, 999999))
        with pytest.raises(ValueError) as exc_info:
            airspotbot.adsbget.Spotter(generate_empty_adsb_config, valid_watchlist)
        assert "latitude must be a float value >= -90 and <= 90" in str(exc_info.value)
        generate_empty_adsb_config['ADSB']['lat'] = str(random.uniform(-90.01, -999999))
        with pytest.raises(ValueError) as exc_info:
            airspotbot.adsbget.Spotter(generate_empty_adsb_config, valid_watchlist)
        assert "latitude must be a float value >= -90 and <= 90" in str(exc_info.value)

    def test_empty_longitude(self, generate_empty_adsb_config):
        generate_empty_adsb_config['ADSB']['cooldown'] = "10"
        generate_empty_adsb_config['ADSB']['adsb_interval'] = "10"
        generate_empty_adsb_config['ADSB']['lat'] = str(random.uniform(-90, 90))
        with pytest.raises(ValueError) as exc_info:
            airspotbot.adsbget.Spotter(generate_empty_adsb_config, valid_watchlist)
        assert "longitude must be a float value >= -180 and <= 180" in str(exc_info.value)

    def test_invalid_longitudes(self, generate_empty_adsb_config):
        """Test impossible longitudes < -180 or > 180 raising an exception"""
        generate_empty_adsb_config['ADSB']['cooldown'] = "10"
        generate_empty_adsb_config['ADSB']['adsb_interval'] = "10"
        generate_empty_adsb_config['ADSB']['lat'] = str(random.uniform(-90, 90))
        generate_empty_adsb_config['ADSB']['long'] = str(random.uniform(180.01, 999999))
        with pytest.raises(ValueError) as exc_info:
            airspotbot.adsbget.Spotter(generate_empty_adsb_config, valid_watchlist)
        assert "longitude must be a float value >= -180 and <= 180" in str(exc_info.value)
        generate_empty_adsb_config['ADSB']['long'] = str(random.uniform(-180.01, -999999))
        with pytest.raises(ValueError) as exc_info:
            airspotbot.adsbget.Spotter(generate_empty_adsb_config, valid_watchlist)
        assert "longitude must be a float value >= -180 and <= 180" in str(exc_info.value)

    def test_invalid_radii(self, generate_empty_adsb_config):
        """Test invalid radii raising an exception"""
        generate_empty_adsb_config['ADSB']['cooldown'] = "10"
        generate_empty_adsb_config['ADSB']['adsb_interval'] = "10"
        generate_empty_adsb_config['ADSB']['lat'] = str(random.uniform(-90, 90))
        generate_empty_adsb_config['ADSB']['long'] = str(random.uniform(-180, 180))
        # try 5 different invalid radii and make sure they raise the correct exception
        for _ in range(0, 5):
            invalid_radius = 1
            while invalid_radius in (1, 5, 10, 25, 100, 250):
                invalid_radius = random.randint(0, 9999)
            with pytest.raises(ValueError) as exc_info:
                airspotbot.adsbget.Spotter(generate_empty_adsb_config, valid_watchlist)
            assert "Error in configuration file: radius value is not 1, 5, 10, 25, 100, or 250" in str(exc_info.value)


class TestWatchlistImport:
    """Tests import of watchlist.csv"""

    def test_invalid_watchlist_file(self, generate_valid_adsb_config):
        """Test exception thrown when bogus watchlist file is read"""
        with pytest.raises(IndexError) as exc_info:
            airspotbot.adsbget.Spotter(generate_valid_adsb_config, invalid_watchlist)
        assert "Error reading watchlist.csv, please check the watchlist file." in str(exc_info.value)

    def test_watchlist_length(self, generate_spotter):
        """Test whether the correct number of watchlist entries were imported"""
        spots = generate_spotter
        assert len(spots.watchlist_rn) + len(spots.watchlist_tc) + len(spots.watchlist_ia) == 4

    def test_rn_watchlist_length(self, generate_spotter):
        """Test registration number watchlist length"""
        spots = generate_spotter
        assert len(spots.watchlist_rn) == 1

    def test_ia_watchlist_length(self, generate_spotter):
        """Test ICAO hex code watchlist length"""
        spots = generate_spotter
        assert len(spots.watchlist_ia) == 1

    def test_tc_watchlist_length(self, generate_spotter):
        """Test type code watchlist length"""
        spots = generate_spotter
        assert len(spots.watchlist_tc) == 2

    def test_h60_watchlist(self, generate_spotter):
        """Check that the H60 entry in valid_watchlist is properly imported"""
        spots = generate_spotter
        assert "H60" in spots.watchlist_tc.keys()
        assert spots.watchlist_tc["H60"]["desc"] == "Sikorsky H-60"
        assert spots.watchlist_tc["H60"]["mil_only"] is False
        assert spots.watchlist_tc["H60"]["img"] == "uh-60.jpg"

    def test_guppy_watchlist(self, generate_spotter):
        """Check that the Super Guppy entry in valid_watchlist is properly imported"""
        spots = generate_spotter
        assert "NASA941" in spots.watchlist_rn.keys()
        assert spots.watchlist_rn["NASA941"]["desc"] == "NASA Super Guppy"
        assert spots.watchlist_rn["NASA941"]["img"] == ""

    def test_antonov_watchlist(self, generate_spotter):
        """Check that the AN-225 entry in valid_watchlist is properly imported"""
        spots = generate_spotter
        assert "508035" in spots.watchlist_ia.keys()
        assert spots.watchlist_ia["508035"]["desc"] == "Antonov AN-225 Mriya"
        assert spots.watchlist_ia["508035"]["img"] == ""

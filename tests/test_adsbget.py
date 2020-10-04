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
def generate_watchlist(scope="module"):
    csv_string = StringIO("""\
    Key,Type,Mil Only,Description,Image
    H60,TC,N,Sikorsky H-60,uh-60
    EC45,TC,Y,UH-72 Lakota,uh72.jpg
    NASA941,RN,,NASA Super Guppy,
    508035,IA,,Antonov AN-225 Mriya,""")
    return csv_string


def test_import():
    """Test whether module to be tested was successfully imported"""
    assert "airspotbot.adsbget" in sys.modules


class TestADSBValidation:
    """Tests validation of ADSB configuration"""
    def test_empty_interval(self, generate_empty_adsb_config, generate_watchlist):
        with pytest.raises(ValueError) as exc_info:
            airspotbot.adsbget.Spotter(generate_empty_adsb_config, generate_watchlist)
        assert "adsb_interval must be an integer value" in str(exc_info.value)

    def test_empty_cooldown(self, generate_empty_adsb_config, generate_watchlist):
        generate_empty_adsb_config['ADSB']['adsb_interval'] = "10"
        with pytest.raises(ValueError) as exc_info:
            airspotbot.adsbget.Spotter(generate_empty_adsb_config, generate_watchlist)
        assert "cooldown must be an integer value" in str(exc_info.value)

    def test_empty_latitude(self, generate_empty_adsb_config, generate_watchlist):
        generate_empty_adsb_config['ADSB']['cooldown'] = "10"
        generate_empty_adsb_config['ADSB']['adsb_interval'] = "10"
        with pytest.raises(ValueError) as exc_info:
            airspotbot.adsbget.Spotter(generate_empty_adsb_config, generate_watchlist)
        assert "latitude must be a float value >= -90 and <= 90" in str(exc_info.value)

    def test_invalid_latitudes(self, generate_empty_adsb_config, generate_watchlist):
        """Test impossible latitudes < -90 or > 90 raising an exception"""
        generate_empty_adsb_config['ADSB']['cooldown'] = "10"
        generate_empty_adsb_config['ADSB']['adsb_interval'] = "10"
        generate_empty_adsb_config['ADSB']['lat'] = str(random.uniform(90.01, 999999))
        with pytest.raises(ValueError) as exc_info:
            airspotbot.adsbget.Spotter(generate_empty_adsb_config, generate_watchlist)
        assert "latitude must be a float value >= -90 and <= 90" in str(exc_info.value)
        generate_empty_adsb_config['ADSB']['lat'] = str(random.uniform(-90.01, -999999))
        with pytest.raises(ValueError) as exc_info:
            airspotbot.adsbget.Spotter(generate_empty_adsb_config, generate_watchlist)
        assert "latitude must be a float value >= -90 and <= 90" in str(exc_info.value)

    def test_empty_longitude(self, generate_empty_adsb_config, generate_watchlist):
        generate_empty_adsb_config['ADSB']['cooldown'] = "10"
        generate_empty_adsb_config['ADSB']['adsb_interval'] = "10"
        generate_empty_adsb_config['ADSB']['lat'] = str(random.uniform(-90, 90))
        with pytest.raises(ValueError) as exc_info:
            airspotbot.adsbget.Spotter(generate_empty_adsb_config, generate_watchlist)
        assert "longitude must be a float value >= -180 and <= 180" in str(exc_info.value)

    def test_invalid_longitudes(self, generate_empty_adsb_config, generate_watchlist):
        """Test impossible longitudes < -180 or > 180 raising an exception"""
        generate_empty_adsb_config['ADSB']['cooldown'] = "10"
        generate_empty_adsb_config['ADSB']['adsb_interval'] = "10"
        generate_empty_adsb_config['ADSB']['lat'] = str(random.uniform(-90, 90))
        generate_empty_adsb_config['ADSB']['long'] = str(random.uniform(180.01, 999999))
        with pytest.raises(ValueError) as exc_info:
            airspotbot.adsbget.Spotter(generate_empty_adsb_config, generate_watchlist)
        assert "longitude must be a float value >= -180 and <= 180" in str(exc_info.value)
        generate_empty_adsb_config['ADSB']['long'] = str(random.uniform(-180.01, -999999))
        with pytest.raises(ValueError) as exc_info:
            airspotbot.adsbget.Spotter(generate_empty_adsb_config, generate_watchlist)
        assert "longitude must be a float value >= -180 and <= 180" in str(exc_info.value)

    def test_invalid_radii(self, generate_empty_adsb_config, generate_watchlist):
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
                airspotbot.adsbget.Spotter(generate_empty_adsb_config, generate_watchlist)
            assert "Error in configuration file: radius value is not 1, 5, 10, 25, 100, or 250" in str(exc_info.value)


class TestWatchlistImport:
    """Tests import of watchlist.csv"""
    
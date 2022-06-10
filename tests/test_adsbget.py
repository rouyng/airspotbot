"""
Tests for the adsbget.py module
"""

from .context import airspotbot

import pytest
import random
import sys
import configparser
import logging
import requests_mock
import requests
import string

valid_watchlist = "./tests/valid_watchlist.csv"
invalid_watchlist = "./tests/invalid_watchlist.csv"


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
                            "adsb_api_key": ""}
    return dummy_config


@pytest.fixture
def generate_valid_adsb_config(scope="module"):
    dummy_config = configparser.ConfigParser()
    dummy_config['ADSB'] = {"lat": str(random.uniform(-90, 90)),
                            "long": str(random.uniform(-180, 180)),
                            "radius": str(random.randint(1, 250)),
                            "adsb_interval": str(random.randint(1, 20)),
                            "cooldown": str(random.randint(1, 20)),
                            "spot_unknown": "y",
                            "spot_mil": "y",
                            "spot_interesting": "y",
                            "adsb_api_key": ''.join(
                                random.choices(string.ascii_letters + string.digits, k=16))}
    return dummy_config


@pytest.fixture
def generate_spotter(generate_valid_adsb_config, scope="module"):
    return airspotbot.adsbget.Spotter(generate_valid_adsb_config, valid_watchlist)


@pytest.fixture
def sample_adsbx_json():
    """A sample JSON response from the ADSBx API showing some busy airspace"""
    return {"ac": [
        {"hex": "3e232e", "type": "adsb_icao", "flight": "DIENE   ", "r": "D-IENE", "t": "C25A",
         "alt_baro": 1200, "alt_geom": 1525, "gs": 177.6, "ias": 163, "tas": 164, "mach": 0.252,
         "wd": 61, "ws": 20, "track": 204.98, "track_rate": -0.19, "roll": -1.76,
         "mag_heading": 200.57, "true_heading": 201.14, "baro_rate": -288, "geom_rate": -64,
         "squawk": "2751", "emergency": "none", "category": "A1", "nav_qnh": 1019.2,
         "nav_altitude_mcp": 1344, "nav_altitude_fms": 1808, "nav_heading": 198.98,
         "lat": 51.374119, "lon": 0.0354, "nic": 8, "rc": 186, "seen_pos": 0.086, "version": 2,
         "nic_baro": 1, "nac_p": 11, "nac_v": 1, "sil": 3, "sil_type": "perhour", "gva": 2,
         "sda": 2, "alert": 0, "spi": 0, "mlat": [], "tisb": [], "messages": 7566034, "seen": 0,
         "rssi": -2.8, "dst": 16.71},
        {"hex": "407941", "type": "mlat", "flight": "GAWGB   ", "r": "G-AWGB", "t": "SPIT",
         "dbFlags": 1, "gs": 250, "track": 229, "squawk": "7047", "emergency": "none",
         "category": "A1",
         "lat": 51.310141, "lon": 0.128013, "nic": 0, "rc": 0, "seen_pos": 3.919, "version": 0,
         "alert": 0, "spi": 0, "mlat": ["gs", "track", "lat", "lon", "nic", "rc"], "tisb": [],
         "messages": 3194830, "seen": 0.5, "rssi": -8.6, "dst": 15.52},
        {"hex": "407968", "type": "mlat", "flight": "GHCNX   ", "r": "G-HCNX", "t": "EC55",
         "alt_baro": 1250, "gs": 145, "tas": 278, "track": 12, "roll": -0.18, "baro_rate": 0,
         "squawk": "6600", "category": "A7", "nav_qnh": 1013.2, "nav_altitude_mcp": 27008,
         "nav_altitude_fms": 27008, "lat": 51.296933, "lon": 0.188649, "nic": 0, "rc": 0,
         "seen_pos": 0.095, "version": 0, "alert": 0, "spi": 0,
         "mlat": ["gs", "track", "baro_rate", "lat", "lon", "nic", "rc"], "tisb": [],
         "messages": 365967, "seen": 0.1, "rssi": -7.5, "dst": 14.36},
        {"hex": "407536", "type": "adsb_icao", "flight": "BAW622  ", "r": "G-TTNF", "t": "A20N",
         "dbFlags": 2, "alt_baro": 14525, "alt_geom": 15075, "gs": 383.4, "ias": 306, "tas": 378,
         "mach": 0.6,
         "wd": 218, "ws": 12, "oat": -12, "tat": 7, "track": 101.28, "track_rate": 0, "roll": -0.35,
         "mag_heading": 102.3, "true_heading": 102.95, "baro_rate": 2624, "geom_rate": 2592,
         "squawk": "3473", "emergency": "none", "category": "A3", "nav_qnh": 1012.8,
         "nav_altitude_mcp": 27008, "lat": 51.360199, "lon": 0.270386, "nic": 8, "rc": 186,
         "seen_pos": 0.195, "version": 2, "nic_baro": 1, "nac_p": 9, "nac_v": 1, "sil": 3,
         "sil_type": "perhour", "gva": 2, "sda": 3, "alert": 0, "spi": 0, "mlat": [], "tisb": [],
         "messages": 22288110, "seen": 0, "rssi": -10, "dst": 9.51},
        {"hex": "4ca708", "type": "adsb_icao", "flight": "RYR89BZ ", "r": "EI-EBL", "t": "B738",
         "alt_baro": 35025, "alt_geom": 35825, "gs": 422.4, "ias": 259, "tas": 442, "mach": 0.764,
         "wd": 210, "ws": 102, "oat": -53, "tat": -27, "track": 124.29, "track_rate": 0,
         "roll": -0.35, "mag_heading": 136.76, "true_heading": 137.46, "baro_rate": 0,
         "geom_rate": 32, "squawk": "5256", "emergency": "none", "category": "A3",
         "nav_qnh": 1013.6, "nav_altitude_mcp": 35008, "nav_altitude_fms": 35008,
         "nav_heading": 136.41, "lat": 51.380636, "lon": 0.488815, "nic": 7, "rc": 371,
         "seen_pos": 0.39, "version": 2, "nic_baro": 1, "nac_p": 8, "nac_v": 1, "sil": 3,
         "sil_type": "perhour", "gva": 1, "sda": 2, "alert": 0, "spi": 0, "mlat": [], "tisb": [],
         "messages": 31308987, "seen": 0.2, "rssi": -12.7, "dst": 5.44},
        {"hex": "3e2bcd", "type": "adsb_icao", "flight": "AWU504E ", "r": "D-IHUB", "t": "C25A",
         "alt_baro": 5825, "alt_geom": 6225, "gs": 257.6, "ias": 244, "tas": 266, "mach": 0.408,
         "wd": 166, "ws": 10, "oat": 7, "tat": 16, "track": 186.46, "track_rate": -0.03,
         "roll": -0.18, "mag_heading": 184.92, "true_heading": 185.72, "baro_rate": 32,
         "geom_rate": 0, "squawk": "2037", "emergency": "none", "category": "A1", "nav_qnh": 1020,
         "nav_altitude_mcp": 6016, "nav_heading": 184.92, "lat": 51.419174, "lon": 0.727473,
         "nic": 8, "rc": 186, "seen_pos": 0.221, "version": 2, "nic_baro": 1, "nac_p": 10,
         "nac_v": 1, "sil": 3, "sil_type": "perhour", "gva": 2, "sda": 2, "alert": 0, "spi": 0,
         "mlat": [], "tisb": [], "messages": 5724763, "seen": 0, "rssi": -5.5, "dst": 10.6},
        {"hex": "40796c", "type": "adsb_icao", "flight": "TOM7NT  ", "r": "G-TUMN", "t": "B38M",
         "alt_baro": 14375, "alt_geom": 14950, "gs": 344.1, "ias": 277, "tas": 342, "mach": 0.54,
         "wd": 183, "ws": 16, "oat": -9, "tat": 6, "track": 83.66, "track_rate": 0.03, "roll": 0,
         "mag_heading": 85.25, "true_heading": 86.07, "baro_rate": 2432, "geom_rate": 2432,
         "squawk": "3441", "emergency": "none", "category": "A3", "nav_qnh": 1013.6,
         "nav_altitude_mcp": 27008, "nav_altitude_fms": 27008, "nav_heading": 85.08,
         "lat": 51.207733, "lon": 0.736307, "nic": 8, "rc": 186, "seen_pos": 0, "version": 2,
         "nic_baro": 1, "nac_p": 10, "nac_v": 2, "sil": 3, "sil_type": "perhour", "gva": 2,
         "sda": 2, "alert": 0, "spi": 0, "mlat": [], "tisb": [], "messages": 19732262, "seen": 0,
         "rssi": -18.8, "dst": 18.88},
        {"hex": "4058c7", "type": "mlat", "flight": "GZAAP   ", "r": "G-ZAAP", "t": "CRUZ",
         "alt_baro": "ground", "gs": 50, "track": 54, "baro_rate": 2, "squawk": "4575",
         "lat": 51.538891,
         "lon": 0.76194, "nic": 0, "rc": 0, "seen_pos": 1.95, "alert": 0, "spi": 0,
         "mlat": ["gs", "track", "baro_rate", "lat", "lon", "nic", "rc"], "tisb": [],
         "messages": 198847, "seen": 0.8, "rssi": -5.4, "dst": 12.2},
        {"hex": "77058e", "type": "adsb_icao", "flight": "ALK503  ", "r": "4R-ALN", "t": "A333",
         "alt_baro": 14100, "alt_geom": 14750, "gs": 373, "ias": 307, "tas": 376, "mach": 0.596,
         "wd": 321, "ws": 5, "oat": -11, "tat": 8, "track": 270.61, "track_rate": 0, "roll": 0,
         "mag_heading": 270.35, "true_heading": 271.15, "baro_rate": -1856, "geom_rate": -1856,
         "squawk": "3260", "emergency": "none", "category": "A5", "nav_qnh": 1013.6,
         "nav_altitude_mcp": 8000, "lat": 51.643295, "lon": 0.780549, "nic": 8, "rc": 186,
         "seen_pos": 0.123, "version": 2, "nic_baro": 1, "nac_p": 9, "nac_v": 1, "sil": 3,
         "sil_type": "perhour", "gva": 2, "sda": 2, "alert": 0, "spi": 0, "mlat": [], "tisb": [],
         "messages": 11755558, "seen": 0, "rssi": -19.9, "dst": 16.02}], "total": 9,
        "now": 1654367538288, "ctime": 1654367542448, "ptime": 184}


@pytest.fixture
def unexpected_adsbx_json():
    """A sample JSON response from the ADSBx API with some missing keys"""
    # first aircraft is missing hex key
    return {"ac": [
        {"type": "adsb_icao", "flight": "DIENE   ", "r": "D-IENE", "t": "C25A",
         "alt_baro": 1200, "alt_geom": 1525, "gs": 177.6, "ias": 163, "tas": 164, "mach": 0.252,
         "wd": 61, "ws": 20, "track": 204.98, "track_rate": -0.19, "roll": -1.76,
         "mag_heading": 200.57, "true_heading": 201.14, "baro_rate": -288, "geom_rate": -64,
         "squawk": "2751", "emergency": "none", "category": "A1", "nav_qnh": 1019.2,
         "nav_altitude_mcp": 1344, "nav_altitude_fms": 1808, "nav_heading": 198.98,
         "lat": 51.374119, "lon": 0.0354, "nic": 8, "rc": 186, "seen_pos": 0.086, "version": 2,
         "nic_baro": 1, "nac_p": 11, "nac_v": 1, "sil": 3, "sil_type": "perhour", "gva": 2,
         "sda": 2, "alert": 0, "spi": 0, "mlat": [], "tisb": [], "messages": 7566034, "seen": 0,
         "rssi": -2.8, "dst": 16.71},
        {"hex": "407941", "type": "mlat", "flight": "GAWGB   ", "r": "G-AWGB", "t": "SPIT",
         "gs": 250, "track": 229, "squawk": "7047", "emergency": "none", "category": "A1",
         "lat": 51.310141, "lon": 0.128013, "nic": 0, "rc": 0, "seen_pos": 3.919, "version": 0,
         "alert": 0, "spi": 0, "mlat": ["gs", "track", "lat", "lon", "nic", "rc"], "tisb": [],
         "messages": 3194830, "seen": 0.5, "rssi": -8.6, "dst": 15.52},
        {"hex": "407968", "type": "mlat", "flight": "GHCNX   ", "r": "G-HCNX", "t": "EC55",
         "alt_baro": 1250, "gs": 145, "tas": 278, "track": 12, "roll": -0.18, "baro_rate": 0,
         "squawk": "6600", "category": "A7", "nav_qnh": 1013.2, "nav_altitude_mcp": 27008,
         "nav_altitude_fms": 27008, "lat": 51.296933, "lon": 0.188649, "nic": 0, "rc": 0,
         "seen_pos": 0.095, "version": 0, "alert": 0, "spi": 0,
         "mlat": ["gs", "track", "baro_rate", "lat", "lon", "nic", "rc"], "tisb": [],
         "messages": 365967, "seen": 0.1, "rssi": -7.5, "dst": 14.36},
        {"hex": "407536", "type": "adsb_icao", "flight": "BAW622  ", "r": "G-TTNF", "t": "A20N",
         "alt_baro": 14525, "alt_geom": 15075, "gs": 383.4, "ias": 306, "tas": 378, "mach": 0.6,
         "wd": 218, "ws": 12, "oat": -12, "tat": 7, "track": 101.28, "track_rate": 0, "roll": -0.35,
         "mag_heading": 102.3, "true_heading": 102.95, "baro_rate": 2624, "geom_rate": 2592,
         "squawk": "3473", "emergency": "none", "category": "A3", "nav_qnh": 1012.8,
         "nav_altitude_mcp": 27008, "lat": 51.360199, "lon": 0.270386, "nic": 8, "rc": 186,
         "seen_pos": 0.195, "version": 2, "nic_baro": 1, "nac_p": 9, "nac_v": 1, "sil": 3,
         "sil_type": "perhour", "gva": 2, "sda": 3, "alert": 0, "spi": 0, "mlat": [], "tisb": [],
         "messages": 22288110, "seen": 0, "rssi": -10, "dst": 9.51},
        {"hex": "4ca708", "type": "adsb_icao", "flight": "RYR89BZ ", "r": "EI-EBL", "t": "B738",
         "alt_baro": 35025, "alt_geom": 35825, "gs": 422.4, "ias": 259, "tas": 442, "mach": 0.764,
         "wd": 210, "ws": 102, "oat": -53, "tat": -27, "track": 124.29, "track_rate": 0,
         "roll": -0.35, "mag_heading": 136.76, "true_heading": 137.46, "baro_rate": 0,
         "geom_rate": 32, "squawk": "5256", "emergency": "none", "category": "A3",
         "nav_qnh": 1013.6, "nav_altitude_mcp": 35008, "nav_altitude_fms": 35008,
         "nav_heading": 136.41, "lat": 51.380636, "lon": 0.488815, "nic": 7, "rc": 371,
         "seen_pos": 0.39, "version": 2, "nic_baro": 1, "nac_p": 8, "nac_v": 1, "sil": 3,
         "sil_type": "perhour", "gva": 1, "sda": 2, "alert": 0, "spi": 0, "mlat": [], "tisb": [],
         "messages": 31308987, "seen": 0.2, "rssi": -12.7, "dst": 5.44},
        {"hex": "3e2bcd", "type": "adsb_icao", "flight": "AWU504E ", "r": "D-IHUB", "t": "C25A",
         "alt_baro": 5825, "alt_geom": 6225, "gs": 257.6, "ias": 244, "tas": 266, "mach": 0.408,
         "wd": 166, "ws": 10, "oat": 7, "tat": 16, "track": 186.46, "track_rate": -0.03,
         "roll": -0.18, "mag_heading": 184.92, "true_heading": 185.72, "baro_rate": 32,
         "geom_rate": 0, "squawk": "2037", "emergency": "none", "category": "A1", "nav_qnh": 1020,
         "nav_altitude_mcp": 6016, "nav_heading": 184.92, "lat": 51.419174, "lon": 0.727473,
         "nic": 8, "rc": 186, "seen_pos": 0.221, "version": 2, "nic_baro": 1, "nac_p": 10,
         "nac_v": 1, "sil": 3, "sil_type": "perhour", "gva": 2, "sda": 2, "alert": 0, "spi": 0,
         "mlat": [], "tisb": [], "messages": 5724763, "seen": 0, "rssi": -5.5, "dst": 10.6},
        {"hex": "40796c", "type": "adsb_icao", "flight": "TOM7NT  ", "r": "G-TUMN", "t": "B38M",
         "alt_baro": 14375, "alt_geom": 14950, "gs": 344.1, "ias": 277, "tas": 342, "mach": 0.54,
         "wd": 183, "ws": 16, "oat": -9, "tat": 6, "track": 83.66, "track_rate": 0.03, "roll": 0,
         "mag_heading": 85.25, "true_heading": 86.07, "baro_rate": 2432, "geom_rate": 2432,
         "squawk": "3441", "emergency": "none", "category": "A3", "nav_qnh": 1013.6,
         "nav_altitude_mcp": 27008, "nav_altitude_fms": 27008, "nav_heading": 85.08,
         "lat": 51.207733, "lon": 0.736307, "nic": 8, "rc": 186, "seen_pos": 0, "version": 2,
         "nic_baro": 1, "nac_p": 10, "nac_v": 2, "sil": 3, "sil_type": "perhour", "gva": 2,
         "sda": 2, "alert": 0, "spi": 0, "mlat": [], "tisb": [], "messages": 19732262, "seen": 0,
         "rssi": -18.8, "dst": 18.88},
        {"hex": "4058c7", "type": "mlat", "flight": "GZAAP   ", "r": "G-ZAAP", "t": "CRUZ",
         "alt_baro": 300, "gs": 50, "track": 54, "baro_rate": 2, "squawk": "4575", "lat": 51.538891,
         "lon": 0.76194, "nic": 0, "rc": 0, "seen_pos": 1.95, "alert": 0, "spi": 0,
         "mlat": ["gs", "track", "baro_rate", "lat", "lon", "nic", "rc"], "tisb": [],
         "messages": 198847, "seen": 0.8, "rssi": -5.4, "dst": 12.2},
        {"hex": "77058e", "type": "adsb_icao", "flight": "ALK503  ", "r": "4R-ALN", "t": "A333",
         "alt_baro": 14100, "alt_geom": 14750, "gs": 373, "ias": 307, "tas": 376, "mach": 0.596,
         "wd": 321, "ws": 5, "oat": -11, "tat": 8, "track": 270.61, "track_rate": 0, "roll": 0,
         "mag_heading": 270.35, "true_heading": 271.15, "baro_rate": -1856, "geom_rate": -1856,
         "squawk": "3260", "emergency": "none", "category": "A5", "nav_qnh": 1013.6,
         "nav_altitude_mcp": 8000, "lat": 51.643295, "lon": 0.780549, "nic": 8, "rc": 186,
         "seen_pos": 0.123, "version": 2, "nic_baro": 1, "nac_p": 9, "nac_v": 1, "sil": 3,
         "sil_type": "perhour", "gva": 2, "sda": 2, "alert": 0, "spi": 0, "mlat": [], "tisb": [],
         "messages": 11755558, "seen": 0, "rssi": -19.9, "dst": 16.02}], "total": 9,
        "now": 1654367538288, "ctime": 1654367542448, "ptime": 184}


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
        assert "'' is an invalid latitude value. Must be a float between -90 and 90." \
               in str(exc_info.value)

    def test_invalid_latitudes(self, generate_empty_adsb_config):
        """Test impossible latitudes < -90 or > 90 raising an exception"""
        generate_empty_adsb_config['ADSB']['cooldown'] = "10"
        generate_empty_adsb_config['ADSB']['adsb_interval'] = "10"
        generate_empty_adsb_config['ADSB']['lat'] = str(random.uniform(90.01, 999999))
        with pytest.raises(ValueError) as exc_info:
            airspotbot.adsbget.Spotter(generate_empty_adsb_config, valid_watchlist)
        assert "is an invalid latitude value. Must be a float between -90 and 90." \
               in str(exc_info.value)
        generate_empty_adsb_config['ADSB']['lat'] = str(random.uniform(-90.01, -999999))
        with pytest.raises(ValueError) as exc_info:
            airspotbot.adsbget.Spotter(generate_empty_adsb_config, valid_watchlist)
        assert "is an invalid latitude value. Must be a float between -90 and 90." \
               in str(exc_info.value)

    def test_empty_longitude(self, generate_empty_adsb_config):
        generate_empty_adsb_config['ADSB']['cooldown'] = "10"
        generate_empty_adsb_config['ADSB']['adsb_interval'] = "10"
        generate_empty_adsb_config['ADSB']['lat'] = str(random.uniform(-90, 90))
        with pytest.raises(ValueError) as exc_info:
            airspotbot.adsbget.Spotter(generate_empty_adsb_config, valid_watchlist)
        assert "'' is an invalid longitude value. Must be a float between -180 and 180." \
               in str(exc_info.value)

    def test_invalid_longitudes(self, generate_empty_adsb_config):
        """Test impossible longitudes < -180 or > 180 raising an exception"""
        generate_empty_adsb_config['ADSB']['cooldown'] = "10"
        generate_empty_adsb_config['ADSB']['adsb_interval'] = "10"
        generate_empty_adsb_config['ADSB']['lat'] = str(random.uniform(-90, 90))
        generate_empty_adsb_config['ADSB']['long'] = str(random.uniform(180.01, 999999))
        with pytest.raises(ValueError) as exc_info:
            airspotbot.adsbget.Spotter(generate_empty_adsb_config, valid_watchlist)
        assert "is an invalid longitude value. Must be a float between -180 and 180." \
               in str(exc_info.value)
        generate_empty_adsb_config['ADSB']['long'] = str(random.uniform(-180.01, -999999))
        with pytest.raises(ValueError) as exc_info:
            airspotbot.adsbget.Spotter(generate_empty_adsb_config, valid_watchlist)
        assert "is an invalid longitude value. Must be a float between -180 and 180." \
               in str(exc_info.value)

    def test_invalid_radii(self, generate_empty_adsb_config):
        """Test invalid radii raising an exception"""
        generate_empty_adsb_config['ADSB']['cooldown'] = "10"
        generate_empty_adsb_config['ADSB']['adsb_interval'] = "10"
        generate_empty_adsb_config['ADSB']['lat'] = str(random.uniform(-90, 90))
        generate_empty_adsb_config['ADSB']['long'] = str(random.uniform(-180, 180))
        # try 5 different invalid radii and make sure they raise the correct exception
        for _ in range(0, 5):
            invalid_radius = 1
            while invalid_radius in range(1, 251):
                invalid_radius = random.randint(0, 9999)
            with pytest.raises(ValueError) as exc_info:
                airspotbot.adsbget.Spotter(generate_empty_adsb_config, valid_watchlist)
            assert "Error in configuration file: radius value must be an integer between 1 and 250" \
                   in str(exc_info.value)


class TestWatchlistImport:
    """Tests import of watchlist.csv"""

    def test_invalid_watchlist_file(self, generate_valid_adsb_config, caplog):
        """Test exception thrown when bogus watchlist file is read"""
        test_spotter = airspotbot.adsbget.Spotter(generate_valid_adsb_config, invalid_watchlist)
        logging_output = caplog.text
        assert "Error reading row 1 from ./tests/invalid_watchlist.csv, please check the " \
               "watchlist file. This error is usually caused by missing columns in a row." \
               in logging_output
        assert len(test_spotter.watchlist_ia) == 0
        assert len(test_spotter.watchlist_rn) == 0
        assert len(test_spotter.watchlist_tc) == 0

    def test_missing_watchlist_file(self, generate_valid_adsb_config, caplog):
        """Test that warning message is generated when watchlist file is missing"""
        test_spotter = airspotbot.adsbget.Spotter(generate_valid_adsb_config, "foo.csv")
        logging_output = caplog.text
        assert "Watchlist file not found at foo.csv. Aircraft will only be spotted based on " \
               "rules in asb.config." \
               in logging_output
        assert len(test_spotter.watchlist_ia) == 0
        assert len(test_spotter.watchlist_rn) == 0
        assert len(test_spotter.watchlist_tc) == 0

    def test_watchlist_length(self, generate_spotter):
        """Test whether the correct number of watchlist entries were imported"""
        spots = generate_spotter
        assert len(spots.watchlist_rn) + len(spots.watchlist_tc) + len(spots.watchlist_ia) == 6

    def test_rn_watchlist_length(self, generate_spotter):
        """Test registration number watchlist length"""
        spots = generate_spotter
        assert len(spots.watchlist_rn) == 2

    def test_ia_watchlist_length(self, generate_spotter):
        """Test ICAO hex code watchlist length"""
        spots = generate_spotter
        assert len(spots.watchlist_ia) == 1

    def test_tc_watchlist_length(self, generate_spotter):
        """Test type code watchlist length"""
        spots = generate_spotter
        assert len(spots.watchlist_tc) == 3

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


class TestADSBxCall:
    """Test functions that call the ADSBx API,
    using requests-mock to simulate various API responses"""

    def test_api_unavailable(self, requests_mock, generate_spotter, caplog):
        """Make sure correct error log is generated when API request times out"""
        spots = generate_spotter
        # set up the mocker so it returns a ConnectTimeout
        requests_mock.get(spots.url, exc=requests.exceptions.ConnectTimeout)
        spots.check_spots()
        # test that the expected message appears in the log
        assert "Error with ADSB Exchange API request" in caplog.text

    def test_no_aircraft(self, requests_mock, generate_spotter, caplog):
        spots = generate_spotter
        no_aircraft_json = {'ac': None, 'total': 0, 'ctime': 1602380366877, 'ptime': 42}
        requests_mock.get(spots.url, json=no_aircraft_json, status_code=200)
        caplog.set_level(logging.DEBUG)
        spots.check_spots()
        assert "API request appears successful" in caplog.text
        assert "No aircraft detected in spotting area" in caplog.text

    def test_bad_keys(self, requests_mock, generate_spotter, caplog, unexpected_adsbx_json):
        """Test that API response logic fails gracefully when keys are missing/malformed"""
        spots = generate_spotter
        requests_mock.get(spots.url, json=unexpected_adsbx_json, status_code=200)
        caplog.set_level(logging.DEBUG)
        spots.check_spots()
        assert "Key error when parsing aircraft returned from API, skipping" in caplog.text
        assert "D-IENE" in caplog.text

    def test_type_spotted(self, requests_mock, generate_spotter, sample_adsbx_json):
        """test whether aircraft of a certain type code in watchlist will be spotted"""
        spots = generate_spotter
        requests_mock.get(spots.url, json=sample_adsbx_json, status_code=200)
        spots.check_spots()
        assert len([p for p in spots.spot_queue if p['type'] == 'C25A']) == 2

    def test_watchlist_image(self, requests_mock, generate_spotter, sample_adsbx_json):
        """Test that image path is assigned from watchlist"""
        spots = generate_spotter
        requests_mock.get(spots.url, json=sample_adsbx_json, status_code=200)
        spots.check_spots()
        for i in [p['img'] for p in spots.spot_queue if p['type'] == 'C25A']:
            assert i == 'test.png'

    def test_grounded(self, requests_mock, generate_spotter, sample_adsbx_json):
        """test whether aircraft of a certain type code in watchlist will be spotted"""
        spots = generate_spotter
        requests_mock.get(spots.url, json=sample_adsbx_json, status_code=200)
        spots.check_spots()
        assert '4058c7' not in [p['icao'] for p in spots.spot_queue]

    def test_rn_spotted(self, requests_mock, generate_spotter, sample_adsbx_json):
        """test whether aircraft with reg number in watchlist is spotted"""
        spots = generate_spotter
        requests_mock.get(spots.url, json=sample_adsbx_json, status_code=200)
        spots.check_spots()
        assert '4R-ALN' in [p['reg'] for p in spots.spot_queue]

    def test_mil_spotted(self, requests_mock, generate_spotter, sample_adsbx_json):
        """Test whether an aircraft flagged as mil by ADSBx will be spotted"""
        spots = generate_spotter
        requests_mock.get(spots.url, json=sample_adsbx_json, status_code=200)
        spots.check_spots()
        assert '407941' in [p['icao'] for p in spots.spot_queue]

    def test_interesting_spotted(self, requests_mock, generate_spotter, sample_adsbx_json):
        """Test whether an aircraft flagged as interesting by ADSBx will be spotted"""
        spots = generate_spotter
        requests_mock.get(spots.url, json=sample_adsbx_json, status_code=200)
        spots.check_spots()
        assert '407536' in [p['icao'] for p in spots.spot_queue]

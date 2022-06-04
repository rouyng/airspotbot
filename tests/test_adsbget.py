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
                                "radius": str(random.choice((1, 5, 10, 25, 100, 250))),
                                "adsb_interval": str(random.randint(1, 20)),
                                "cooldown": str(random.randint(1, 20)),
                                "spot_unknown": "y",
                                "spot_mil": "y",
                                "spot_interesting": "y",
                                "adsb_api_key": ''.join(random.choices(string.ascii_letters + string.digits, k=16))}
    return dummy_config


@pytest.fixture
def generate_spotter(generate_valid_adsb_config, scope="module"):
    return airspotbot.adsbget.Spotter(generate_valid_adsb_config, valid_watchlist)


@pytest.fixture
def sample_adsbx_json():
    """A sample JSON response from the ADSBx API showing some busy airspace"""
    return {'ac':
            [
                {'postime': '1602439568508',
                 'icao': 'A12986',
                 'reg': 'N174RF',
                 'type': 'C414',
                 'wtc': '1', 'spd': '0', 'altt': '0', 'alt': '300', 'galt': '380', 'talt': '',
                 'lat': '32.811687', 'lon': '-117.137686', 'vsit': '0', 'vsi': '', 'trkh': '0',
                 'ttrk': '', 'trak': '', 'sqk': '1200', 'call': 'N174RF', 'gnd': '1', 'trt': '5',
                 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '6.05'},
                {'postime': '1602439570493', 'icao': 'A6FC66', 'reg': 'N5495D', 'type': 'C172',
                 'wtc': '1', 'spd': '49.7', 'altt': '0', 'alt': '300', 'galt': '380', 'talt': '',
                 'lat': '32.814905', 'lon': '-117.140322', 'vsit': '1', 'vsi': '0', 'trkh': '0',
                 'ttrk': '', 'trak': '295', 'sqk': '1200', 'call': 'N5495D', 'gnd': '0', 'trt': '2',
                 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '6.22'},
                {'postime': '1602439569723', 'icao': 'AAFA92', 'reg': 'N8060U', 'type': 'P28A',
                 'wtc': '1', 'spd': '90.3', 'altt': '0', 'alt': '2200', 'galt': '2289', 'talt': '',
                 'lat': '32.779495', 'lon': '-117.052679', 'vsit': '1', 'vsi': '-576', 'trkh': '0',
                 'ttrk': '', 'trak': '291.4', 'sqk': '1200', 'call': 'N8060U', 'gnd': '0',
                 'trt': '2', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '6.69'},
                {'postime': '1602439568699', 'icao': 'A321DF', 'reg': 'N3001T', 'type': 'P28A',
                 'wtc': '1', 'spd': '104.8', 'altt': '0', 'alt': '3400', 'galt': '3489', 'talt': '',
                 'lat': '32.787532', 'lon': '-116.938701', 'vsit': '1', 'vsi': '128', 'trkh': '0',
                 'ttrk': '', 'trak': '110.7', 'sqk': '1200', 'call': 'N3001T', 'gnd': '0',
                 'trt': '2', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '11.98'},
                {'postime': '1602439568696', 'icao': 'A8E87B', 'reg': 'N673SP', 'type': 'C172',
                 'wtc': '1', 'spd': '92', 'altt': '0', 'alt': '6900', 'galt': '6989', 'talt': '',
                 'lat': '32.840555', 'lon': '-116.706082', 'vsit': '0', 'vsi': '512', 'trkh': '0',
                 'ttrk': '', 'trak': '88.8', 'sqk': '1370', 'call': 'N673SP', 'gnd': '0',
                 'trt': '2', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '24.09'},
                {'postime': '1602439569417', 'icao': 'A67A47', 'reg': 'N5161U', 'type': 'C206',
                 'wtc': '1', 'spd': '100', 'altt': '0', 'alt': '7275', 'galt': '7355', 'talt': '',
                 'lat': '32.563989', 'lon': '-117.173337', 'vsit': '1', 'vsi': '448', 'trkh': '0',
                 'ttrk': '', 'trak': '178.9', 'sqk': '4224', 'call': 'N5161U', 'gnd': '0',
                 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '8.94'},
                {'postime': '1602439568503', 'icao': 'A40A17', 'reg': 'N36BL', 'type': 'LJ31',
                 'wtc': '2', 'spd': '0', 'altt': '0', 'alt': '300', 'galt': '389', 'talt': '',
                 'lat': '32.821644', 'lon': '-116.970875', 'vsit': '0', 'vsi': '', 'trkh': '0',
                 'ttrk': '', 'trak': '', 'sqk': '1440', 'call': 'N36BL', 'gnd': '1', 'trt': '5',
                 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '11.52'},
                {'postime': '1602439569571', 'icao': 'A54819', 'reg': 'N43983', 'type': 'P28A',
                 'wtc': '1', 'spd': '7', 'altt': '0', 'alt': '300', 'galt': '380', 'talt': '',
                 'lat': '32.812408', 'lon': '-117.135681', 'vsit': '1', 'vsi': '0', 'trkh': '0',
                 'ttrk': '', 'trak': '90', 'sqk': '1200', 'call': 'N43983', 'gnd': '0', 'trt': '5',
                 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '6.11'},
                {'postime': '1602439569135', 'icao': 'ABC07B', 'reg': 'N8563Z', 'type': 'B738',
                 'wtc': '2', 'spd': '212.3', 'altt': '0', 'alt': '1925', 'galt': '2005',
                 'talt': '23008', 'lat': '32.74704', 'lon': '-117.248071', 'vsit': '0',
                 'vsi': '1088', 'trkh': '0', 'ttrk': '102.7', 'trak': '285', 'sqk': '2046',
                 'call': 'SWA1322', 'gnd': '0', 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0',
                 'sat': '0', 'opicao': 'SWA', 'cou': 'United States', 'mil': '0', 'interested': '0',
                 'from': 'CMH Port Columbus United States',
                 'to': 'PVD Theodore Francis Green State Providence United States', 'dst': '4.96'},
                {'postime': '1602439568370', 'icao': 'AB540D', 'reg': 'N829UA', 'type': 'A319',
                 'wtc': '2', 'spd': '51.5', 'altt': '0', 'alt': '-25', 'galt': '55', 'talt': '',
                 'lat': '32.730526', 'lon': '-117.177182', 'vsit': '0', 'vsi': '', 'trkh': '1',
                 'ttrk': '', 'trak': '286.9', 'sqk': '7240', 'call': 'UAL2475', 'gnd': '1',
                 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': 'UAL',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '1.43'},
                {'postime': '1602439570701', 'icao': 'A06651', 'reg': 'N125AM', 'type': 'RV10',
                 'wtc': '1', 'spd': '155.1', 'altt': '0', 'alt': '2175', 'galt': '2255', 'talt': '',
                 'lat': '32.815231', 'lon': '-117.103888', 'vsit': '1', 'vsi': '448', 'trkh': '0',
                 'ttrk': '', 'trak': '125', 'sqk': '1200', 'call': 'N125AM', 'gnd': '0', 'trt': '5',
                 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '6.76'},
                {'postime': '1602439569129', 'icao': 'A98012', 'reg': 'N711DC', 'type': 'C170',
                 'wtc': '1', 'spd': '7.1', 'altt': '0', 'alt': '325', 'galt': '414', 'talt': '',
                 'lat': '32.827242', 'lon': '-116.964989', 'vsit': '1', 'vsi': '0', 'trkh': '0',
                 'ttrk': '', 'trak': '8.1', 'sqk': '1200', 'call': 'N711DC', 'gnd': '0', 'trt': '5',
                 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '1', 'dst': '11.96'},
                {'postime': '1602439568505', 'icao': 'A4CA8C', 'reg': 'N408CA', 'type': 'P28A',
                 'wtc': '1', 'spd': '107.5', 'altt': '0', 'alt': '3825', 'galt': '3905',
                 'talt': '3008', 'lat': '32.708533', 'lon': '-117.221487', 'vsit': '0',
                 'vsi': '-320', 'trkh': '0', 'ttrk': '', 'trak': '185.3', 'sqk': '5214',
                 'call': 'N408CA', 'gnd': '0', 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0',
                 'sat': '0', 'opicao': '', 'cou': 'United States', 'mil': '0', 'interested': '0',
                 'dst': '3.18'},
                {'postime': '1602439570700', 'icao': 'A956CC', 'reg': '', 'type': '', 'wtc': '0',
                 'spd': '0', 'altt': '0', 'alt': '350', 'galt': '430', 'talt': '',
                 'lat': '32.811893', 'lon': '-117.131232', 'vsit': '0', 'vsi': '', 'trkh': '1',
                 'ttrk': '', 'trak': '306.6', 'sqk': '0264', 'call': 'N700YZ', 'gnd': '1',
                 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '6.13'},
                {'postime': '1602439568820', 'icao': 'AC2320', 'reg': 'N881SD', 'type': 'AS50',
                 'wtc': '1', 'spd': '59', 'altt': '0', 'alt': '2275', 'galt': '2355', 'talt': '',
                 'lat': '32.834747', 'lon': '-117.088275', 'vsit': '1', 'vsi': '0', 'trkh': '0',
                 'ttrk': '', 'trak': '51.2', 'sqk': '4212', 'call': 'N881SD', 'gnd': '0',
                 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '8.15'},
                {'postime': '1602439570332', 'icao': 'A31FB5', 'reg': 'N300DZ', 'type': 'DHC6',
                 'wtc': '1', 'spd': '166', 'altt': '0', 'alt': '4250', 'galt': '4330', 'talt': '',
                 'lat': '32.606827', 'lon': '-116.862231', 'vsit': '1', 'vsi': '-2880', 'trkh': '0',
                 'ttrk': '', 'trak': '90.3', 'sqk': '4221', 'call': 'N300DZ', 'gnd': '0',
                 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '16.26'},
                {'postime': '1602439568501', 'icao': 'A61A28', 'reg': 'N4922D', 'type': 'C172',
                 'wtc': '1', 'spd': '97.5', 'altt': '0', 'alt': '4475', 'galt': '4546', 'talt': '',
                 'lat': '33.064332', 'lon': '-117.327034', 'vsit': '0', 'vsi': '-64', 'trkh': '0',
                 'ttrk': '', 'trak': '334.5', 'sqk': '0204', 'call': 'N4922D', 'gnd': '0',
                 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '22.75'},
                {'postime': '1602439570200', 'icao': 'A48315', 'reg': 'N390DA', 'type': 'B738',
                 'wtc': '2', 'spd': '512.2', 'altt': '0', 'alt': '26025', 'galt': '26035',
                 'talt': '39008', 'lat': '32.925839', 'lon': '-117.402593', 'vsit': '1',
                 'vsi': '960', 'trkh': '0', 'ttrk': '125.9', 'trak': '136.9', 'sqk': '7375',
                 'call': 'DAL1805', 'gnd': '0', 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0',
                 'sat': '0', 'opicao': 'DAL', 'cou': 'United States', 'mil': '0', 'interested': '0',
                 'from': 'ATL Hartsfield Jackson Atlanta United States',
                 'to': 'YVR Vancouver Canada', 'dst': '17.75'},
                {'postime': '1602439569132', 'icao': 'A36968', 'reg': 'N319MW', 'type': 'B407',
                 'wtc': '1', 'spd': '116.9', 'altt': '0', 'alt': '1700', 'galt': '1789', 'talt': '',
                 'lat': '33.082767', 'lon': '-117.063642', 'vsit': '1', 'vsi': '-384', 'trkh': '0',
                 'ttrk': '', 'trak': '165.1', 'sqk': '1200', 'call': 'N319MW', 'gnd': '0',
                 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '22.73'},
                {'postime': '1602439570681', 'icao': 'A65ED4', 'reg': 'N5098E', 'type': 'C172',
                 'wtc': '1', 'spd': '89.3', 'altt': '0', 'alt': '4475', 'galt': '4546', 'talt': '',
                 'lat': '33.101715', 'lon': '-117.299048', 'vsit': '1', 'vsi': '448', 'trkh': '0',
                 'ttrk': '', 'trak': '99.7', 'sqk': '1200', 'call': 'N5098E', 'gnd': '0',
                 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '24.4'},
                {'postime': '1602439568508', 'icao': 'ABACEB', 'reg': 'N851VA', 'type': 'A320',
                 'wtc': '2', 'spd': '481.8', 'altt': '0', 'alt': '29075', 'galt': '29065',
                 'talt': '36992', 'lat': '32.455353', 'lon': '-116.844598', 'vsit': '1',
                 'vsi': '352', 'trkh': '0', 'ttrk': '', 'trak': '133.1', 'sqk': '1354',
                 'call': 'ASA220', 'gnd': '0', 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0',
                 'sat': '0', 'opicao': 'ASA', 'cou': 'United States', 'mil': '0', 'interested': '0',
                 'from': 'SFO San Francisco United States', 'to': 'ORD Chicago OHare United States',
                 'dst': '22.14'},
                {'postime': '1602439569272', 'icao': 'A6D50B', 'reg': 'N5396E', 'type': 'C172',
                 'wtc': '1', 'spd': '93.4', 'altt': '0', 'alt': '800', 'galt': '871', 'talt': '',
                 'lat': '32.834783', 'lon': '-117.300969', 'vsit': '1', 'vsi': '192', 'trkh': '0',
                 'ttrk': '', 'trak': '5.5', 'sqk': '1200', 'call': 'N5396E', 'gnd': '0', 'trt': '2',
                 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '10.27'},
                {'postime': '1602439569288', 'icao': 'A9D70D', 'reg': 'N733JW', 'type': 'C172',
                 'wtc': '1', 'spd': '67.4', 'altt': '0', 'alt': '2000', 'galt': '2089', 'talt': '',
                 'lat': '33.015701', 'lon': '-116.895026', 'vsit': '1', 'vsi': '0', 'trkh': '0',
                 'ttrk': '', 'trak': '32.3', 'sqk': '1200', 'call': 'N733JW', 'gnd': '0',
                 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '22.53'},
                {'postime': '1602439569571', 'icao': 'A4F488', 'reg': 'N4182T', 'type': 'C172',
                 'wtc': '1', 'spd': '97.8', 'altt': '0', 'alt': '1000', 'galt': '1080', 'talt': '',
                 'lat': '32.81309', 'lon': '-117.09918', 'vsit': '1', 'vsi': '-448', 'trkh': '0',
                 'ttrk': '', 'trak': '196', 'sqk': '1200', 'call': 'N4182T', 'gnd': '0', 'trt': '5',
                 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '6.74'},
                {'postime': '1602439569418', 'icao': 'A336DF', 'reg': 'N306NY', 'type': 'B738',
                 'wtc': '2', 'spd': '2.2', 'altt': '0', 'alt': '-50', 'galt': '30', 'talt': '',
                 'lat': '32.735045', 'lon': '-117.202737', 'vsit': '0', 'vsi': '', 'trkh': '1',
                 'ttrk': '', 'trak': '109.7', 'sqk': '1341', 'call': 'AAL1064', 'gnd': '1',
                 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': 'AAL',
                 'cou': 'United States', 'mil': '0', 'interested': '0',
                 'from': 'DFW Dallas Fort Worth Dallas-Fort Worth United States',
                 'to': 'DFW Dallas Fort Worth Dallas-Fort Worth United States', 'dst': '2.6'},
                {'postime': '1602439570330', 'icao': 'A6E8AE', 'reg': 'N544VL', 'type': 'A20N',
                 'wtc': '2', 'spd': '131.2', 'altt': '0', 'alt': '1675', 'galt': '1785',
                 'talt': '6016', 'lat': '32.515202', 'lon': '-116.880798', 'vsit': '0',
                 'vsi': '-704', 'trkh': '0', 'ttrk': '0', 'trak': '293.8', 'sqk': '6302',
                 'call': 'VOI501', 'gnd': '0', 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0',
                 'sat': '0', 'opicao': 'VOI', 'cou': 'United States', 'mil': '0', 'interested': '0',
                 'from': 'PBC Hermanos Serdán Puebla Mexico',
                 'to': 'TIJ General Abelardo L Rodríguez Tijuana Mexico', 'dst': '18.37'},
                {'postime': '1602439570474', 'icao': 'AC259F', 'reg': 'N882DS', 'type': 'DA40',
                 'wtc': '1', 'spd': '0', 'altt': '0', 'alt': '350', 'galt': '430', 'talt': '672',
                 'lat': '32.811756', 'lon': '-117.131314', 'vsit': '1', 'vsi': '128', 'trkh': '1',
                 'ttrk': '', 'trak': '306.6', 'sqk': '4627', 'call': 'N882DS', 'gnd': '1',
                 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '6.12'},
                {'postime': '1602439570703', 'icao': 'A08588', 'reg': 'N1324E', 'type': 'C172',
                 'wtc': '1', 'spd': '12.2', 'altt': '0', 'alt': '300', 'galt': '380', 'talt': '',
                 'lat': '32.813152', 'lon': '-117.137686', 'vsit': '1', 'vsi': '0', 'trkh': '0',
                 'ttrk': '', 'trak': '106.9', 'sqk': '1200', 'call': 'N1324E', 'gnd': '1',
                 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '6.13'},
                {'postime': '1602439570329', 'icao': 'A5523E', 'reg': 'N442CA', 'type': 'P28A',
                 'wtc': '1', 'spd': '89.7', 'altt': '0', 'alt': '1325', 'galt': '1405',
                 'talt': '1504', 'lat': '32.580231', 'lon': '-116.963306', 'vsit': '1',
                 'vsi': '-192', 'trkh': '0', 'ttrk': '', 'trak': '97', 'sqk': '1200',
                 'call': 'N442CA', 'gnd': '0', 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0',
                 'sat': '0', 'opicao': '', 'cou': 'United States', 'mil': '0', 'interested': '0',
                 'dst': '12.66'},
                {'postime': '1602439569129', 'icao': 'A9E5D2', 'reg': 'N737HY', 'type': 'C172',
                 'wtc': '1', 'spd': '63.1', 'altt': '0', 'alt': '350', 'galt': '430', 'talt': '',
                 'lat': '32.816209', 'lon': '-117.139818', 'vsit': '1', 'vsi': '128', 'trkh': '0',
                 'ttrk': '', 'trak': '295.3', 'sqk': '1200', 'call': 'N737HY', 'gnd': '0',
                 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '6.3'},
                {'postime': '1602439568355', 'icao': 'A959E3', 'reg': 'N701SP', 'type': 'C172',
                 'wtc': '1', 'spd': '102', 'altt': '0', 'alt': '3300', 'galt': '3389', 'talt': '',
                 'lat': '32.808574', 'lon': '-116.856079', 'vsit': '1', 'vsi': '-256', 'trkh': '0',
                 'ttrk': '', 'trak': '245.7', 'sqk': '1200', 'call': 'N701SP', 'gnd': '0',
                 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '16.32'},
                {'postime': '1602439570684', 'icao': 'A1D0D8', 'reg': 'N216LT', 'type': 'C172',
                 'wtc': '1', 'spd': '70.2', 'altt': '0', 'alt': '1000', 'galt': '1089', 'talt': '',
                 'lat': '32.820398', 'lon': '-116.938084', 'vsit': '1', 'vsi': '-704', 'trkh': '0',
                 'ttrk': '', 'trak': '280.7', 'sqk': '1200', 'call': 'N216LT', 'gnd': '0',
                 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '12.88'},
                {'postime': '1602439568822', 'icao': 'A19555', 'reg': 'N2007E', 'type': 'BE76',
                 'wtc': '1', 'spd': '98', 'altt': '0', 'alt': '5100', 'galt': '5189', 'talt': '',
                 'lat': '32.816162', 'lon': '-116.800543', 'vsit': '1', 'vsi': '-1600', 'trkh': '0',
                 'ttrk': '', 'trak': '268.8', 'sqk': '1200', 'call': 'N2007E', 'gnd': '0',
                 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '19.11'},
                {'postime': '1602439569134', 'icao': 'A5F55C', 'reg': 'N483SP', 'type': 'C172',
                 'wtc': '1', 'spd': '115.7', 'altt': '0', 'alt': '5900', 'galt': '5989', 'talt': '',
                 'lat': '32.949463', 'lon': '-116.92348', 'vsit': '1', 'vsi': '128', 'trkh': '0',
                 'ttrk': '', 'trak': '123', 'sqk': '5266', 'call': 'N483SP', 'gnd': '0', 'trt': '5',
                 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '18.52'},
                {'postime': '1602439568964', 'icao': 'A47408', 'reg': 'N38603', 'type': 'P28A',
                 'wtc': '1', 'spd': '68', 'altt': '0', 'alt': '600', 'galt': '680', 'talt': '',
                 'lat': '32.8089', 'lon': '-117.121208', 'vsit': '1', 'vsi': '-704', 'trkh': '0',
                 'ttrk': '', 'trak': '296.2', 'sqk': '1200', 'call': 'N38603', 'gnd': '1',
                 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '6.09'},
                {'postime': '1602439568508', 'icao': 'A4B7D3', 'reg': 'N403AN', 'type': 'A21N',
                 'wtc': '2', 'spd': '2.8', 'altt': '0', 'alt': '-50', 'galt': '30', 'talt': '',
                 'lat': '32.733559', 'lon': '-117.202505', 'vsit': '0', 'vsi': '', 'trkh': '1',
                 'ttrk': '', 'trak': '137.8', 'sqk': '1323', 'call': 'AAL438', 'gnd': '1',
                 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': 'AAL',
                 'cou': 'United States', 'mil': '0', 'interested': '0',
                 'from': 'PHX Phoenix Sky Harbor United States',
                 'to': 'PHX Phoenix Sky Harbor United States', 'dst': '2.55'},
                {'postime': '1602439568354', 'icao': 'A129B0', 'reg': 'N174SY', 'type': 'E170',
                 'wtc': '2', 'spd': '315.4', 'altt': '0', 'alt': '11200', 'galt': '11280',
                 'talt': '6016', 'lat': '32.995422', 'lon': '-117.330634', 'vsit': '0',
                 'vsi': '-1664', 'trkh': '0', 'ttrk': '128', 'trak': '135.3', 'sqk': '3333',
                 'call': 'SKW3354', 'gnd': '0', 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0',
                 'sat': '0', 'opicao': 'SKW', 'cou': 'United States', 'mil': '0', 'interested': '0',
                 'from': 'SFO San Francisco United States',
                 'to': 'MSP Minneapolis-St Paul InternationalWold-Chamberlain Minneapolis United States',
                 'dst': '19.06'},
                {'postime': '1602439570181', 'icao': 'A3B6B6', 'reg': 'N3386E', 'type': 'C172',
                 'wtc': '1', 'spd': '101.6', 'altt': '0', 'alt': '4350', 'galt': '4430',
                 'talt': '4512', 'lat': '32.732461', 'lon': '-116.857649', 'vsit': '1',
                 'vsi': '-64', 'trkh': '0', 'ttrk': '', 'trak': '280.2', 'sqk': '0241',
                 'call': 'N3386E', 'gnd': '0', 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0',
                 'sat': '0', 'opicao': '', 'cou': 'United States', 'mil': '0', 'interested': '0',
                 'dst': '15.24'},
                {'postime': '1602439570336', 'icao': 'AA4138', 'reg': 'N76WW', 'type': 'PA18',
                 'wtc': '1', 'spd': '39.5', 'altt': '0', 'alt': '500', 'galt': '571', 'talt': '',
                 'lat': '33.080978', 'lon': '-117.315143', 'vsit': '1', 'vsi': '64', 'trkh': '0',
                 'ttrk': '', 'trak': '171.3', 'sqk': '1200', 'call': 'ADS6', 'gnd': '0', 'trt': '5',
                 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '23.47'},
                {'postime': '1602439570198', 'icao': 'AD8A80', 'reg': 'N97154', 'type': 'C172',
                 'wtc': '1', 'spd': '88.9', 'altt': '0', 'alt': '1400', 'galt': '1471', 'talt': '',
                 'lat': '33.092468', 'lon': '-117.268396', 'vsit': '1', 'vsi': '-384', 'trkh': '0',
                 'ttrk': '', 'trak': '251', 'sqk': '1200', 'call': 'N97154', 'gnd': '0', 'trt': '5',
                 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '23.46'},
                {'postime': '1602439568505', 'icao': 'A43CE3', 'reg': 'N372TA', 'type': 'C172',
                 'wtc': '1', 'spd': '88.1', 'altt': '0', 'alt': '2600', 'galt': '2680', 'talt': '',
                 'lat': '32.807271', 'lon': '-117.068799', 'vsit': '1', 'vsi': '640', 'trkh': '0',
                 'ttrk': '', 'trak': '116.3', 'sqk': '5225', 'call': 'N372TA', 'gnd': '0',
                 'trt': '2', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '7.28'},
                {'postime': '1602439568819', 'icao': 'A1A0FC', 'reg': 'N204BD', 'type': 'DHC6',
                 'wtc': '1', 'spd': '103.3', 'altt': '0', 'alt': '9000', 'galt': '9080', 'talt': '',
                 'lat': '32.59192', 'lon': '-116.881415', 'vsit': '1', 'vsi': '1216', 'trkh': '0',
                 'ttrk': '', 'trak': '94.4', 'sqk': '4223', 'call': 'N204BD', 'gnd': '0',
                 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '15.76'},
                {'postime': '1602439570335', 'icao': 'A0BCE6', 'reg': 'N147CC', 'type': 'P28T',
                 'wtc': '1', 'spd': '148.1', 'altt': '0', 'alt': '2875', 'galt': '2955',
                 'talt': '672', 'lat': '32.764618', 'lon': '-117.009503', 'vsit': '1',
                 'vsi': '-1152', 'trkh': '0', 'ttrk': '', 'trak': '295.2', 'sqk': '3355',
                 'call': 'N147CC', 'gnd': '0', 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0',
                 'sat': '0', 'opicao': '', 'cou': 'United States', 'mil': '0', 'interested': '0',
                 'dst': '8.16'},
                {'postime': '1602439569414', 'icao': 'ABC5E3', 'reg': 'N858JL', 'type': 'GALX',
                 'wtc': '2', 'spd': '201.9', 'altt': '0', 'alt': '3650', 'galt': '3730', 'talt': '',
                 'lat': '32.686933', 'lon': '-116.995818', 'vsit': '1', 'vsi': '-1408', 'trkh': '0',
                 'ttrk': '', 'trak': '286.1', 'sqk': '2234', 'call': 'N858JL', 'gnd': '0',
                 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '1', 'interested': '0', 'dst': '8.37'},
                {'postime': '1602439569727', 'icao': 'A7A59F', 'reg': 'N592JB', 'type': 'A320',
                 'wtc': '2', 'spd': '0', 'altt': '0', 'alt': '-50', 'galt': '30', 'talt': '2496',
                 'lat': '32.733753', 'lon': '-117.198561', 'vsit': '0', 'vsi': '-64', 'trkh': '1',
                 'ttrk': '0', 'trak': '177.2', 'sqk': '2032', 'call': 'JBU530', 'gnd': '1',
                 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': 'JBU',
                 'cou': 'United States', 'mil': '0', 'interested': '0',
                 'from': 'SAN San Diego United States',
                 'to': 'FLL Fort Lauderdale Hollywood United States', 'dst': '2.38'},
                {'postime': '1602439569133', 'icao': 'A0FAF3', 'reg': 'N162UW', 'type': 'A321',
                 'wtc': '2', 'spd': '15.5', 'altt': '0', 'alt': '-25', 'galt': '55', 'talt': '',
                 'lat': '32.733706', 'lon': '-117.194581', 'vsit': '0', 'vsi': '', 'trkh': '1',
                 'ttrk': '', 'trak': '106.9', 'sqk': '1045', 'call': 'AAL639', 'gnd': '1',
                 'trt': '5', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': 'AAL',
                 'cou': 'United States', 'mil': '0', 'interested': '0',
                 'from': 'CLT Charlotte Douglas United States',
                 'to': 'CLT Charlotte Douglas United States', 'dst': '2.21'}], 'total': 46,
            'ctime': 1602439574290, 'ptime': 109}


@pytest.fixture
def unexpected_adsbx_json():
    """A sample JSON response from the ADSBx API with some missing keys"""
    return {'ac':
            [
                {'postime': '1602439568508',
                 'icao': 'A12986',
                 'reg': 'N174RF',
                 'type': 'C414',
                 'wtc': '1', 'spd': '0', 'altt': '0', 'alt': '300', 'galt': '380', 'talt': '',
                 'lat': '32.811687', 'lon': '-117.137686', 'vsit': '0', 'vsi': '', 'trkh': '0',
                 'ttrk': '', 'trak': '', 'sqk': '1200', 'call': 'N174RF', 'gnd': '1', 'trt': '5',
                 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '6.05'},
                {'postime': '1602439570493', 'icao': 'A6FC66', 'reg': 'N5495D', 'type': 'C172',
                 'wtc': '1', 'spd': '49.7', 'altt': '0', 'alt': '300', 'galt': '380', 'talt': '',
                 'lat': '32.814905', 'lon': '-117.140322', 'vsit': '1', 'vsi': '0', 'trkh': '0',
                 'ttrk': '', 'trak': '295', 'sqk': '1200', 'call': 'N5495D', 'gnd': '0', 'trt': '2',
                 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'blah': '0', 'foo': '0', 'dst': '6.22'},
                {'postime': '1602439569723', 'icao': 'AAFA92', 'reg': 'N8060U', 'type': 'P28A',
                 'wtc': '1', 'spd': '90.3', 'altt': '0', 'alt': '2200', 'galt': '2289', 'talt': '',
                 'lat': '32.779495', 'lon': '-117.052679', 'vsit': '1', 'vsi': '-576', 'trkh': '0',
                 'ttrk': '', 'trak': '291.4', 'sqk': '1200', 'call': 'N8060U', 'gnd': '0',
                 'trt': '2', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '6.69'},
                {'postime': '1602439568699', 'fuzz': 'A321DF', 'reg': 'N3001T', 'type': 'P28A',
                 'wtc': '1', 'spd': '104.8', 'altt': '0', 'alt': '3400', 'galt': '3489', 'talt': '',
                 'lat': '32.787532', 'lon': '-116.938701', 'vsit': '1', 'vsi': '128', 'trkh': '0',
                 'ttrk': '', 'trak': '110.7', 'sqk': '1200', 'call': 'N3001T', 'gnd': '0',
                 'trt': '2', 'pos': '1', 'mlat': '0', 'tisb': '0', 'sat': '0', 'opicao': '',
                 'cou': 'United States', 'mil': '0', 'interested': '0', 'dst': '11.98'}
            ]
            }


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
            while invalid_radius in range(1, 251):
                invalid_radius = random.randint(0, 9999)
            with pytest.raises(ValueError) as exc_info:
                airspotbot.adsbget.Spotter(generate_empty_adsb_config, valid_watchlist)
            assert "Error in configuration file: radius value must be an integer between 1 and 250"\
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
        assert "1602439570493" in caplog.text

    def test_type_spotted(self, requests_mock, generate_spotter, sample_adsbx_json):
        """test whether aircraft of a certain type code in watchlist will be spotted"""
        spots = generate_spotter
        requests_mock.get(spots.url, json=sample_adsbx_json, status_code=200)
        spots.check_spots()
        assert len([p for p in spots.spot_queue if p['type'] == 'P28A']) == 5

    def test_watchlist_image(self, requests_mock, generate_spotter, sample_adsbx_json):
        """Test that image path is assigned from watchlist"""
        spots = generate_spotter
        requests_mock.get(spots.url, json=sample_adsbx_json, status_code=200)
        spots.check_spots()
        for i in [p['img'] for p in spots.spot_queue if p['type'] == 'P28A']:
            assert i == 'test.png'

    def test_grounded(self, requests_mock, generate_spotter, sample_adsbx_json):
        """test whether aircraft of a certain type code in watchlist will be spotted"""
        spots = generate_spotter
        requests_mock.get(spots.url, json=sample_adsbx_json, status_code=200)
        spots.check_spots()
        assert 'A47408' not in [p['icao'] for p in spots.spot_queue]

    def test_rn_spotted(self, requests_mock, generate_spotter, sample_adsbx_json):
        """test whether aircraft with reg number in watchlist is spotted"""
        spots = generate_spotter
        requests_mock.get(spots.url, json=sample_adsbx_json, status_code=200)
        spots.check_spots()
        assert 'N174SY' in [p['reg'] for p in spots.spot_queue]

    def test_mil_spotted(self, requests_mock, generate_spotter, sample_adsbx_json):
        """Test whether an aircraft flagged as mil by ADSBx will be spotted"""
        spots = generate_spotter
        requests_mock.get(spots.url, json=sample_adsbx_json, status_code=200)
        spots.check_spots()
        assert 'ABC5E3' in [p['icao'] for p in spots.spot_queue]

    def test_interesting_spotted(self, requests_mock, generate_spotter, sample_adsbx_json):
        """Test whether an aircraft flagged as interesting by ADSBx will be spotted"""
        spots = generate_spotter
        requests_mock.get(spots.url, json=sample_adsbx_json, status_code=200)
        spots.check_spots()
        assert 'A98012' in [p['icao'] for p in spots.spot_queue]

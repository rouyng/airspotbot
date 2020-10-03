"""
This module contains functionality to provide human-readable location information given latitude/longitude coordinates.
This is used by the main airspotbot package to provide location descriptions in tweets of spotted aircraft.

Based on settings read from the airspotbot config file, the Locator.get_location_description() method will return
a manually-specified string, a nicely formatted string of latitude/longitude coordinates, or a description of the nearby
area and/or points of interest. This last option is provided by a requests to the Pelias reverse geocoding API endpoint.
For more information on this Pelias endpoint, see https://github.com/pelias/documentation/blob/master/reverse.md
"""

import configparser
import logging
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%d-%b-%y %H:%M:%S')


class Locator:
    """Class for generating location descriptions"""
    def __init__(self, config_file_path):
        self.config_file_path = config_file_path
        self.location_type = 'MANUAL'
        self.location_manual_description = ''
        self.pelias_host = ''
        self.pelias_port = 0
        self.pelias_url = ''
        self.pelias_valid_layers = ('venue',
                                    'address',
                                    'street',
                                    'country',
                                    'macroregion',
                                    'region',
                                    'macrocounty',
                                    'county',
                                    'locality',
                                    'localadmin',
                                    'borough',
                                    'neighbourhood',
                                    'coarse')
        self.pelias_point_layer = ''
        self.pelias_area_layer = ''
        self._read_location_config()

    def _read_location_config(self):
        """Read configuration values from file and check whether values are sane"""
        logging.info(f'Loading location data configuration from {self.config_file_path}')
        parser = configparser.ConfigParser()
        parser.read(self.config_file_path)  # read config file at path
        try:
            self.location_type = str(parser.get('LOCATION', 'location_type')).upper()
            assert self.location_type != ''  # check location type is not blank
            assert self.location_type in ('MANUAL', 'COORDINATE', 'PELIAS')  # check for valid location type
        except (configparser.NoOptionError, configparser.NoSectionError, AssertionError):
            logging.warning(f"Location type is not set in {self.config_file_path}, defaulting to coordinate. Valid "
                            f"options are 'manual', 'coordinate', or 'pelias'")
            self.location_type = 'COORDINATE'
        if self.location_type == 'MANUAL':
            try:
                self.location_manual_description = str(parser.get('LOCATION', 'location_description'))
                assert self.location_manual_description != ''  # check location type is not blank
            except (configparser.NoOptionError, configparser.NoSectionError, AssertionError):
                logging.warning(f"Location type is set to manual, but location_description is not set in {self.config_file_path}. Reverting location type to coordinates")
                self.location_type = 'COORDINATE'
        elif self.location_type == 'PELIAS':
            # if location type is PELIAS, configure and test pelias host
            # first, read host url/IP from config file
            try:
                self.pelias_host = str(parser.get('LOCATION', 'pelias_host'))
                assert self.pelias_host != ''
            except (configparser.NoOptionError, configparser.NoSectionError, AssertionError) as e:
                logging.error(f'pelias is selected as the location type, but pelias_host is not set in {self.config_file_path}. Please enter a url/IP address of a valid pelias instance')
                raise configparser.NoOptionError from e
            # read pelias API port from config file
            try:
                self.pelias_port = int(parser.get('LOCATION', 'pelias_port'))
                assert self.pelias_port != 0
            except (configparser.NoOptionError, configparser.NoSectionError, AssertionError) as e:
                logging.error(f'Pelias port is not set in {self.config_file_path}')
                raise configparser.NoOptionError from e
            # construct a url to test the API
            # uses an arbitrary location and just checks that the API response looks like it is in the correct format
            # there is NO check to see whether the pelias host has geolocation data for the lat/longitude used by ASB
            pelias_test_url = f'{self.pelias_host}:{self.pelias_port}/v1/reverse?point.lat=51.5081124&point.lon=-0.0759493'
            # make sure we can connect to the pelias host over http
            try:
                logging.info(f"Testing Pelias API at {pelias_test_url}")
                test_result = requests.get(pelias_test_url)
                test_result.raise_for_status()
                # once we know we can connect to the host, make sure the response looks like it should
                try:
                    result_keys = test_result.json().keys()
                    assert 'geocoding' in result_keys
                    assert 'type' in result_keys
                    assert 'features' in result_keys
                    logging.info(f'Pelias API at {self.pelias_host}:{self.pelias_port} appears to be functional')
                except AssertionError:
                    logging.error('Pelias API response was not as expected, reverting location type to coordinates')
                    self.location_type = 'COORDINATES'
            except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
                logging.error('Error connecting to Pelias API, reverting location type to coordinates')
                logging.error(e)
                self.location_type = 'COORDINATES'
            # read pelias layers to use from file- see README.md and https://github.com/pelias/documentation/blob/master/reverse.md
            # first, the area layer
            try:
                self.pelias_area_layer = str(parser.get('LOCATION', 'pelias_area_layer'))
                assert self.pelias_area_layer != ''
            except (configparser.NoOptionError, configparser.NoSectionError, AssertionError):
                logging.warning(f'Pelias area layer is not set in {self.config_file_path}.')
                self.pelias_area_layer = None
            try:
                assert self.pelias_area_layer in self.pelias_valid_layers
            except AssertionError:
                logging.warning(f'"{self.pelias_area_layer}" is not a valid pelias layer type. See https://github.com/pelias/documentation/blob/master/reverse.md for supported layers.')
                self.pelias_area_layer = None
            # second, the point layer
            try:
                self.pelias_point_layer = str(parser.get('LOCATION', 'pelias_point_layer'))
                assert self.pelias_point_layer != ''
            except (configparser.NoOptionError, configparser.NoSectionError, AssertionError):
                logging.warning(f'Pelias point layer is not set in {self.config_file_path}.')
                self.pelias_point_layer = None
            try:
                assert self.pelias_point_layer in self.pelias_valid_layers
            except AssertionError:
                logging.warning(f'"{self.pelias_point_layer}" is not a valid pelias layer type. See https://github.com/pelias/documentation/blob/master/reverse.md for supported layers.')
                self.pelias_point_layer = None

    def get_location_description(self, lat, long):
        """Return a human-readable location description, based on settings in config file"""
        coord_string = str(round(float(lat), 4)) + ', ' + str(round(float(long), 4))
        if self.location_type == 'MANUAL':
            return self.location_manual_description  # return string specified in config file
        if self.location_type == 'PELIAS':
            geocode = self._reverse_geocode(lat, long)
            if geocode['area'] is None and geocode['point'] is None:
                logging.warning("No reverse geocoding results returned, defaulting to coordinate location")
                return f"near {coord_string}"
            if geocode['area'] is None:
                return f"near {geocode['point']}"
            if geocode['point'] is None:
                return f"over {geocode['area']}"
            return f"over {geocode['area']}, near {geocode['point']}"
        return f"near {coord_string}"

    def _reverse_geocode(self, lat, long):
        self.pelias_url = f'{self.pelias_host}:{self.pelias_port}/v1/reverse?point.lat={lat}&point.lon={long}'
        geo_results = {}
        try:
            if self.pelias_point_layer is not None:
                pelias_result = requests.get(self.pelias_url+f"&layers={self.pelias_point_layer}")
                pelias_result.raise_for_status()
                try:
                    point_name = pelias_result.json()["features"][0]["properties"]["name"]
                except (AttributeError, KeyError, IndexError):
                    logging.warning("No point feature found")
                    point_name = None
            else:
                point_name = None
            if self.pelias_area_layer is not None:
                pelias_result = requests.get(self.pelias_url + f"&layers={self.pelias_area_layer}")
                pelias_result.raise_for_status()
                try:
                    area_name = pelias_result.json()["features"][0]["properties"]["name"]
                except (AttributeError, KeyError, IndexError):
                    logging.warning("No area feature found")
                    area_name = None
            else:
                area_name = None
            geo_results['point'] = point_name
            geo_results['area'] = area_name
            return geo_results
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
            logging.error('Error connecting to Pelias API')
            logging.error(e)
            geo_results['point'] = None
            geo_results['area'] = None
        return geo_results

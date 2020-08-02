# this script contains functionality to interface with the Pelias API, to fetch additional location information
# based on the latitude/longitude coordinates of spotted aircraft

import logging
import requests
import configparser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%d-%b-%y %H:%M:%S')


class Locator:
    def __init__(self, config_file_path):
        self.config_file_path = config_file_path
        self.location_type = 'MANUAL'
        self.location_manual_description = ''
        self.pelias_host = ''
        self.pelias_port = 0
        self.pelias_url = ''
        self.read_pelias_config(self.config_file_path)

    def read_pelias_config(self, path):
        logging.info(f'Loading location data configuration from {self.config_file_path}')
        parser = configparser.ConfigParser()
        parser.read(self.config_file_path)  # read config file at path
        try:
            self.location_type = str(parser.get('LOCATION', 'location_type')).upper()
            assert self.location_type != ''  # check location type is not blank
            assert self.location_type in ('MANUAL', 'COORDINATE', 'PELIAS')  # check for valid location type
        except (configparser.NoOptionError, configparser.NoSectionError, AssertionError):
            logging.warning(f"Location type is not set in {self.config_file_path}, defaulting to coordinate")
            self.location_type = 'COORDINATE'
        if self.location_type == 'MANUAL':
            try:
                self.location_manual_description = str(parser.get('LOCATION', 'location_description'))
                assert self.location_manual_description != ''  # check location type is not blank
            except (configparser.NoOptionError, configparser.NoSectionError, AssertionError):
                logging.warning(f"Location type is set to manual, but description is not set in {self.config_file_path}. Reverting location type to coordinates")
                self.location_type = 'COORDINATE'
        elif self.location_type == 'PELIAS':
            # if location type is PELIAS, configure and test pelias host
            # first, read host url/IP from config file
            try:
                self.pelias_host = str(parser.get('LOCATION', 'pelias_host'))
                assert self.pelias_host != ''
            except (configparser.NoOptionError, configparser.NoSectionError, AssertionError):
                logging.error(f'Pelias host is not set in {self.config_file_path}')
                raise configparser.NoOptionError
            # read pelias API port from config file
            try:
                self.pelias_port = int(parser.get('LOCATION', 'pelias_host'))
                assert self.pelias_host != 0
            except (configparser.NoOptionError, configparser.NoSectionError, AssertionError):
                logging.error(f'Pelias port is not set in {self.config_file_path}')
                raise configparser.NoOptionError
            # construct a url to test the API
            # uses an arbitrary location and just checks that the API response looks like it is in the correct format
            pelias_test_url = f'http://{self.pelias_host}:{self.pelias_port}/v1/reverse?point.lat=51.5081124&point.lon=-0.0759493'
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
                    logging.info(f'Pelias API at http://{self.pelias_host}:{self.pelias_port} appears to be functional')
                except AssertionError:
                    logging.error(f'Pelias API response was not as expected, reverting location type to coordinates')
                    self.location_type = 'COORDINATES'
            except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
                logging.error(f'Error connecting to Pelias API, reverting location type to coordinates')
                logging.error(e)
                self.location_type = 'COORDINATES'

    def get_location_description(self, lat, long):
        if self.location_type == 'COORDINATE':
            return str(round(float(lat), 4)) + ', ' + str(round(float(long), 4))
        elif self.location_type == 'MANUAL':
            return self.location_manual_description
        elif self.location_type == 'PELIAS':
            # TODO: function for pelias reverse geocoding
            pass

    def reverse_geocode(self, lat, long):
        pelias_url = f'http://{self.pelias_host}:{self.pelias_port}/v1/reverse?point.lat={lat}&point.lon={long}'
        try:
            pelias_result = requests.get(pelias_url)
            pelias_result.raise_for_status()
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
            logging.error(f'Error connecting to Pelias API, returning coordinates instead of geocoded results')
            logging.error(e)
            return str(round(float(lat), 4)) + ', ' + str(round(float(long), 4))

                

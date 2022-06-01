"""
This module contains functionality to provide human-readable location information given
latitude/longitude coordinates. This is used by the main airspotbot package to provide location
descriptions in tweets of spotted aircraft.

Based on settings read from the airspotbot config file, the Locator.get_location_description()
method will return a manually-specified string, a nicely formatted string of latitude/longitude
coordinates, or a description of the nearby area and/or points of interest. This last option is
provided by either Pelias or 3geonames reverse geocoding API endpoints. For more information on this
Pelias endpoint, see https://github.com/pelias/documentation/blob/master/reverse.md. For more info
on the 3geonames API, see https://3geonames.org/api.
"""

import configparser
import logging
import requests
from time import sleep

logger = logging.getLogger(__name__)


class Locator:
    """Class for generating location descriptions, using either manual description, coordinates,
    pelias reverse geocoder or 3geonames reverse geocoder"""

    def __init__(self, config_parsed):
        """
        Args:
            config_parsed: ConfigParser object, generated from the config/ini file whose path is
             specified as a command line argument when airspotbot is started.
         """
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
        self._validate_location_config(config_parsed)

    def _validate_location_config(self, config_parsed: configparser.ConfigParser):
        """Checks location-related values in ConfigParser object and make sure they are sane

        Args:
            config_parsed: ConfigParser object, generated from the config/ini file whose path is
             specified as a command line argument when airspotbot is started.

        Raises:
            configparser.NoOptionError: This exception is raised if pelias location type is set but
             other necessary options are not.
         """
        try:
            self.location_type = str(config_parsed.get('LOCATION', 'location_type')).upper()
            # check location_type is populated with a valid value
            assert self.location_type != ''
            assert self.location_type in ('MANUAL', 'COORDINATE', 'PELIAS', '3GEONAMES')
        except (configparser.NoOptionError, configparser.NoSectionError, AssertionError):
            logger.warning("Location type is not set in config, defaulting to coordinate. Valid "
                           "options are 'manual', 'coordinate', or 'pelias'")
            self.location_type = 'COORDINATE'
        if self.location_type == 'MANUAL':
            logger.info("Location type set to manual")
            try:
                self.location_manual_description = str(config_parsed.get('LOCATION',
                                                                         'location_description'))
                assert self.location_manual_description != ''  # check location type is not blank
            except (configparser.NoOptionError, configparser.NoSectionError, AssertionError):
                logger.warning("Location type is set to manual, but location_description is not"
                               " set in config file. Reverting location type to coordinates")
                self.location_type = 'COORDINATE'
        elif self.location_type == 'PELIAS':
            logger.info("Location type set to pelias")
            # if location type is PELIAS, configure and test pelias host
            # first, read host url/IP from config file
            try:
                self.pelias_host = str(config_parsed.get('LOCATION', 'pelias_host'))
                assert self.pelias_host != ''
            except (configparser.NoOptionError, configparser.NoSectionError,
                    AssertionError) as config_error:
                logger.error('pelias is selected as the location type, but pelias_host is not set'
                             ' in config file. Please enter a url/IP address of a valid pelias'
                             ' instance')
                raise configparser.NoOptionError("pelias_host", "LOCATION") from config_error
            # read pelias API port from config file
            try:
                self.pelias_port = int(config_parsed.get('LOCATION', 'pelias_port'))
                assert self.pelias_port != 0
            except (configparser.NoOptionError, configparser.NoSectionError, AssertionError,
                    ValueError) as config_error:
                logger.error('Pelias port is not set in config file')
                raise configparser.NoOptionError("pelias_port", "LOCATION") from config_error
            # construct URL to test the API. Uses an arbitrary location and only checks that the
            # API response is in the correct format. There is NO check to see
            # whether the pelias host has geolocation data for the lat/longitude used by ASB.
            pelias_test_url = \
                f'{self.pelias_host}:{self.pelias_port}/v1/reverse?point.lat=51.5081124&' \
                f'point.lon=-0.0759493'
            # make sure we can connect to the pelias host over http
            try:
                logger.info(f"Testing Pelias API at {pelias_test_url}")
                test_result = requests.get(pelias_test_url)
                test_result.raise_for_status()
                # once we know we can connect to the host, make sure the response looks right
                try:
                    result_keys = test_result.json().keys()
                    assert 'geocoding' in result_keys
                    assert 'type' in result_keys
                    assert 'features' in result_keys
                    logger.info(f'Pelias API at {self.pelias_host}:{self.pelias_port} appears'
                                f' to be functional')
                except AssertionError:
                    logger.error('Pelias API response was not as expected, reverting location'
                                 ' type to coordinates')
                    self.location_type = 'COORDINATES'
            except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as conn_err:
                logger.error('Error connecting to Pelias API, reverting location type to'
                             ' coordinates', exc_info=True)
                self.location_type = 'COORDINATES'
            # read pelias layers to use from file- see README.md and
            # https://github.com/pelias/documentation/blob/master/reverse.md
            # first, the area layer
            try:
                self.pelias_area_layer = str(config_parsed.get('LOCATION', 'pelias_area_layer'))
                assert self.pelias_area_layer != ''
            except (configparser.NoOptionError, configparser.NoSectionError, AssertionError):
                logger.warning('Pelias area layer is not set in config file.')
                self.pelias_area_layer = None
            try:
                assert self.pelias_area_layer in self.pelias_valid_layers
            except AssertionError:
                logger.warning(f'"{self.pelias_area_layer}" is not a valid pelias layer type. See'
                               f' https://github.com/pelias/documentation/blob/master/reverse.md'
                               f' for supported layers.')
                self.pelias_area_layer = None
            # second, the point layer
            try:
                self.pelias_point_layer = str(config_parsed.get('LOCATION', 'pelias_point_layer'))
                assert self.pelias_point_layer != ''
            except (configparser.NoOptionError, configparser.NoSectionError, AssertionError):
                logger.warning('Pelias point layer is not set in config file.')
                self.pelias_point_layer = None
            try:
                assert self.pelias_point_layer in self.pelias_valid_layers
            except AssertionError:
                logger.warning(f'"{self.pelias_point_layer}" is not a valid pelias layer type. See'
                               f' https://github.com/pelias/documentation/blob/master/reverse.md'
                               f' for supported layers.')
                self.pelias_point_layer = None
        elif self.location_type == '3GEONAMES':
            logger.info("Location type set to 3geonames")
        elif self.location_type == 'COORDINATE':
            logger.info("Location type set to coordinate")

    def get_location_description(self, latitude_degrees: str, longitude_degrees: str):
        """
        Return a human-readable location description, based on settings in config file. This is
        the public interface for the Locator object after it is instantiated.

        Args:
            latitude_degrees: String representing latitude value in decimal degrees (-90 to 90)
            longitude_degrees: String representing longitude value in decimal degrees (-180 to 180)

        Returns:
            String containing location description of the type set when the Locator object is
             instantiated.
        """
        # TODO: check that latitude_degrees and longitude_degrees are valid, pass to
        #  geocode functions as floats
        coord_string = str(round(float(latitude_degrees), 4)) + ', ' + str(
            round(float(longitude_degrees), 4))
        if self.location_type == 'MANUAL':
            return self.location_manual_description  # return string specified in config file
        elif self.location_type == 'PELIAS':
            geocode = self._reverse_geocode_pelias(latitude_degrees, longitude_degrees)
            if geocode['area'] is None and geocode['point'] is None:
                logger.warning("No reverse geocoding results returned, defaulting to coordinate"
                               " location")
                return f"near {coord_string}"
            if geocode['area'] is None:
                return f"near {geocode['point']}"
            if geocode['point'] is None:
                return f"over {geocode['area']}"
            return f"over {geocode['area']}, near {geocode['point']}"
        elif self.location_type == '3GEONAMES':
            geocode = self._reverse_geocode_geonames(latitude_degrees, longitude_degrees)
            try:
                if geocode['nearest']['name'] != geocode['nearest']['city']:
                    return f"near {geocode['nearest']['name']}, {geocode['nearest']['city']}"
                else:
                    return f"near {geocode['nearest']['name']}"
            except KeyError:
                logger.info("3geonames reverse geocoder did not return place name, trying city")
                try:
                    return f"near {geocode['nearest']['city']}"
                except KeyError:
                    logger.warning("3geonames reverse geocoder did not return name or city, "
                                   "falling back to coordinate string")
            except TypeError:
                logger.warning("Did not receive result from 3geonames reverse geocoder, falling "
                               "back to coordinate string")
        return f"near {coord_string}"

    def _reverse_geocode_pelias(self, latitude_degrees: str, longitude_degrees: str):
        """
        Args:
            latitude_degrees: String representing latitude value in decimal degrees (-90 to 90)
            longitude_degrees: String representing longitude value in decimal degrees (-180 to 180)

        Returns:
            Dictionary with "point" and "area" keys, with values containing either strings of
            human-readable names of the nearest point and area to the specified coordinates, or None
            if the geocoder returns no result.
        """
        self.pelias_url = \
            f'{self.pelias_host}:{self.pelias_port}/v1/reverse?point.lat={latitude_degrees}&point.lon={longitude_degrees}'
        geo_results = {}
        try:
            if self.pelias_point_layer is not None:
                pelias_result = requests.get(self.pelias_url + f"&layers={self.pelias_point_layer}")
                pelias_result.raise_for_status()
                try:
                    point_name = pelias_result.json()["features"][0]["properties"]["name"]
                except (AttributeError, KeyError, IndexError):
                    logger.warning("No point feature found")
                    point_name = None
            else:
                point_name = None
            if self.pelias_area_layer is not None:
                pelias_result = requests.get(self.pelias_url + f"&layers={self.pelias_area_layer}")
                pelias_result.raise_for_status()
                try:
                    area_name = pelias_result.json()["features"][0]["properties"]["name"]
                except (AttributeError, KeyError, IndexError):
                    logger.warning("No area feature found")
                    area_name = None
            else:
                area_name = None
            geo_results['point'] = point_name
            geo_results['area'] = area_name
            return geo_results
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as conn_err:
            logger.error('Error connecting to Pelias API', exc_info=True)
            geo_results['point'] = None
            geo_results['area'] = None
        return geo_results

    @staticmethod
    def _reverse_geocode_geonames(latitude_degrees: str, longitude_degrees: str):
        """
        Fetch geocoding from the free https://3geonames.org/api

        Args:
            latitude_degrees: String representing latitude value in decimal degrees (-90 to 90)
            longitude_degrees: String representing longitude value in decimal degrees (-180 to 180)

        Returns:
            JSON object containing geocoder API response, or None if we cannot connect to the API
        """
        logger.debug(f"Looking up {latitude_degrees}, {longitude_degrees} using 3geonames api")
        sleep(1)  # hardcoded delay to limit rate of requests to this free API
        try:
            response = requests.get(
                f"https://api.3geonames.org/{latitude_degrees},{longitude_degrees}.json", timeout=4)
            return response.json()
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError) as conn_err:
            logger.error("Error connecting to https://api.3geonames.org/", exc_info=True)
            return None
        except requests.exceptions.Timeout as timeout_exc:
            logger.error("Connection to https://api.3geonames.org/ timed out", exc_info=True)
            return None
        except requests.exceptions.JSONDecodeError as json_err:
            # when the API provider limits requests, they return an HTML document rather than
            # the expected JSON response
            logger.error("https://api.3geonames.org/ did not return JSON, "
                         "likely due to rate limiting", exc_info=True)
            return None

    @staticmethod
    def _reverse_geocode_geoapify(latitude_degrees: str, longitude_degrees: str):
        """
        Fetch geocoding from https://www.geoapify.com/reverse-geocoding-api

        Args:
            latitude_degrees: String representing latitude value in decimal degrees (-90 to 90)
            longitude_degrees: String representing longitude value in decimal degrees (-180 to 180)

        Returns:

        """
        # TODO: implement request to geoapify
        pass
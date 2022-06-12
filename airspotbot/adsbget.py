"""This module contains functionality that interfaces with the ADSBx API to pull information
about active aircraft Also contains code to filter valid aircraft spots based on configuration of
asb.config and watchlist.csv """

import logging
from time import time
import configparser
import csv
import requests
from pathlib import Path
from collections import deque

logger = logging.getLogger(__name__)


class AircraftSpot:
    """
    Class for storing individual aircraft spot information fetched from ADSB exchange API. Converts
    string data from API response into correct types and does some sanity checks.

    Args:
            raw_aircraft: Dictionary generated from ADSBX API JSON reply, representing one aircraft
    Raises:
            ValueError: If raw strings returned by the API cannot be coerced into expected types
    """

    def __init__(self, raw_aircraft: dict[str, str]):
        self.hex_code: str = str(raw_aircraft['hex'])  # ICAO transponder hex address
        try:
            self.type_code: str = str(raw_aircraft['t']).strip()  # ICAO type code
        except KeyError:
            self.type_code: str = 'Unknown aircraft type'
        try:
            self.reg: str = str(raw_aircraft['r']).strip()
        except KeyError:
            self.reg: str = 'unknown'
        try:
            if raw_aircraft['alt_baro'] == 'ground':
                self.grounded: bool = True
            else:
                self.grounded: bool = False
                self.altitude_ft: int | None = int(raw_aircraft['alt_baro'])
        except (KeyError, ValueError):
            logger.warning(f"Could not parse altitude for aircraft w/ hex {self.hex_code}")
            self.altitude_ft: int = 0
            self.grounded: bool = False
        if 'dbFlags' in raw_aircraft:
            self.military: bool = bool(int(raw_aircraft['dbFlags']) & 1)
            self.interesting: bool = bool(int(raw_aircraft['dbFlags']) & 2)
        else:
            self.military: bool = False
            self.interesting: bool = False
        try:
            self.coordinates = Coordinates(raw_aircraft['lat'], raw_aircraft['lon'])
        except ValueError as e:
            logger.error(f"Aircraft with hex {self.hex_code} has invalid lat/lon coordinates")
            raise e
        # Create a string describing aircraft speed. Prefer ground speed, then fall back to
        #  true air speed and indicated air speed in that order. If none are reported, describe
        #  speed as unknown.
        for n, k in (("ground", 'gs'), ("true air", 'tas'), ("indicated air", 'ias')):
            try:
                self.speed_string: str = f"{n} speed {raw_aircraft[k]} kts"
                break
            except KeyError:
                continue
        else:
            logger.warning(f"Could not parse speed for aircraft w/ hex {self.hex_code}")
            self.speed_string: str = 'speed unknown'
        try:
            if raw_aircraft['flight'].strip() != self.reg:
                self.callsign: str | None = str(raw_aircraft['flight'].strip())
            else:
                self.callsign: str | None = None
        except KeyError:
            self.callsign: str | None = None
        self.description: str | None = None  # custom text description pulled from watchlist
        self.image_path: Path | None = None  # path to custom image file pulled from watchlist

    def update_from_watchlist(self, search_key: str, watchlist: dict[str, dict[str, str]]):
        """Check watchlist for custom description and image path. If present, update description
        and image path.

        Args:
            search_key: Key used to search watchlist. Can be a registration number, ICAO hex code
                or an ICAO type code
            watchlist: Watchlist dictionary, consisting of keys which can be registration number,
                ICAO hex code or an ICAO type code, and values which are dictionaries containing
                'desc' and 'img' key/value pairs for custom descriptions and image paths.
            """
        if watchlist[search_key]['desc'] != '':
            self.description = watchlist[search_key]['desc']
        image_filename = watchlist[search_key]['img']
        # Check if file exists at path defined by image_path, then update self.image_path
        if image_filename != '':
            full_path = Path("./images/" + image_filename)
            if full_path.is_file():
                self.image_path = full_path
            else:
                logger.error(f"Cannot add image to aircraft with hex {self.hex_code}. "
                             f"No file found at {full_path}.")


class Coordinates:
    """Class for storing latitude/longitude coordinates, with simple sanity checks"""

    def __init__(self, latitude: str, longitude: str):
        try:
            if float(latitude) > 90 or float(latitude) < -90:
                raise ValueError
        except ValueError:
            raise ValueError(f"'{latitude}' is an invalid latitude value. Must "
                             f"be a float between -90 and 90.")
        self.latitude: float = float(latitude)
        try:
            if float(longitude) > 180 or float(longitude) < -180:
                raise ValueError
        except ValueError:
            raise ValueError(f"'{longitude}' is an invalid longitude value. Must "
                                 f"be a float between -180 and 180.")
        self.longitude: float = float(longitude)


class Spotter:
    """Class for fetching active aircraft from ADSBx API and returning those that meet watchlist
    criteria. Requires a ConfigParser object and path to watchlist.csv as arguments.
    """

    def __init__(self, config_parsed: configparser.ConfigParser, watchlist_path: str):
        """
        Args:
            config_parsed: ConfigParser object, generated from the config/ini file whose path is
             specified as a command line argument when airspotbot is started.
            watchlist_path: String containing path to watchlist csv file, specified as a command
             line argument when airspotbot is started.
        """
        self.watchlist_path = watchlist_path
        self.watchlist_rn = {}
        self.watchlist_tc = {}
        self.watchlist_ia = {}
        self.seen = {}
        self.adsb_interval_seconds = 60  # interval to check adsb_exchange
        self.cooldown_seconds = 3600  # cooldown interval (seconds)
        # lat/lon coordinates of center of spot radius
        self.spot_center_coordinates: Coordinates | None = None
        self.radius_nautical_miles = 1  # radius of circle to check for spots (nautical miles)
        self.adsb_api_key = None
        self.spot_queue: deque[AircraftSpot] = deque()
        self.spot_unknown = True  # always spot unknown reg #s
        self.spot_mil = True  # always spot mil-format serial numbers
        self.spot_interesting = True  # always spot aircraft designated "interesting"
        self.url = ""
        self.headers = {}
        self._validate_adsb_config(config_parsed)
        self._read_watchlist()

    def _validate_adsb_config(self, config_parsed: configparser.ConfigParser):
        """
        Checks values in ConfigParser object and make sure they are sane

        Args:
            config_parsed: ConfigParser object, generated from the config/ini file whose path is
            specified when airspotbot is started.
        """
        # TODO: refactor this giant conditional tree to something more maintainable
        try:
            try:
                self.adsb_interval_seconds = int(config_parsed.get('ADSB', 'adsb_interval'))
                logger.debug(f"Setting interval to {self.adsb_interval_seconds}")
            except ValueError as interval_error:
                raise ValueError(
                    "adsb_interval must be an integer value") from interval_error
            try:
                self.cooldown_seconds = int(config_parsed.get('ADSB', 'cooldown'))
                logger.debug(f"Setting interval to {self.cooldown_seconds}")
            except ValueError as cooldown_error:
                raise ValueError(
                    "cooldown must be an integer value") from cooldown_error
            self.spot_center_coordinates = Coordinates(config_parsed.get('ADSB', 'lat'),
                                                       config_parsed.get('ADSB', 'long'))
            logger.debug(f"Set spotting coordinates to: {self.spot_center_coordinates.latitude}, "
                         f"{self.spot_center_coordinates.longitude}")
            try:
                self.radius_nautical_miles = int(config_parsed.get('ADSB', 'radius'))
                if 250 < self.radius_nautical_miles or self.radius_nautical_miles < 1:
                    raise ValueError
                logger.debug(f"Setting radius to {self.radius_nautical_miles}")
            except ValueError as radius_error:
                raise ValueError('Error in configuration file: radius value must be an integer '
                                 'between 1 and 250') from radius_error
            self.adsb_api_key = config_parsed.get('ADSB', 'adsb_api_key').strip()
            logger.debug(f'Setting API key value to {self.adsb_api_key}')
            # create url and headers for RapidAPI request
            logger.debug("Setting api endpoint to rapidapi")
            self.url = f"https://adsbexchange-com1.p.rapidapi.com/v2/" \
                       f"lat/{self.spot_center_coordinates.latitude}/lon/" \
                       f"{self.spot_center_coordinates.longitude}/dist/{self.radius_nautical_miles}/"
            logger.debug(f"API request url: {self.url}")
            self.headers = {
                'X-RapidAPI-Host': "adsbexchange-com1.p.rapidapi.com",
                'X-RapidAPI-Key': self.adsb_api_key
            }
            if config_parsed.get('ADSB', 'spot_unknown').lower() == 'y':
                logger.debug('Set spot_unknown to True')
                self.spot_unknown = True
            elif config_parsed.get('ADSB', 'spot_unknown').lower() == 'n':
                logger.debug('Set spot_unknown to False')
                self.spot_unknown = False
            else:
                raise ValueError()
            if config_parsed.get('ADSB', 'spot_mil').lower() == 'y':
                logger.debug('Set spot_mil to True')
                self.spot_mil = True
            elif config_parsed.get('ADSB', 'spot_mil').lower() == 'n':
                logger.debug('Set spot_mil to False')
                self.spot_mil = False
            else:
                raise ValueError()
            if config_parsed.get('ADSB', 'spot_interesting').lower() == 'y':
                logger.debug('Set spot_interesting to True')
                self.spot_interesting = True
            elif config_parsed.get('ADSB', 'spot_interesting').lower() == 'n':
                logger.debug('Set spot_interesting to False')
                self.spot_interesting = False
            else:
                raise ValueError()
        except (configparser.NoOptionError, configparser.NoSectionError) as config_error:
            logger.critical('Configuration file error, missing section and/or option',
                            exc_info=True)
            raise KeyboardInterrupt

    def _read_watchlist(self):
        """
        Load aircraft to watch from watchlist csv file at self.watchlist_path, populating
        self.watchlist_rn, self.watchlist_tc and self.watchlist_ia dictionaries
        """
        logger.info(f'Loading watchlist from {self.watchlist_path}')
        try:
            with open(self.watchlist_path) as watchlist_file:
                csv_reader = csv.reader(watchlist_file, delimiter=',')
                row_count = 0
                row_error_count = 0
                for row in csv_reader:
                    row_count += 1
                    try:
                        if row[0] == 'Key':
                            # Cell A1 should contain the first cell of the title row
                            # If the expected value of "Key" is present, move to the next row
                            continue
                        if row[1] == 'RN':
                            self.watchlist_rn[row[0]] = {'desc': row[3].strip(),
                                                         'img': row[4].strip()}
                            logger.info(
                                f'Added {row[0]} to reg num watchlist. Description: "{row[3]}",'
                                f' image: {row[4]}')
                        elif row[1] == 'TC':
                            mil_only = bool(row[2].lower() == 'y')
                            self.watchlist_tc[row[0]] = {'desc': row[3].strip(),
                                                         'img': row[4].strip(),
                                                         'mil_only': mil_only}
                            logger.info(
                                f'Added {row[0]} to type code watchlist. Military only: {mil_only} '
                                f'Description: "{row[3]}", image: {row[4]}')
                        elif row[1] == 'IA':
                            self.watchlist_ia[row[0]] = {'desc': row[3].strip(),
                                                         'img': row[4].strip()}
                            logger.info(
                                f'Added {row[0]} to ICAO address watchlist. Description: "{row[3]}", '
                                f'image: {row[4]}')
                        else:
                            # if none of these are true, watchlist file is likely invalid
                            # so raise an exception
                            raise IndexError
                    except IndexError as watchlist_error:
                        row_error_count += 1
                        logger.warning(f"Error reading row {row_count} from {self.watchlist_path}, "
                                       f"please check the watchlist file. This error is usually "
                                       f"caused by missing columns in a row.")
                        continue
                if row_error_count > 0:
                    logger.warning(f"Generated {row_error_count} while reading watchlist file")
        except FileNotFoundError:
            logger.warning(f"Watchlist file not found at {self.watchlist_path}. Aircraft will "
                           f"only be spotted based on rules in asb.config.")
        finally:
            logger.info(
                f'Added {len(self.watchlist_rn) + len(self.watchlist_tc) + len(self.watchlist_ia)}'
                f' entries to the watchlist')

    def _append_craft(self, spotted_aircraft: AircraftSpot):
        """
        Add aircraft to self.spot_queue list and self.seen dictionary. Called when the logic
        in check_spots matches an aircraft seen nearby.

        Args:
            spotted_aircraft: AircraftSpot object, representing a single aircraft
        """
        try:
            hex_code = spotted_aircraft.hex_code
            logger.info(f'Aircraft added to queue. ICAO #: {hex_code}')
            self.spot_queue.append(spotted_aircraft)
            self.seen[hex_code] = time()
        except ValueError:
            logger.warning("Error adding aircraft to queue. Value could not be coerced to expected"
                           "type.", exc_info=True)

    def _check_seen(self):
        """
        Before checking for new spots, this function is run to remove aircraft from the self.seen
        dictionary, so aircraft that loiter longer than the cooldown time will generate new tweets
        """
        del_list = []
        for seen_id, seen_time_seconds in self.seen.items():
            if seen_time_seconds < time() - self.cooldown_seconds:
                logger.debug(f'Removing {seen_id} from seen list, cooldown time exceeded')
                del_list.append(seen_id)
        for item_to_delete in del_list:
            del self.seen[item_to_delete]

    def check_spots(self):
        """
        Check for new spotted aircraft that meet spotting criteria, including both watchlist
        and configurable global spotting rules (such as military or unknown reg. no.).
        Aircraft that meet spotting criteria are passed to self._append_craft function.
        """
        logger.info(
            f'Checking for aircraft via ADSBx API (endpoint: RapidAPI)')
        try:
            response = requests.request("GET", self.url, headers=self.headers,
                                        timeout=4)
            response.raise_for_status()
            logger.debug('API request appears successful')
            aircraft_nearby = response.json()['ac']
            if aircraft_nearby is None:
                # prevent an empty list of spots from creating a TypeError in the next for loop
                logger.info('No aircraft detected in spotting area')
                aircraft_nearby = []
            else:
                logger.info(f'API returned {len(aircraft_nearby)} aircraft in spotting area')
        except (requests.exceptions.HTTPError, requests.exceptions.Timeout,
                AttributeError) as err:
            logger.error('Error with ADSB Exchange API request', exc_info=True)
            aircraft_nearby = []
        self._check_seen()  # clear off aircraft from the seen list if cooldown on them has expired
        for raw_aircraft in aircraft_nearby:
            try:
                logger.debug(
                    f'Received ADSBX data for aircraft w/ hex code {raw_aircraft["hex"]}. '
                    f'Full data: {raw_aircraft}')
                # Attempt to process raw API response into sanitized AircraftSpot
                aircraft = AircraftSpot(raw_aircraft)
            except (ValueError, KeyError):
                logger.error(f"Error processing raw aircraft data, skipping. Raw data: {raw_aircraft}", exc_info=True)
                continue
            # Once an instance of AircraftSpot is successfully created, run through spotting logic
            #  to see if it should be added to the tweet queue
            if aircraft.hex_code in self.seen:
                # if craft icao number is in seen list, do not queue
                logger.debug(f"{aircraft.hex_code} is already spotted, not added to queue")
                continue
            if aircraft.grounded:
                logger.debug(f'{aircraft.hex_code} is grounded, skipping')
                continue
            if aircraft.hex_code in self.watchlist_ia:
                # if the aircraft's ICAO address is on the watchlist, add it to the queue
                logger.debug(f'{aircraft.hex_code} in watchlist, adding to spot queue')
                aircraft.update_from_watchlist(aircraft.hex_code, self.watchlist_ia)
                self._append_craft(aircraft)
            elif aircraft.reg in self.watchlist_rn:
                # if the aircraft's registration number is on the watchlist, add it to the queue
                logger.debug(f'{aircraft.reg} in watchlist, adding to spot queue')
                aircraft.update_from_watchlist(aircraft.reg, self.watchlist_rn)
                self._append_craft(aircraft)
            elif aircraft.type_code in self.watchlist_tc:
                if self.watchlist_tc[aircraft.type_code]['mil_only'] is True and aircraft.military:
                    logger.debug(
                        f'{aircraft.type_code} in watchlist as military-only and this one is '
                        f'military, adding to spot queue')
                    aircraft.update_from_watchlist(aircraft.type_code, self.watchlist_tc)
                    self._append_craft(aircraft)
                elif self.watchlist_tc[aircraft.type_code]['mil_only'] is True and \
                        not aircraft.military:
                    logger.debug(
                        f'{aircraft.type_code} in watchlist as military-only, but this one isn\'t '
                        f'military, not adding to spot queue')
                    continue
                else:
                    logger.debug(
                        f'{aircraft.type_code} in watchlist, adding to spot queue')
                    aircraft.update_from_watchlist(aircraft.type_code, self.watchlist_tc)
                    self._append_craft(aircraft)
            elif aircraft.reg == 'unknown' and self.spot_unknown is True:
                # if there's no registration number and spot_unknown is set, add to tweet queue
                logger.info('Unknown registration number, adding to spot queue')
                self._append_craft(aircraft)
            elif aircraft.military and self.spot_mil is True:
                # if craft is designated military by ADS-B exchange and spot_mil is set,
                # add to tweet queue
                logger.debug(
                    "Aircraft is designated as military, adding to spot queue")
                self._append_craft(aircraft)
            elif aircraft.interesting and self.spot_interesting is True:
                # if craft is designated military by ADS-B exchange and spot_mil is set,
                # add to tweet queue
                logger.debug(
                    "Aircraft is designated as interesting, adding to spot queue")
                self._append_craft(aircraft)
            else:
                # if none of these criteria are met, iterate to next aircraft in the list
                logger.debug(
                    f"{aircraft.hex_code} did not meet any spotting criteria, not added to queue")
                continue

"""This module contains functionality that interfaces with the ADSBx API to pull information
about active aircraft Also contains code to filter valid aircraft spots based on configuration of
asb.config and watchlist.csv """

import logging
from time import time
import configparser
import csv
import requests
from typing import TypedDict

logger = logging.getLogger(__name__)


class Aircraft(TypedDict):
    icao: str  # ICAO hex address
    type: str  # type code
    reg: str  # registration number (or military serial number)
    lat: float  # latitude in decimal degrees
    lon: float  # longitude in decimal degrees
    desc: str  # description from watchlist
    alt: int  # altitude in feet
    spd: int  # speed in knots
    call: str  # callsign or commercial flight number
    img: str  # path to


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
        self.latitude_degrees = 0  # latitude of center of spot radius
        self.longitude_degrees = 0  # longitude of center of spot radius
        self.radius_nautical_miles = 1  # radius of circle to check for spots (nautical miles)
        self.adsb_api_key = None
        self.spot_queue = []
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
            try:
                self.latitude_degrees = float(config_parsed.get('ADSB', 'lat'))
                if not -90 <= self.latitude_degrees <= 90:
                    raise ValueError
                logger.debug(f"Setting latitude to {self.latitude_degrees}")
            except ValueError as latitude_error:
                raise ValueError(
                    "latitude must be a float value >= -90 and <= 90") from latitude_error
            try:
                self.longitude_degrees = float(config_parsed.get('ADSB', 'long'))
                if not -180 <= self.longitude_degrees <= 180:
                    raise ValueError
                logger.debug(f"Setting longitude to {self.longitude_degrees}")
            except ValueError as longitude_error:
                raise ValueError("longitude must be a float value >= -180 and"
                                 " <= 180") from longitude_error
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
                       f"lat/{self.latitude_degrees}/lon/{self.longitude_degrees}/dist/" \
                       f"{self.radius_nautical_miles}/"
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

    def _append_craft(self, aircraft: dict):
        """
        Add aircraft to self.spot_queue list and self.seen dictionary

        Args:
            aircraft: Dictionary generated from ADSBX API JSON reply, representing one aircraft
        """
        try:
            spotted_aircraft = Aircraft(
                icao=str(aircraft['hex']),
                type=str(aircraft['t']),
                reg=str(aircraft['r']),
                lat=float(aircraft['lat']),
                lon=float(aircraft['lon']),
                desc=str(aircraft['desc']),
                alt=int(aircraft['alt_baro']),
                spd=int(aircraft['gs']),
                call=str(aircraft['flight'].strip()),
                img=str(aircraft['img']),
            )
            icao = spotted_aircraft['icao']
            logger.info(f'Aircraft added to queue. ICAO #: {icao}')
            self.spot_queue.append(spotted_aircraft)
            self.seen[icao] = time()
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
            spotted_aircraft = response.json()['ac']
            if spotted_aircraft is None:
                # prevent an empty list of spots from creating a TypeError in the next for loop
                logger.info('No aircraft detected in spotting area')
                spotted_aircraft = []
            else:
                logger.info(f'API returned {len(spotted_aircraft)} aircraft in spotting area')
        except (requests.exceptions.HTTPError, requests.exceptions.Timeout,
                AttributeError) as err:
            logger.error('Error with ADSB Exchange API request', exc_info=True)
            spotted_aircraft = []
        self._check_seen()  # clear off aircraft from the seen list if cooldown on them has expired
        for craft in spotted_aircraft:
            try:
                # This loop checks all spotted aircraft against watchlist and preferences to
                # determine if it should be added to the tweet queue
                # TODO: refactor this giant tree of conditionals to something more maintainable
                logger.debug(
                    f'Spotted aircraft {craft["hex"]}. Full data: {craft}')
                # add reg and type keys w/ empty string if not present
                for k in ('r', 't'):
                    if k not in craft.keys():
                        craft[k] = ''
                for k in ('dbFlags', 'alt_baro'):
                    if k not in craft.keys():
                        craft[k] = 0
                if craft['hex'] in self.seen.keys():
                    # if craft icao number is in seen list, do not queue
                    logger.debug(f"{craft['hex']} is already spotted, not added to queue")
                    continue
                if craft['alt_baro'] == 'ground':
                    logger.debug(f'{craft["hex"]} is grounded, skipping')
                    continue
                if craft['hex'] in self.watchlist_ia.keys():
                    # if the aircraft's ICAO address is on the watchlist, add it to the queue
                    logger.debug(f'{craft["hex"]} in watchlist, adding to spot queue')
                    if self.watchlist_ia[craft['hex']]['desc'] != '':
                        # if there is a description in the watchlist entry for this ICAO address,
                        # add it to the dict
                        craft['desc'] = self.watchlist_ia[craft['hex']]['desc']
                    else:
                        craft['desc'] = ''
                    if self.watchlist_ia[craft['hex']]['img'] != '':
                        craft['img'] = self.watchlist_ia[craft['hex']]['img']
                    else:
                        craft['img'] = ''
                    self._append_craft(craft)
                elif craft['r'] in self.watchlist_rn.keys():
                    logger.debug(f'{craft["r"]} in watchlist, adding to spot queue')
                    # if the aircraft's registration number is on the watchlist, add it to the queue
                    if self.watchlist_rn[craft['r']]['desc'] != '':
                        # if there is a description in the watchlist entry for this reg number,
                        # add it to the dict
                        craft['desc'] = self.watchlist_rn[craft['r']]['desc']
                    else:
                        craft['desc'] = ''
                    if self.watchlist_rn[craft['r']]['img'] != '':
                        craft['img'] = self.watchlist_rn[craft['r']]['img']
                    else:
                        craft['img'] = ''
                    self._append_craft(craft)
                elif craft['t'] in self.watchlist_tc.keys():
                    if self.watchlist_tc[craft['t']]['mil_only'] is True and craft['dbFlags'] & 1:
                        if self.watchlist_tc[craft['t']]['desc'] != '':
                            craft['desc'] = self.watchlist_tc[craft['t']]['desc']
                        else:
                            craft['desc'] = ''
                        if self.watchlist_tc[craft['t']]['img'] != '':
                            craft['img'] = self.watchlist_tc[craft['t']]['img']
                        else:
                            craft['img'] = ''
                        logger.debug(
                            f'{craft["type"]} in watchlist as military-only and mil=1, adding to '
                            f'spot queue')
                        self._append_craft(craft)
                    elif self.watchlist_tc[craft['t']]['mil_only'] is True and \
                            craft['mil'] == '0':
                        logger.debug(
                            f'{craft["type"]} in watchlist as military-only and mil=0, not adding '
                            f'to spot queue')
                        continue
                    else:
                        if self.watchlist_tc[craft['t']]['desc'] != '':
                            craft['desc'] = self.watchlist_tc[craft['t']]['desc']
                        else:
                            craft['desc'] = ''
                        if self.watchlist_tc[craft['t']]['img'] != '':
                            craft['img'] = self.watchlist_tc[craft['t']]['img']
                        else:
                            craft['img'] = ''
                        logger.debug(
                            f'{craft["type"]} in watchlist, adding to spot queue')
                        self._append_craft(craft)
                elif craft['r'] == '' and self.spot_unknown is True:
                    # if there's no registration number and spot_unknown is set, add to tweet queue
                    craft['desc'] = ''
                    craft['img'] = ''
                    logger.info('Unknown registration number, adding to spot queue')
                    self._append_craft(craft)
                elif 'dbFlags' in craft.keys():
                    if craft['dbFlags'] & 1 and self.spot_mil is True:
                        # if craft is designated military by ADS-B exchange and spot_mil is set,
                        # add to tweet queue
                        craft['desc'] = ''
                        craft['img'] = ''
                        logger.debug(
                            "Aircraft is designated as military, adding to spot queue")
                        self._append_craft(craft)
                    elif craft['dbFlags'] & 2 and self.spot_interesting is True:
                        # if craft is designated military by ADS-B exchange and spot_mil is set,
                        # add to tweet queue
                        craft['desc'] = ''
                        craft['img'] = ''
                        logger.debug(
                            "Aircraft is designated as interesting, adding to spot queue")
                        self._append_craft(craft)
                    else:
                        logger.debug(
                            f"{craft['hex']} did not meet any spotting criteria, "
                            f"not added to queue")
                        continue
                else:
                    # if none of these criteria are met, iterate to next aircraft in the list
                    logger.debug(
                        f"{craft['hex']} did not meet any spotting criteria, not added to queue")
                    continue
            except KeyError:
                logger.warning("Key error when parsing aircraft returned from API, skipping",
                               exc_info=True)
                logger.debug(f"Raw json object: {craft}")
                continue

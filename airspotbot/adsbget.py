"""This module contains functionality that interfaces with the ADSBx API to pull information
about active aircraft Also contains code to filter valid aircraft spots based on configuration of
asb.config and watchlist.csv """

import logging
from time import time
import configparser
import csv
import requests

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s: %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')


class Spotter:
    """Class for fetching active aircraft from ADSBx API and returning those that meet watchlist
    criteria. Requires a ConfigParser object and path to watchlist.csv as arguments.
    """

    def __init__(self, config_parsed, watchlist_path):
        self.watchlist_path = watchlist_path
        self.watchlist_rn = {}
        self.watchlist_tc = {}
        self.watchlist_ia = {}
        self.seen = {}
        self.interval = 60  # interval to check adsb_exchange
        self.cooldown = 3600  # cooldown interval (seconds)
        self.latitude = 0  # latitude of center of spot radius
        self.longitude = 0  # longitude of center of spot radius
        self.radius = 1  # radius of circle to check for spots (nautical miles)
        self.adsb_api_key = None
        self.adsb_api_endpoint = None
        self.spot_queue = []
        self.spot_unknown = True  # always spot unknown reg #s
        self.spot_mil = True  # always spot mil-format serial numbers
        self.url = ""
        self.logging_level = "INFO"  # verbosity level of log messages
        self.headers = {}
        self._validate_adsb_config(config_parsed)
        self._read_watchlist()

    def _validate_adsb_config(self, parsed_config):
        """Checks values in ConfigParser object and make sure they are sane"""
        try:
            try:
                self.interval = int(parsed_config.get('ADSB', 'adsb_interval'))
                logging.debug(f"Setting interval to {self.interval}")
            except ValueError as interval_error:
                raise ValueError(
                    "adsb_interval must be an integer value") from interval_error
            try:
                self.cooldown = int(parsed_config.get('ADSB', 'cooldown'))
                logging.debug(f"Setting interval to {self.cooldown}")
            except ValueError as cooldown_error:
                raise ValueError(
                    "cooldown must be an integer value") from cooldown_error
            try:
                self.latitude = float(parsed_config.get('ADSB', 'lat'))
                if not -90 <= self.latitude <= 90:
                    raise ValueError
                logging.debug(f"Setting latitude to {self.latitude}")
            except ValueError as latitude_error:
                raise ValueError(
                    "latitude must be a float value >= -90 and <= 90") from latitude_error
            try:
                self.longitude = float(parsed_config.get('ADSB', 'long'))
                if not -180 <= self.longitude <= 180:
                    raise ValueError
                logging.debug(f"Setting longitude to {self.longitude}")
            except ValueError as longitude_error:
                raise ValueError("longitude must be a float value >= -180 and"
                                 " <= 180") from longitude_error
            try:
                self.radius = int(parsed_config.get('ADSB', 'radius'))
                if self.radius not in (1, 5, 10, 25, 100, 250):
                    raise ValueError
                logging.debug(f"Setting radius to {self.radius}")
            except ValueError as radius_error:
                raise ValueError('Error in configuration file: radius value is'
                                 ' not 1, 5, 10, 25, 100, or 250') from radius_error
            self.adsb_api_endpoint = parsed_config.get('ADSB', 'adsb_api').strip()
            self.adsb_api_key = parsed_config.get('ADSB', 'adsb_api_key').strip()
            logging.debug(f'Setting API key value to {self.adsb_api_key}')
            if self.adsb_api_endpoint == 'rapidapi':
                # create url and headers for RapidAPI request
                logging.debug("Setting api endpoint to rapidapi")
                self.url = f"https://adsbexchange-com1.p.rapidapi.com/json/" \
                           f"lat/{self.latitude}/lon/{self.longitude}/dist/" \
                           f"{self.radius}/"
                logging.debug(f"API request url: {self.url}")
                self.headers = {
                    'x-rapidapi-host': "adsbexchange-com1.p.rapidapi.com",
                    'x-rapidapi-key': self.adsb_api_key
                }
            elif self.adsb_api_endpoint == 'adsbx':
                # create url and headers for ADSBx API request
                logging.debug("Setting api endpoint to adsbx")
                self.url = f"https://adsbexchange.com/api/aircraft/json/lat/" \
                           f"{self.latitude}/lon/{self.longitude}/dist/{self.radius}/"
                logging.debug(f"API request url: {self.url}")
                self.headers = {
                    'api-auth': self.adsb_api_key
                }
            else:
                logging.critical(
                    f"{self.adsb_api_endpoint} is not a valid API endpoint")
                raise Exception('Invalid API endpoint')
            if parsed_config.get('ADSB', 'spot_unknown').lower() == 'y':
                logging.debug('Set spot_unknown to True')
                self.spot_unknown = True
            elif parsed_config.get('ADSB', 'spot_unknown').lower() == 'n':
                logging.debug('Set spot_unknown to False')
                self.spot_unknown = False
            else:
                raise ValueError()
            if parsed_config.get('ADSB', 'spot_mil').lower() == 'y':
                logging.debug('Set spot_mil to True')
                self.spot_mil = True
            elif parsed_config.get('ADSB', 'spot_mil').lower() == 'n':
                logging.debug('Set spot_mil to False')
                self.spot_mil = False
            else:
                raise ValueError()
        except (configparser.NoOptionError, configparser.NoSectionError) as config_error:
            logging.critical(
                f'Configuration file error, missing section and/or option: {config_error}')
            raise config_error

    def _read_watchlist(self):
        """Load aircraft to watch from watchlist csv file"""
        logging.info(f'Loading watchlist from {self.watchlist_path}')
        with open(self.watchlist_path) as watchlist_file:
            csv_reader = csv.reader(watchlist_file, delimiter=',')
            for row in csv_reader:
                try:
                    if row[0] == 'Key':
                        # Cell A1 should be the the first cell of the title row
                        # If the expected value of "Key" is present, move to the next row
                        continue
                    if row[1] == 'RN':
                        self.watchlist_rn[row[0]] = {'desc': row[3].strip(),
                                                     'img': row[4].strip()}
                        logging.info(
                            f'Added {row[0]} to reg num watchlist. Description: "{row[3]}",'
                            f' image: {row[4]}')
                    elif row[1] == 'TC':
                        mil_only = bool(row[2].lower() == 'y')
                        self.watchlist_tc[row[0]] = {'desc': row[3].strip(),
                                                     'img': row[4].strip(),
                                                     'mil_only': mil_only}
                        logging.info(
                            f'Added {row[0]} to type code watchlist. Military only: {mil_only} '
                            f'Description: "{row[3]}", image: {row[4]}')
                    elif row[1] == 'IA':
                        self.watchlist_ia[row[0]] = {'desc': row[3].strip(),
                                                     'img': row[4].strip()}
                        logging.info(
                            f'Added {row[0]} to ICAO address watchlist. Description: "{row[3]}", '
                            f'image: {row[4]}')
                    else:
                        # if none of these are true, watchlist file is likely invalid
                        # so raise an exception
                        raise IndexError
                except IndexError as watchlist_error:
                    raise IndexError(
                        "Error reading watchlist.csv, please check the watchlist file.") \
                        from watchlist_error
            logging.info(
                f'Added {len(self.watchlist_rn) + len(self.watchlist_tc) + len(self.watchlist_ia)}'
                f' entries to the watchlist')

    def _append_craft(self, aircraft):
        """Add aircraft to spot queue and seen list"""
        icao = aircraft['icao']
        logging.info(f'Aircraft added to queue. ICAO #: {icao}')
        self.spot_queue.append(aircraft)
        self.seen[icao] = time()

    def _check_seen(self):
        """Before checking for new spots, this function is run to clear aircraft off the "seen" list
        so aircraft that loiter longer than the cooldown time will generate new tweets
        """
        del_list = []
        for seen_id, seen_time in self.seen.items():
            if seen_time < time() - self.cooldown:
                logging.debug(
                    f'Removing {seen_id} from seen list, cooldown time exceeded')
                del_list.append(seen_id)
        for item_to_delete in del_list:
            del self.seen[item_to_delete]

    def check_spots(self):
        """Check for new spotted aircraft that meet watchlist criteria"""
        logging.info(
            f'Checking for aircraft via ADSBx API (endpoint: {self.adsb_api_endpoint})')
        try:
            response = requests.request("GET", self.url, headers=self.headers,
                                        timeout=4)
            response.raise_for_status()
            logging.debug('API request appears successful')
            spotted_aircraft = response.json()['ac']
            if spotted_aircraft is None:
                # prevent an empty list of spots from creating a TypeError in the next for loop
                logging.info('No aircraft detected in spotting area')
                spotted_aircraft = []
        except (requests.exceptions.HTTPError, requests.exceptions.Timeout,
                AttributeError) as err:
            logging.error(f'Error with API request: {err}')
            spotted_aircraft = []
        self._check_seen()  # clear off aircraft from the seen list if cooldown on them has expired
        for aircraft in spotted_aircraft:
            # This loop checks all spotted aircraft against watchlist and preferences to determine
            # if it should be added to the tweet queue
            craft = dict(aircraft)  # convert json object provided by API to dictionary
            logging.debug(
                f'Spotted aircraft {craft["icao"]}. Full data: {craft}')
            if craft['icao'] in self.seen.keys():
                # if craft icao number is in seen list, do not queue
                logging.debug(f"{craft['icao']} is already spotted, not added to queue")
                continue
            if craft['gnd'] == '1':
                # if craft is on ground, do not queue
                logging.debug(f"{craft['icao']} is on the ground, not added to queue")
                continue
            if craft['icao'] in self.watchlist_ia.keys():
                # if the aircraft's ICAO address is on the watchlist, add it to the queue
                logging.debug(f'{craft["icao"]} in watchlist, adding to spot queue')
                if self.watchlist_ia[craft['icao']]['desc'] != '':
                    # if there is a description in the watchlist entry for this ICAO address,
                    # add it to the dict
                    craft['desc'] = self.watchlist_ia[craft['icao']]['desc']
                else:
                    craft['desc'] = False
                if self.watchlist_ia[craft['icao']]['img'] != '':
                    craft['img'] = self.watchlist_ia[craft['icao']]['img']
                else:
                    craft['img'] = False
                self._append_craft(craft)
            elif craft['reg'] in self.watchlist_rn.keys():
                logging.debug(f'{craft["reg"]} in watchlist, adding to spot queue')
                # if the aircraft's registration number is on the watchlist, add it to the queue
                if self.watchlist_rn[craft['reg']]['desc'] != '':
                    # if there is a description in the watchlist entry for this reg number,
                    # add it to the dict
                    craft['desc'] = self.watchlist_rn[craft['reg']]['desc']
                else:
                    craft['desc'] = False
                if self.watchlist_rn[craft['reg']]['img'] != '':
                    craft['img'] = self.watchlist_rn[craft['reg']]['img']
                else:
                    craft['img'] = False
                self._append_craft(craft)
            elif craft['type'] in self.watchlist_tc.keys():
                if self.watchlist_tc[craft['type']]['mil_only'] is True and \
                        craft['mil'] == '1':
                    if self.watchlist_tc[craft['type']]['desc'] != '':
                        craft['desc'] = self.watchlist_tc[craft['type']]['desc']
                    else:
                        craft['desc'] = False
                    if self.watchlist_tc[craft['type']]['img'] != '':
                        craft['img'] = self.watchlist_tc[craft['type']]['img']
                    else:
                        craft['img'] = False
                    logging.debug(
                        f'{craft["type"]} in watchlist as military-only and mil=1, adding to '
                        f'spot queue')
                    self._append_craft(craft)
                elif self.watchlist_tc[craft['type']]['mil_only'] is True and \
                        craft['mil'] == '0':
                    logging.debug(
                        f'{craft["type"]} in watchlist as military-only and mil=0, not adding to '
                        f'spot queue')
                    continue
                else:
                    if self.watchlist_tc[craft['type']]['desc'] != '':
                        craft['desc'] = self.watchlist_tc[craft['type']]['desc']
                    else:
                        craft['desc'] = False
                    if self.watchlist_tc[craft['type']]['img'] != '':
                        craft['img'] = self.watchlist_tc[craft['type']]['img']
                    else:
                        craft['img'] = False
                    logging.debug(
                        f'{craft["type"]} in watchlist, adding to spot queue')
                    self._append_craft(craft)
            elif craft['reg'] == '' and self.spot_unknown is True:
                # if there's no registration number and spot_unknown is set, add to tweet queue
                craft['desc'] = False
                craft['img'] = False
                logging.info('Unknown registration number, adding to spot queue')
                self._append_craft(craft)
            elif craft['mil'] == '1' and self.spot_mil is True:
                # if craft is designated military by ADS-B exchange and spot_mil is set,
                # add to tweet queue
                craft['desc'] = False
                craft['img'] = False
                logging.debug(
                    "Aircraft is designated as military, adding to spot queue")
                self._append_craft(craft)
            else:
                # if none of these criteria are met, iterate to next aircraft in the spotted list
                logging.debug(
                    f"{craft['icao']} did not meet any spotting critera, not added to queue")
                continue

import logging
from time import time
import requests
import configparser
import csv
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%d-%b-%y %H:%M:%S')


class Spotter:
    def __init__(self, config_file_path, watchlist_path):
        self.config_file_path = config_file_path
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

        self.read_adsb_config()
        self.read_watchlist()

    def read_adsb_config(self):
        logging.info(f'Loading ADSB exchange configuration from {self.config_file_path}')
        parser = configparser.ConfigParser()
        parser.read(self.config_file_path)  # read config file at path
        try:
            self.interval = int(parser.get('ADSB', 'adsb_interval'))
            self.cooldown = int(parser.get('ADSB', 'cooldown'))
            self.latitude = float(parser.get('ADSB', 'lat'))
            self.longitude = float(parser.get('ADSB', 'long'))
            self.adsb_api_endpoint = parser.get('ADSB', 'adsb_api')
            self.adsb_api_key = parser.get('ADSB', 'adsb_api_key')
            self.radius = int(parser.get('ADSB', 'radius'))
            if self.radius not in (1, 5, 10, 25, 100, 250):
                raise ValueError('Error in configuration file: radius value is not 1, 5, 10, 25, 100, or 250')
            if parser.get('ADSB', 'spot_unknown').lower() == 'y':
                self.spot_unknown = True
            elif parser.get('ADSB', 'spot_unknown').lower() == 'n':
                self.spot_unknown = False
            else:
                raise ValueError()
            if parser.get('ADSB', 'spot_mil').lower() == 'y':
                self.spot_mil = True
            elif parser.get('ADSB', 'spot_mil').lower() == 'n':
                self.spot_mil = False
            else:
                raise ValueError()
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            logging.critical(f'Configuration file error: {e}')

    def read_watchlist(self):
        logging.info(f'Loading watchlist from {self.watchlist_path}')
        with open(self.watchlist_path) as watchlist_file:
            csv_reader = csv.reader(watchlist_file, delimiter=',')
            for row in csv_reader:
                if row[0] == 'Key':
                    continue
                else:
                    if row[1] == 'RN':
                        self.watchlist_rn[row[0]] = {'desc': row[3]}
                        logging.info(f'Added {row[0]} to reg num watchlist. Description: "{row[3]}"')
                    elif row[1] == 'TC':
                        if row[2].lower() == 'y':
                            mil_only = True
                        else:
                            mil_only = False
                        self.watchlist_tc[row[0]] = {'desc': row[3], 'mil_only': mil_only}
                        logging.info(f'Added {row[0]} to type code watchlist. Military only: {mil_only} Description: "{row[3]}"')
                    elif row[1] == 'IA':
                        self.watchlist_ia[row[0]] = {'desc': row[3]}
                        logging.info(f'Added {row[0]} to ICAO address watchlist. Description: "{row[3]}"')
            logging.info(f'Added {len(self.watchlist_rn) + len(self.watchlist_tc) + len(self.watchlist_ia)} entries to the watchlist')

    def append_craft(self, aircraft):
        # add aircraft to spot queue and seen list
        icao = aircraft['icao']
        logging.info(f'Aircraft added to queue. ICAO #: {icao}')
        self.spot_queue.append(aircraft)
        self.seen[icao] = time()

    def check_seen(self):
        # before checking for new spots, this function is run to clear aircraft off the "seen" list
        # so aircraft that loiter longer than the cooldown time will generate new tweets
        del_list = []
        for k, t in self.seen.items():
            if t < time() - self.cooldown:
                del_list.append(k)
        for d in del_list:
            del self.seen[d]

    def check_spots(self):
        logging.info('Checking for aircraft via ADSB exchange API')
        if self.adsb_api_endpoint == 'rapidapi':
            url = f"https://adsbexchange-com1.p.rapidapi.com/json/lat/{self.latitude}/lon/{self.longitude}/dist/{self.radius}/"

            headers = {
                'x-rapidapi-host': "adsbexchange-com1.p.rapidapi.com",
                'x-rapidapi-key': self.adsb_api_key
            }
            try:
                response = requests.request("GET", url, headers=headers, timeout=4)
                response.raise_for_status()
            except (requests.exceptions.HTTPError, requests.exceptions.Timeout) as err:
                logging.error(f'Error with ADSBX API request: {err}')
                response = []
            try:
                spotted_aircraft = response.json()['ac']
                self.check_seen()  # clear off aircraft from the seen list if cooldown on them has expired
                for c in spotted_aircraft:
                    # This loop checks all spotted aircraft against your watchlist and preferences to determine
                    # if it should be added to the tweet queue
                    craft = dict(c)  # convert json object provided by API to dictionary
                    if craft['icao'] in self.seen.keys() or craft['gnd'] == '1':
                        # if craft icao number is in seen list, do not queue
                        # if craft is on ground, do not queue
                        continue
                    else:
                        if craft['icao'] in self.watchlist_ia.keys():
                            # if the aircraft's ICAO address is on the watchlist, add it to the queue
                            if self.watchlist_ia[craft['icao']]['desc'] != '':
                                # if there is a description in the watchlist entry for this ICAO address, add it to the dict
                                craft['desc'] = self.watchlist_ia[craft['icao']]['desc']
                            else:
                                craft['desc'] = False
                            self.append_craft(craft)
                        elif craft['reg'] in self.watchlist_rn.keys():
                            # if the aircraft's registration number is on the watchlist, add it to the queue
                            if self.watchlist_rn[craft['reg']]['desc'] != '':
                                # if there is a description in the watchlist entry for this reg number, add it to the dict
                                craft['desc'] = self.watchlist_rn[craft['reg']]['desc']
                            else:
                                craft['desc'] = False
                            self.append_craft(craft)
                        elif craft['type'] in self.watchlist_tc.keys():
                            if self.watchlist_tc[craft['type']]['mil_only'] is True and craft['mil'] == '1':
                                if self.watchlist_tc[craft['type']]['desc'] != '':
                                    craft['desc'] = self.watchlist_tc[craft['type']]['desc']
                                else:
                                    craft['desc'] = False
                                self.append_craft(craft)
                            elif self.watchlist_tc[craft['type']]['mil_only'] is True and craft['mil'] == '0':
                                continue
                            else:
                                if self.watchlist_tc[craft['type']]['desc'] != '':
                                    craft['desc'] = self.watchlist_tc[craft['type']]['desc']
                                else:
                                    craft['desc'] = False
                                self.append_craft(craft)
                        elif craft['reg'] == '' and self.spot_unknown is True:
                            # if there's no registration number and spot_unknown is set, add to tweet queue
                            craft['desc'] = False
                            self.append_craft(craft)
                        elif craft['mil'] == '1' and self.spot_mil is True:
                            # if craft is designated military by ADS-B exchange and spot_mil is set, add to tweet queue
                            craft['desc'] = False
                            self.append_craft(craft)
                        else:
                            # if none of these criteria are met, iterate to next aircraft in the spotted list
                            continue
            except AttributeError as err:
                logging.error(f'Error decoding JSON, likely due to ADSBX API error: {err}')
        elif self.adsb_api_endpoint == 'free':
            # TODO: add support for ADS-B Exchange free endpoint
            logging.critical('ADS-B Exchange free api endpoint is currently not supported. This feature is planned, see README.md')
            raise Exception('Invalid API endpoint')
        else:
            raise Exception('Invalid API endpoint')

import logging
import requests
import configparser



class Spotter:
    def __init__(self, config_file_path):
        self.config_file_path = config_file_path
        self.interval = 60  # interval to check adsb_exchange
        self.cooldown = 3600  # cooldown interval (seconds)
        self.latitude = 0  # latitude of center of spot radius
        self.longitude = 0  # longitude of center of spot radius
        self.radius = 1  # radius of circle to check for spots (nautical miles)
        self.spot_queue = []
        self.spot_unknown = True  # always spot unknown reg #s
        self.spot_mil = True  # always spot mil-format serial numbers
        self.read_adsb_config()

    def read_adsb_config(self):
        # TODO: function for reading and storing variables/keys from asb.config
        parser = configparser.ConfigParser()
        parser.read(self.config_file_path)  # read config file at path
        try:
            self.interval = int(parser.get('ADSB', 'adsb_interval'))
            self.cooldown = int(parser.get('ADSB', 'cooldown'))
            self.latitude = float(parser.get('ADSB', 'lat'))
            self.longitude = float(parser.get('ADSB', 'long'))
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

    def check_spots(self):
        pass
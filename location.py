# this script contains functionality to interface with the Pelias API, to fetch additional location information
# based on the latitude/longitude coordinates of spotted aircraft

import logging
import requests
import configparser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%d-%b-%y %H:%M:%S')

class Locator:
    def __init__(self, config_file_path):
        self.config_file_path = config_file_path
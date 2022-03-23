"""This module contains the class SpotBot, which interfaces with the twitter API to generate
airspotbot's tweets. It also has the main program loop of airspotbot, so executing this module
starts airspotbot. """

import configparser
import logging
from time import sleep, time
import tweepy
from . import adsbget, location
import os.path as path

logger = logging.getLogger("airspotbot")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s',
                              datefmt='%d-%b-%y %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)


class SpotBot:
    """
    Generates formatted tweet text and interfaces with the twitter API.

    simple usage example:

    some_configparser_object = read_config(r"./config/asb.config")
    bot = SpotBot(some_configparser_object)
    spots = adsbget.Spotter(some_configparser_object, 'watchlist.csv')
    while True:
        spots.check_spots()
        spot = spots.spot_queue.pop(0)
        bot.tweet_spot(spot)
        sleep(30)
    """

    def __init__(self, config_parsed: configparser.ConfigParser):
        self.tweet_interval_seconds = 5
        self._consumer_key = None
        self._consumer_secret = None
        self._access_token = None
        self._access_token_secret = None
        self._use_descriptions = False
        self._down_tweet = False
        self._read_logging_config(config_parsed)
        self._validate_twitter_config(config_parsed)
        if self.enable_tweets:
            self._api = self._initialize_twitter_api()
        self._loc = location.Locator(config_parsed)

    def _read_logging_config(self, config_parsed: configparser.ConfigParser):
        """set logging verbosity from parsed config file"""
        try:
            self.logging_level = str(config_parsed.get('MISC', 'logging_level')).upper()
            assert self.logging_level != ''
            assert self.logging_level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
            logger.setLevel(self.logging_level)
            logger.warning(f"Set logging level to {self.logging_level}")
        except (configparser.NoOptionError, configparser.NoSectionError, AssertionError):
            logger.warning("Logging verbosity level is not set in config, defaulting to DEBUG")
            logger.setLevel('DEBUG')

    def _initialize_twitter_api(self):
        """Authenticate to Twitter API, check credentials and connection"""
        logger.info(f'Twitter consumer key: {self._consumer_key}')
        logger.info(f'Twitter consumer secret: {self._consumer_secret}')
        logger.info(f'Twitter access token: {self._access_token}')
        logger.info(f'Twitter access token secret: {self._access_token_secret}')
        auth = tweepy.OAuthHandler(self._consumer_key, self._consumer_secret)
        auth.set_access_token(self._access_token, self._access_token_secret)
        api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
        try:
            # test that authentication worked
            api.verify_credentials()
            logger.info("Authentication OK")
        except tweepy.error.TweepError as tp_error:
            logger.critical('Error during Twitter API authentication', exc_info=True)
            raise KeyboardInterrupt
        logger.info('Twitter API created')
        return api

    def _validate_twitter_config(self, config_parsed: configparser.ConfigParser):
        """Checks values in ConfigParser object and make sure they are sane"""
        try:
            if config_parsed.get('TWITTER', 'enable_tweets') == 'y':
                self.enable_tweets = True
            elif config_parsed.get('TWITTER', 'enable_tweets') == 'n':
                logger.warning("Tweeting disabled in config file")
                self.enable_tweets = False
            else:
                raise ValueError("Bad value in config file for TWITTER/enable_tweets. "
                                 "Must be 'y' or 'n'.")
            self.tweet_interval_seconds = int(config_parsed.get('TWITTER', 'tweet_interval'))
            self._consumer_key = config_parsed.get('TWITTER', 'consumer_key')
            self._consumer_secret = config_parsed.get('TWITTER', 'consumer_secret')
            self._access_token = config_parsed.get('TWITTER', 'access_token')
            self._access_token_secret = config_parsed.get('TWITTER', 'access_token_secret')
            if config_parsed.get('TWITTER', 'use_descriptions').lower() == 'y':
                self._use_descriptions = True
            elif config_parsed.get('TWITTER', 'use_descriptions').lower() == 'n':
                self._use_descriptions = False
            else:
                raise ValueError("Bad value in config file for TWITTER/use_descriptions. "
                                 "Must be 'y' or 'n'.")
            if config_parsed.get('TWITTER', 'down_tweet').lower() == 'y':
                self._down_tweet = True
            elif config_parsed.get('TWITTER', 'down_tweet').lower() == 'n':
                self._down_tweet = False
            else:
                raise ValueError("Bad value in config file for TWITTER/down_tweet. "
                                 "Must be 'y' or 'n'.")
        except configparser.Error as config_error:
            logger.critical('Configuration file error', exc_info=True)
            raise KeyboardInterrupt

    def tweet_spot(self, aircraft: dict):
        """
        Generate tweet based on aircraft data returned in dictionary format from the adsbget
        module's Spotter.spot_queue list of dictionaries.
        """
        icao = aircraft['icao']
        type_code = aircraft['type']
        reg_num = aircraft['reg']
        latitude_degrees = aircraft['lat']
        longitude_degrees = aircraft['lon']
        description = aircraft['desc']
        altitude_feet = aircraft['alt']
        speed_knots = aircraft['spd']
        callsign = aircraft['call']
        link = f'https://globe.adsbexchange.com/?icao={icao}'
        location_description = self._loc.get_location_description(latitude_degrees,
                                                                  longitude_degrees)
        if reg_num.strip() == '':
            reg_num = 'unknown'
        if type_code.strip() == '':
            type_code = 'Unknown aircraft type'
        if callsign == reg_num:
            # if callsign is same as the registration number, ADSBx is not reporting a callsign
            callsign = False
        tweet = f"{description if description else type_code}" \
                f"{', callsign ' + callsign if callsign else ''}, ICAO {icao}, RN {reg_num}, is " \
                f"{location_description}. Altitude {altitude_feet} ft, speed {speed_knots} kt. {link}"
        if aircraft['img']:
            image_path = "images/" + aircraft['img']  # always look for images in images subfolder
            if self.enable_tweets:
                try:
                    # if an image path is specified, upload it
                    logger.debug(f"Uploading image from {image_path}")
                    image = self._api.media_upload(image_path)
                except tweepy.error.TweepError:
                    # if upload fails, handle exception and proceed gracefully without an image
                    logger.warning(f"Error uploading image from {image_path}, check if file exists")
                    image = False
        else:
            image = False
        logger.info(f"Generated tweet: {tweet}")
        if self.enable_tweets:
            logger.info(f'Tweeting: {tweet}')
            try:
                if image:
                    try:
                        self._api.update_status(tweet, media_ids=[image.media_id])
                    except AttributeError as upload_error:
                        # catch an attribute error, in case media upload fails in an unexpected way
                        logger.warning("Attribute error when sending tweet", exc_info=True)
                        self._api.update_status(tweet)
                else:
                    self._api.update_status(tweet)
            except tweepy.error.TweepError as tp_error:
                logger.critical('Error sending tweet', exc_info=True)
                raise KeyboardInterrupt

    def _link_reply(self):
        # TODO: function to reply to to a tweet with a link defined in watchlist.csv
        pass


def run_bot(config_path: str, watchlist_path: str):
    """
    Main program loop of airspotbot. Invoked from __main__.py.

    :param config_path: String containing relative or absolute path to config INI file.
    :param watchlist_path: String containing relative or absolute path to watchlist CSV file.
    :return:
    """

    config = read_config(config_path)
    bot = SpotBot(config)
    spots = adsbget.Spotter(config, watchlist_path)
    bot_time_seconds = time()
    spot_time_seconds = time()
    # check for aircraft and tweet any when bot first starts
    spots.check_spots()
    for _ in range(0, len(spots.spot_queue)):
        spot = spots.spot_queue.pop(0)
        bot.tweet_spot(spot)
    # perpetually loop through checking aircraft spots and tweeting according to interval in config
    while True:
        if time() > spot_time_seconds + spots.adsb_interval_seconds:
            spots.check_spots()
            spot_time_seconds = time()
        elif time() > bot_time_seconds + bot.tweet_interval_seconds:
            for _ in range(0, len(spots.spot_queue)):
                spot = spots.spot_queue.pop(0)
                bot.tweet_spot(spot)
            bot_time_seconds = time()
        else:
            sleep(1)


def read_config(config_path: str) -> configparser.ConfigParser:
    """
    Parse configuration INI file and return a ConfigParser object.

    :param config_path: String containing relative or absolute path to config INI file.
    :return: ConfigParser object
    """

    logger.info(f'Loading configuration from {config_path}')
    if path.isfile(config_path):
        parser = configparser.ConfigParser()
        try:
            parser.read(config_path)  # read config file at path
            return parser
        except configparser.Error as config_err:
            logger.critical("Error when reading config file", exc_info=True)
            raise KeyboardInterrupt
    else:
        logger.critical(f"Configuration file not found at {config_path}")
        raise KeyboardInterrupt

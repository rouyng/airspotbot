"""
This module contains the class SpotBot, which interfaces with the Twitter API to generate
airspotbot's tweets. It also has the main program loop of airspotbot, so executing this module
starts airspotbot.
"""

import configparser
import logging
from time import sleep, time
import tweepy
from . import adsbget, location, screenshot
import os.path as path
from io import BytesIO
from pathlib import Path

logger = logging.getLogger("airspotbot")



class SpotBot:
    """
    Generates formatted tweet text and interfaces with the Twitter API using tweepy.

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

    def __init__(self,
                 config_parsed: configparser.ConfigParser,
                 user_agent: str,
                 enable_tweets: bool):
        """
        Args:
            config_parsed: ConfigParser object, generated from the config/ini file whose path is
             specified as a command line argument when airspotbot is started.
            user_agent: User agent string used in API requests
        """
        self.user_agent = user_agent
        self.tweet_interval_seconds = 5
        self._consumer_key = None
        self._consumer_secret = None
        self._access_token = None
        self._access_token_secret = None
        self._use_descriptions = False
        self._enable_tweets = enable_tweets
        self._read_logging_config(config_parsed)
        self._validate_twitter_config(config_parsed)
        if self._enable_tweets:
            self._client = self._initialize_twitter_api()
            # instantiate v1.1 api instance only for uploading media
            self._v1_api = self._initialize_twitter_api_v1()
        else:
            logger.warning("Tweeting is disabled, did not create Twitter API connection")
        if self.enable_screenshot:
            self.screenshotter = screenshot.Screenshotter(self.zoom_level)
        self._loc = location.Locator(config_parsed=config_parsed, user_agent=self.user_agent)

    def _read_logging_config(self, config_parsed: configparser.ConfigParser):
        """
        This function is used to display a warning message when the user tries to set logger
        verbosity from the config file. This method of setting log verbosity is deprecated with
        v2.0.0.

        Args:
            config_parsed: ConfigParser object, generated from the config/ini file whose path is
             specified as a command line argument when airspotbot is started.
        """
        try:
            logging_level = str(config_parsed.get('MISC', 'logging_level')).upper()
            logger.warning(f"Setting log level via config file is deprecated as of v2.0.0. Use"
                           f"the '--quiet' or '--verbose' command line options instead.")
        except (configparser.NoOptionError, configparser.NoSectionError):
            pass

    def _initialize_twitter_api(self) -> tweepy.client:
        """
        Authenticate to Twitter API v2 via OAuth 1.0a, check credentials and connection

        Returns:
            tweepy.client object

        Raises:
            KeyboardInterrupt: Exits the main application loop if Twitter API authentication fails
        """
        logger.info('Connecting to Twitter API v2')
        logger.debug(f'Twitter consumer key: {self._consumer_key}')
        logger.debug(f'Twitter consumer secret: {self._consumer_secret}')
        logger.debug(f'Twitter access token: {self._access_token}')
        logger.debug(f'Twitter access token secret: {self._access_token_secret}')
        try:
            client = tweepy.Client(consumer_key=self._consumer_key,
                                   consumer_secret=self._consumer_secret,
                                   access_token=self._access_token,
                                   access_token_secret=self._access_token_secret)
            client.user_agent = self.user_agent
            user_info = client.get_me()
            logger.info(f"Authentication OK. Connected as user {user_info.data.username}")
        except tweepy.errors.TweepyException as tp_error:
            logger.critical('Error during Twitter API authentication', exc_info=True)
            raise KeyboardInterrupt
        logger.info('Twitter API v2 client created')
        return client

    def _initialize_twitter_api_v1(self) -> tweepy.API:
        """
        Authenticate to Twitter API v1.1 via OAuth 1.0a, check credentials and connection.
        This API connection is only used for media uploads, as twitter API v2 does not support
        them yet. Once v2 and tweepy support uploads, this will be removed

        Returns:
            tweepy.API object

        Raises:
            KeyboardInterrupt: Exits the main application loop if Twitter API authentication fails
        """
        logger.info('Connecting to Twitter API v1.1')
        logger.info(f'Twitter consumer key: {self._consumer_key}')
        logger.info(f'Twitter consumer secret: {self._consumer_secret}')
        logger.info(f'Twitter access token: {self._access_token}')
        logger.info(f'Twitter access token secret: {self._access_token_secret}')
        auth = tweepy.OAuthHandler(self._consumer_key, self._consumer_secret)
        auth.set_access_token(self._access_token, self._access_token_secret)
        api = tweepy.API(auth, wait_on_rate_limit=True)
        try:
            # test that authentication worked
            api.verify_credentials()
            api.user_agent = self.user_agent
            logger.info("Authentication OK")
        except (tweepy.errors.TweepyException, tweepy.errors.HTTPException) as tp_error:
            logger.critical('Error during Twitter API authentication', exc_info=True)
            raise KeyboardInterrupt
        logger.info('Twitter API v1.1 client created')
        return api

    def _validate_twitter_config(self, config_parsed: configparser.ConfigParser):
        """
        Checks values in ConfigParser object and make sure they are sane

        Args:
            config_parsed: ConfigParser object, generated from the config/ini file whose path is
             specified as a command line argument when airspotbot is started.

        Raises:
            ValueError: If the config file is parsed but an invalid option/value is present, exit
            the main application loop with a descriptive error message.
            KeyboardInterrupt: Exits the main application loop if an error occurs when getting
            options from the file with the ConfigParser.get() method (for example, a missing option)
        """
        try:
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
            if config_parsed.get('TWITTER', 'enable_screenshot').lower() == 'y':
                self.enable_screenshot = True
                try:
                    zoom_value = config_parsed.get('TWITTER', 'screenshot_zoom')
                    self.zoom_level = int(zoom_value)
                    if self.zoom_level > 20 or self.zoom_level < 1:
                        raise ValueError
                except ValueError:
                    raise ValueError(f"Bad value in config file for TWITTER/screenshot_zoom: "
                                     f"'{zoom_value}'. Must be an integer from 1 to 20.")
            elif config_parsed.get('TWITTER', 'enable_screenshot').lower() == 'n':
                self.enable_screenshot = False
            else:
                raise ValueError("Bad value in config file for TWITTER/enable_screenshot. "
                                 "Must be 'y' or 'n'.")
        except configparser.Error as config_error:
            logger.critical('Configuration file error', exc_info=True)
            raise KeyboardInterrupt

    def tweet_spot(self, aircraft: adsbget.AircraftSpot):
        """
        Generate tweet based on aircraft data returned in dictionary format from the adsbget
        module's Spotter.spot_queue list of dictionaries.

        Args:
            aircraft: adsbget.AircraftSpot object generated from ADSBX API JSON reply,
            representing one aircraft

        Raises:
            KeyboardInterrupt: Exits the main application loop if there is an error when sending
            a tweet or interacting with the Twitter API
        """
        hex_code: str = aircraft.hex_code
        type_code: str = aircraft.type_code
        reg_num: str = aircraft.reg
        latitude_degrees: float = aircraft.coordinates.latitude
        longitude_degrees: float = aircraft.coordinates.longitude
        description: str | None = aircraft.description
        altitude_feet: int = aircraft.altitude_ft
        speed: str = aircraft.speed_string
        callsign: str | None = aircraft.callsign
        image_path: Path | None = aircraft.image_path
        link = f'https://globe.adsbexchange.com/?icao={hex_code}'
        location_description = self._loc.get_location_description(str(latitude_degrees),
                                                                  str(longitude_degrees))
        tweet = f"{description if description else type_code}" \
                f"{', callsign ' + callsign if callsign else ''}, hex ID {hex_code.upper()}, RN {reg_num}, is " \
                f"{location_description}. Altitude {altitude_feet} ft, {speed}. {link}"
        logger.info(f"Generated tweet text: {tweet}")
        if len(tweet) <= 280:
            valid_tweet = True
        else:
            logger.error(f"Tweet is too long: {len(tweet)}/280 characters. Skipping!")
            valid_tweet = False
        if self._enable_tweets and valid_tweet:
            uploaded_media_ids = []
            # generate and upload screenshot image
            if self.enable_screenshot:
                # initialize a binary stream to write then read the png screenshot, all in memory
                with BytesIO() as b:
                    screenshot_binary = self.screenshotter.get_globe_screenshot(hex_code)
                    if screenshot_binary:
                        b.write(screenshot_binary)
                        b.seek(0)  # set byte stream position to the start
                        try:
                            # Twitter api v2 does not support media upload, so we need a
                            #  v1.1 tweepy.api instance for media upload
                            screenshot_media = self._v1_api.media_upload(filename="screenshot.png", file=b)
                            uploaded_media_ids.append(screenshot_media.media_id)
                        except (tweepy.errors.TweepyException, tweepy.errors.HTTPException):
                            # if upload fails, handle exception and proceed gracefully without an image
                            logger.warning(f"Error uploading screenshot", exc_info=True)
                    else:
                        logger.warning("No screenshot uploaded!")
            # find and upload aircraft image from file specified in watchlist
            if image_path:
                try:
                    # if an image path is specified, upload it.
                    # Twitter api v2 does not support media upload, so we need a
                    #  v1.1 tweepy.api instance for media upload
                    logger.debug(f"Uploading image from {image_path}")
                    image_media = self._v1_api.media_upload(image_path)
                    uploaded_media_ids.append(image_media.media_id)
                except (tweepy.errors.TweepyException, tweepy.errors.HTTPException):
                    # if upload fails, handle exception and proceed gracefully without an image
                    logger.warning(f"Error uploading image from {image_path}, check if file exists",
                                   exc_info=True)
            logger.info(f"Attached Media IDs: {uploaded_media_ids}")
            logger.info(f'Sending tweet...')
            try:
                if len(uploaded_media_ids) > 0:
                    self._client.create_tweet(text=tweet, media_ids=uploaded_media_ids)
                else:
                    self._client.create_tweet(text=tweet)
                logger.info("Tweet successful!")
            except (tweepy.errors.TweepyException, ConnectionError):
                logger.error('Error sending tweet', exc_info=True)
                logger.error('Attempting to re-initialize Twitter API connection')
                self._client = self._initialize_twitter_api()
                self._v1_api = self._initialize_twitter_api_v1()


def run_bot(config_path: str,
            watchlist_path: str,
            image_dir: str,
            user_agent: str,
            enable_tweets: bool):
    """
    Main program loop of airspotbot. Handles initial configuration and instantiation of
     config, SpotBot and Spotter objects. After this, runs an infinite loop for checking ADSBX API
     and tweeting spots, based on time intervals specified in config file. Invoked from __main__.py.

    Args:
        config_path: String containing relative or absolute path to config INI file.
        watchlist_path: String containing relative or absolute path to watchlist CSV file.
        image_dir: String containing relative or absoluter path to directory of images
        user_agent: User agent string used in API requests
        enable_tweets: Boolean, if True enables Twitter authentication and creation of tweets.
          Otherwise, tweet text will only be printed to the log.
    """

    config = read_config(config_path)
    bot = SpotBot(config_parsed=config,
                  user_agent=user_agent,
                  enable_tweets=enable_tweets)
    spots = adsbget.Spotter(config_parsed=config,
                            watchlist_path=watchlist_path,
                            image_dir=image_dir,
                            user_agent=user_agent)
    bot_time_seconds = time()
    spot_time_seconds = time()
    # set startup boolean to immediately check for aircraft and tweet when bot first starts
    startup = True
    # perpetually loop through checking aircraft spots and tweeting according to interval in config
    while True:
        if time() > spot_time_seconds + spots.adsb_interval_seconds or startup:
            startup = False
            spots.check_spots()
            spot_time_seconds = time()
            logger.info(f"{len(spots.spot_queue)} spots in tweet queue.")
            first_spot_in_queue = True
            while spots.spot_queue:
                if not first_spot_in_queue:
                    logger.debug(f"Waiting {bot.tweet_interval_seconds} before next tweet")
                    sleep(bot.tweet_interval_seconds)
                spot = spots.spot_queue.popleft()
                bot.tweet_spot(spot)
                first_spot_in_queue = False
        else:
            sleep(0.2)


def read_config(config_path: str) -> configparser.ConfigParser:
    """
    Parse configuration INI file and return a ConfigParser object.

    Args:
        config_path: String containing relative or absolute path to config INI file.

    Returns:
        ConfigParser object

    Raises:
        KeyboardInterrupt: Exits the main application loop if the configuration file is malformed
        or cannot be found
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

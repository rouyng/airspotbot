"""
This module contains the class SpotBot, which interfaces with the twitter API to generate airspotbot's tweets.
It also has the main program loop of airspotbot, so executing this module starts airspotbot.
"""


import configparser
import logging
from time import sleep, time
import tweepy
import adsbget
import location

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%d-%b-%y %H:%M:%S')


class SpotBot:
    def __init__(self, config_file_path):
        self.config_file_path = config_file_path
        self._interval = 5
        self._consumer_key = None
        self._consumer_secret = None
        self._access_token = None
        self._access_token_secret = None
        self._use_descriptions = False
        self._down_tweet = False
        self._read_twitter_config()
        self._api = self._initialize_twitter_api()
        self._loc = location.Locator(self.config_file_path)

    def _initialize_twitter_api(self):
        """Authenticate to Twitter API, check credentials and connection"""
        logging.info(f'Twitter consumer key: {self._consumer_key}')
        logging.info(f'Twitter consumer secret: {self._consumer_secret}')
        logging.info(f'Twitter access token: {self._access_token}')
        logging.info(f'Twitter access token secret: {self._access_token_secret}')
        auth = tweepy.OAuthHandler(self._consumer_key, self._consumer_secret)
        auth.set_access_token(self._access_token, self._access_token_secret)
        api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True) # Create API object
        try:
            # test that authentication worked
            api.verify_credentials()
            logging.info("Authentication OK")
        except tweepy.error.TweepError as e:
            logging.critical('Error during Twitter API authentication')
            raise e
        logging.info('Twitter API created')
        return api

    def _read_twitter_config(self):
        """Read configuration values from file and check whether values are sane"""
        parser = configparser.ConfigParser()
        parser.read(self.config_file_path)  # read config file at path
        try:
            self._interval = int(parser.get('TWITTER', 'tweet_interval'))
            self._consumer_key = parser.get('TWITTER', 'consumer_key')
            self._consumer_secret = parser.get('TWITTER', 'consumer_secret')
            self._access_token = parser.get('TWITTER', 'access_token')
            self._access_token_secret = parser.get('TWITTER', 'access_token_secret')
            if parser.get('TWITTER', 'use_descriptions').lower() == 'y':
                self._use_descriptions = True
            elif parser.get('TWITTER', 'use_descriptions').lower() == 'n':
                self._use_descriptions = False
            else:
                raise ValueError()
            if parser.get('TWITTER', 'down_tweet').lower() == 'y':
                self._down_tweet = True
            elif parser.get('TWITTER', 'down_tweet').lower() == 'n':
                self._down_tweet = False
            else:
                raise ValueError()
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            logging.critical(f'Configuration file error: {e}')

    def tweet_spot(self, aircraft: dict):
        icao, type_code, reg_num, lat, lon, description, alt, speed, callsign = aircraft['icao'], aircraft['type'], aircraft['reg'], aircraft['lat'], aircraft['lon'], aircraft['desc'], aircraft['alt'], aircraft['spd'], aircraft['call']
        link = f'https://tar1090.adsbexchange.com/?icao={icao}'
        location_description = self._loc.get_location_description(lat, lon)
        if reg_num.strip() == '':
            reg_num = 'unknown'
        if type_code.strip() == '':
            type_code = 'Unknown aircraft type'
        if callsign == reg_num:
            # if callsign is same as the registration number, ADSBx is not reporting a callsign
            callsign = False
        tweet = f"{description if description else type_code}{', callsign '+ callsign if callsign else ''}, ICAO {icao}, RN {reg_num}, is {location_description}. Altitude {alt} ft, speed {speed} kt. {link}"
        if aircraft['img']:
            image_path = "images/" + aircraft['img'] # always look for images in the /images subfolder
            try:
                # if an image path is specified, upload it
                logging.debug(f"Uploading image from {image_path}")
                image = self._api.media_upload(image_path)
            except tweepy.error.TweepError:
                # if upload fails, handle exception and proceed gracefully without an image
                logging.warning(f"Error uploading image from {image_path}, check if file exists")
                image = False
        else:
            image = False
        logging.info(f'Tweeting: {tweet}')
        try:
            if image:
                try:
                    self._api.update_status(tweet, media_ids=[image.media_id])
                except AttributeError as e:
                    # catch an attribute error, in case media upload fails in an unexpected way
                    logging.warning("Attribute error when sending tweet")
                    logging.warning(e)
                    self._api.update_status(tweet)
            else:
                self._api.update_status(tweet)
        except tweepy.error.TweepError as e:
            logging.critical('Error sending tweet')
            raise e

    def _link_reply(self):
        # TODO: function to reply to to a tweet generated by tweet_spot with a link defined in watchlist.csv
        pass


if __name__ == "__main__":
    bot = SpotBot('asb.config')
    spots = adsbget.Spotter('asb.config', 'watchlist.csv')
    bot_time = time()
    spot_time = time()
    # check for aircraft and tweet any when bot first starts
    spots.check_spots()
    for i in range(0, len(spots.spot_queue)):
        spot = spots.spot_queue.pop(0)
        bot.tweet_spot(spot)
    # perpetually loop through checking aircraft spots and tweeting according to time intervals set in asb.config
    while True:
        if time() > spot_time + spots.interval:
            spots.check_spots()
            spot_time = time()
        elif time() > bot_time + bot._interval:
            for i in range(0, len(spots.spot_queue)):
                spot = spots.spot_queue.pop(0)
                bot.tweet_spot(spot)
            bot_time = time()
        else:
            sleep(1)

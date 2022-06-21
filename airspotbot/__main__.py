import logging
from . import airspotbot
import argparse

VERSION = "2.0.0"
USER_AGENT = f"airspotbot/{VERSION} (https://github.com/rouyng/airspotbot)"
DEFAULT_CONFIG_PATH = './config/asb.config'
DEFAULT_WATCHLIST_PATH = './config/watchlist.csv'
DEFAULT_IMAGE_DIRECTORY = './images/'

logger = logging.getLogger("airspotbot")

parser = argparse.ArgumentParser(description='A twitter bot for reporting aircraft activity in '
                                             'an area, using the ADS-B Exchange API. For more '
                                             'details, see README.md.',
                                 prog="airspotbot")
parser.add_argument('-c', '--config',
                    type=str,
                    nargs='?',
                    help=f'Optional path to config file. Defaults to {DEFAULT_CONFIG_PATH}',
                    default=DEFAULT_CONFIG_PATH)
parser.add_argument('-w', '--watchlist',
                    type=str,
                    nargs='?',
                    help=f'Optional path to watchlist file. Defaults to {DEFAULT_WATCHLIST_PATH}',
                    default=DEFAULT_WATCHLIST_PATH)
parser.add_argument('-i', '--imagedir',
                    type=str,
                    nargs='?',
                    help=f'Optional path to directory of images. airspotbot will search here for '
                         f'image files defined in the watchlist. Defaults to '
                         f'{DEFAULT_IMAGE_DIRECTORY}',
                    default=DEFAULT_IMAGE_DIRECTORY)
parser.add_argument('-d', '--disable-tweets',
                    action='store_false',
                    help="Optional flag to disable tweets. Can be used for testing without Twitter"
                         "API credentials.")
parser.add_argument('--version', action='version', version=f'%(prog)s {VERSION}')

# TODO: argument to disable twitter API connection and only print tweets to stdout
# TODO: argument to set logging level/verbosity

args = parser.parse_args()
try:
    airspotbot.run_bot(config_path=args.config,
                       watchlist_path=args.watchlist,
                       image_dir=args.imagedir,
                       user_agent=USER_AGENT,
                       enable_tweets=args.disable_tweets)
except KeyboardInterrupt:
    logger.critical("Exiting!")

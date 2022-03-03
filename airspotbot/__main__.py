from . import airspotbot
import argparse

DEFAULT_CONFIG_PATH = './config/asb.config'
DEFAULT_WATCHLIST_PATH = './config/watchlist.csv'

# TODO: refactor logger to instantiate logging config once in this module, then use getLogger()
#  in all other modules

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

# TODO: argument to disable twitter API connection and only print tweets to stdout
# TODO: argument to set logging level/verbosity

args = parser.parse_args()
airspotbot.run_bot(config_path=args.config, watchlist_path=args.watchlist)

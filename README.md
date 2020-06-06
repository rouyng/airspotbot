# airspotbot
airspotbot is a Twitter bot designed to provide simple, flexible way to report interesting aircraft via
twitter posts. It uses [Tweepy](https://www.tweepy.org/) and the [adsbexchange.com API](https://www.adsbexchange.com/data/).

## Configuring
airspotbot has two files that must be configured before use: `asb.config` and `watchlist.csv`

`asb.config` is used to set your API keys and other bot configuration, such as tweeting interval.
 You must have valid API keys for twitter.com and adsbexchange.com. Please operate your installation of airspotbot in
  accordance with all relevant terms of service.
  
`watchlist.csv` is used to specify which aircraft appear as valid spots. Currently, airspotbot supports specifying aircraft by registration number
or type. The "Key" column sets the aircraft type code or registration number. "Type" should be either "RN" for registration
number or "TC" for type code. "Description "
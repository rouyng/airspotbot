# airspotbot
airspotbot is a Twitter bot designed to provide simple, flexible way to report interesting aircraft activity in a designated area via twitter posts. It uses [Tweepy](https://www.tweepy.org/) and the [ADS-B exchange API](https://www.adsbexchange.com/data/). airspotbot is designed to be extremely configurable, so it can be used to monitor diverse kinds of activity.

## Use cases
airspotbot is designed to be configured for multiple use cases. 

## Examples
airspotbot currently runs [@phxairspots on twitter](https://www.twitter.com/phxairspots). If you use airspotbot to run a twitter account and would like it listed here, let me know via opening an issue or create a pull request adding it to this section in `README.md`.

## Configuring
airspotbot has two files that must be configured before use: `asb.config` and `watchlist.csv`

### asb.config
Used to set your API keys and other bot configuration, such as tweeting interval.
 You must have valid API keys for Twitter and ADS-B Exchange in order to deploy airspotbot for your own use. Please operate your installation of airspotbot in accordance with all relevant terms of service.
  
### watchlist.csv
Used to specify which active aircraft cause the bot to tweet spots. Currently, airspotbot supports specifying aircraft by registration number or ICAO aircraft type code. Please note that setting `spot_unknown` and/or `spot_mil` options to "Y" in `asb.config` will cause unknown and/or military aircraft to generate tweets regardless of what is set in `watchlist.csv`.
* "Key" column sets the ICAO aircraft type code or registration number. 
* "Type" should be either "RN" for registration number or "TC" for ICAO type code.
* "Mil Only" should be set to Y or N. This column only has an effect for rows with type set to "TC". When set to Y, only military aircraft with that type code will be tweeted. This feature exists because many military aircraft show up on ADS-B Exchange with civilian type codes. For example, a UH-72 Lakota will appear with a EC45 type code (referring to the Eurocopter EC145 civilian model it is based on). If you are only interested in spotting military UH-72s but not civilian EC145 helicopters, setting "Mil only" to Y will only show those aircraft with a type code of EC45 that are flagged as military.
* The "Description" field is optional, if filled in this will replace the type code in the tweet's text. 

## TODO list
Here are some planned features/fixes. You are welcome to work on these if you are interested and able (see "Contributing" section below)
* Add ability to use ADS-B exchange free API keys. airspotbot currently is only able to use the paid ADS-B Exchange API available through rapidAPI. Therefore the only valid option for `adsb_api` in the config file is `rapidapi.` This is simply because I do not currently meet the requirements to receive a free key from ADS-B exchange. I plan to add the ability to use these free keys when I qualify for one and can test it.
* Add new "type" column value "IA" to watchlist to specify unique ICAO addresses to spot/tweet.  Useful to track aircraft that do not have/report registration or serial numbers.
* Add new "reply" column to watchlist. This will automatically reply to the spot tweet with the content entered in the reply cell. Sometimes, you want to add additional context such as an explanation or link.
* Add ability to specify an image to include with a spot tweet
* Add automatic lookup of photos by registration number with jetphotos.com (`reply_jetphotos` option in config file is a placeholder for this)
* Add automatic tweeting to notify followers of ADS-B Exchange API outage/error. Users should be informed if an error/outage is preventing spots from being tweeted.

 
 ## Contributing
 Contributions are welcome, including those from new/novice contributors (I'm still a Python novice myself!). Source code contributions should be via pull requests. Bug reports and feature requests via opening issues. If you want to suggest a specific aircraft type or registration number for @phxairspots or another airspotbot-powered account to monitor, please contact the account directly rather than changing `watchlist.csv` in this repository.
 
 ## License
 airspotbot is licensed under GNU General Public License v3.0. See `LICENSE.md` for details.

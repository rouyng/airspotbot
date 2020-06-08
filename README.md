# airspotbot
airspotbot is a Twitter bot designed to provide simple, flexible way to report interesting aircraft activity in a designated area via
twitter posts. It uses [Tweepy](https://www.tweepy.org/) and the [adsbexchange.com API](https://www.adsbexchange.com/data/). airspotbot is designed to be extremely configurable, so it can be used to monitor diverse kinds of activity. 

## Configuring
airspotbot has two files that must be configured before use: `asb.config` and `watchlist.csv`

### asb.config
Used to set your API keys and other bot configuration, such as tweeting interval.
 You must have valid API keys for twitter.com and adsbexchange.com in order to deploy airspotbot for your own use. Please operate your installation of airspotbot in accordance with all relevant terms of service.
  
### watchlist.csv
Used to specify which active aircraft cause the bot to tweet spots. Currently, airspotbot supports specifying aircraft by registration number or ICAO aircraft type code. Please note that setting `spot_unknown` and/or `spot_mil` options to "Y" in `asb.config` will cause unknown and/or military aircraft to generate tweets regardless of what is set in `watchlist.csv`.
* "Key" column sets the ICAO aircraft type code or registration number. 
* "Type" should be either "RN" for registration number or "TC" for ICAO type code.
* "Mil Only" should be set to Y or N. This column only has an effect for rows with type set to "TC". When set to Y, only military aircraft with that type code will be tweeted. This feature exists because many military aircraft show up on ADSBexchange with civilian type codes. For example, a UH-72 Lakota will appear with a EC45 type code (referring to the Eurocopter EC145 civilian model it is based on). If you are only interested in spotting military UH-72s but not civilian EC145 helicopters, setting "Mil only" to Y will only show those aircraft with a type code of EC45 that are flagged as military.
 * The "Description" field is optional, if filled in this will be added to the default tweet text. 
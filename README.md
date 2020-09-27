# airspotbot
airspotbot is a Twitter bot designed to provide simple, flexible way to report interesting aircraft activity in a designated area via twitter posts. It uses [Tweepy](https://www.tweepy.org/) and the [ADS-B exchange API](https://www.adsbexchange.com/data/). airspotbot is designed to be extremely configurable, so it can be used to monitor diverse kinds of activity.


## Examples
airspotbot currently runs [@phxairspots on twitter](https://www.twitter.com/phxairspots). If you use airspotbot to run a twitter account and would like it listed here, let me know via opening an issue or create a pull request adding it to this section in `README.md`.

### Use cases
airspotbot is designed to be configurable for multiple use cases. The list below provides some examples. Please note that due to limitations of the ADS-B Exchange API, airspotbot is designed to only track spots within a 1, 5, 10, 25, 100 or 250 nautical mile radius of the latitude and longitude specified in the configuration file. See the configuring section for details on how to configure airspotbot for one of these use cases. airspotbot is designed so that a single bot can be configured to fulfill multiple use cases simultaneously.

* I want to tweet when an aircraft with a specific civil [registration number](https://en.wikipedia.org/wiki/Aircraft_registration) is active in a certain area
* I want to tweet when a military aircraft with a specific serial number (for example, see [US](https://en.wikipedia.org/wiki/United_States_military_aircraft_serial_numbers) and [UK](https://en.wikipedia.org/wiki/United_Kingdom_military_aircraft_serial_numbers) serial numbers) is active in a certain area
* I want to tweet when an aircraft with a specific [unique ICAO transponder address](https://en.wikipedia.org/wiki/Aviation_transponder_interrogation_modes#ICAO_24-bit_address) is active in a certain area
* I want to tweet all military aircraft activity in a certain area
* I want to tweet when any aircraft with a certain [type code](https://en.wikipedia.org/wiki/List_of_aircraft_type_designators) is active in my area
* I want to tweet when any aircraft with a certain type code is active in my area, but only if they are military

## Running
airspotbot was developed and tested using Python 3.7. Ensure a compatible Python version is installed in your system/virtual environment and install package requirements using `pip install -r requirements.txt`. Configure `asb.config` with your API keys and preferences and `watchlist.csv` with your desired watchlist. You can then start airspotbot by running `python airspotbot.py`.

A basic `Dockerfile` is also included for deployment via Docker container. 

## Configuring
airspotbot has two files that must be configured before use: `asb.config` and `watchlist.csv`

### asb.config
Used to set your API keys and other bot configuration, such as tweeting interval, interval to check ADS-B Exchange and some tweeting rules, such as whether to tweet all military activity or all aircraft with unknown registration numbers. You must have valid API keys for Twitter and ADS-B Exchange in order to deploy airspotbot for your own use. Please operate your installation of airspotbot in accordance with all relevant terms of service.

`radius` parameter indicates the radius in nautical miles around the specified latitude/longitude that will be queried for aircraft activity. It must have a value of 1, 5, 10, 25, 100 or 250. Due to ADS-B Exchange API limitations, any values larger, smaller or in between these will cause an error and cannot be used.
 
`down_tweet` and `reply_jetphotos` parameters are currently nonfunctional placeholders for planned features. See TODO section for more information.
  
### watchlist.csv
Used to specify which active aircraft cause the bot to tweet spots. Currently, airspotbot supports specifying aircraft by registration number or ICAO aircraft type code. Please note that setting `spot_unknown` and/or `spot_mil` options to "Y" in `asb.config` will cause unknown and/or military aircraft to generate tweets regardless of what is set in `watchlist.csv`.
* "Key": column sets the ICAO aircraft type code or registration number. 
* "Type": either "RN" for registration number/serial number, "TC" for ICAO type code, or "IA" for unique ICAO address.
* "Mil Only": should be set to Y or N. This column only has an effect for rows with type set to "TC". When set to Y, only military aircraft with that type code will be tweeted. This feature exists because many military aircraft show up on ADS-B Exchange with civilian type codes. For example, a UH-72 Lakota will appear with a EC45 type code (referring to the Eurocopter EC145 civilian model it is based on). If you are only interested in spotting military UH-72s but not civilian EC145 helicopters, setting "Mil only" to Y will only show those aircraft with a type code of EC45 that are flagged as military.
* "Description": Optional, if filled in this will replace the type code in the tweet's text. 
* "Image": filename of image file in the `images/` subdirectory to associate with this watchlist item. The specified image will be added to tweets of that watchlist item. This field is case sensitive.

### Images
Put any images specified in the Images column of watchlist.csv in the `images/` subdirectory. Any media type accepted by Twitter is allowable (JPEG, GIF, and PNG).

### Location information
airspotbot has several options for representing the geographical location of spotted aircraft. This is configured in the `[LOCATION]` section of `asb.config`.
* `location_type`: enter one of the following options:
    * "manual": Use some string of text, like a place/region name. This is useful if your spotting coordinates and radius is close to a distinct landmark/area and you don't need any more granular location representation. For example, if airspotbot is set up to spot aircraft in a 1 nm radius of 51.4736, -0.4688, you might set this option to "manual" and "location_description" to "near Heathrow Airport" so the bot just reports "*aircraft* is near Heathrow Airport".
    * "coordinate": Tweets latitude/longitude coordinates, rounded to 4 decimal places.
    * "pelias": Use pelias geocoder to reverse-lookup nearby landmarks based on the lat/long reported by ADSBx. Useful if you need airspotbot to cover a large area, such as a city with many neighborhoods and landmarks. The "pelias_host" option must also have a valid url to access a running instance of Pelias.
* `location_description`: If "location_type" is set to "manual", enter the text string you want to be tweeted along with the spot to identify the location (such as "near Heathrow Airport", "over Downtown Los Angeles", etc).
* `pelias_host`: Enter the url/port of an active Pelias instance running a reverse geocoding endpoint, such as "http://192.168.1.5:4000". Required if you are using "location_type = pelias". [Find more information about Pelias here](https://github.com/pelias/documentation).
* `pelias_port`: Port for API endpoint at host
* `pelias_area_layer`: Contains the pelias layer name used to determine the nearest area to the spotted aircraft. "neighbourhood" is a good default, but can be changed depending on how coarse/fine you need. If empty, the description will not include an area. See [the Pelias docs](https://github.com/pelias/documentation/blob/master/reverse.md) for information on valid layers for the reverse geocoding endpoint. 
* `pelias_point_layer`: Contains the pelias layer name used to determine the closest point of interest to the spotted aircraft. "venue" is a good default, but can be changed depending on how coarse/fine you need. If empty, the description will not include a nearby point of interest. See [the Pelias docs](https://github.com/pelias/documentation/blob/master/reverse.md) for information on valid layers for the reverse geocoding endpoint. 

## TODO list
Here are some planned features/fixes. You are welcome to work on these if you are interested and able (see "Contributing" section below)
* Add new "reply" column to watchlist. This will automatically reply to the spot tweet with the content entered in the reply cell. Sometimes, you want to add additional context such as an explanation or link.
* Add automatic lookup of photos by registration number with jetphotos.com (`reply_jetphotos` option in config file is a placeholder for this)
* Add automatic tweeting to notify followers of ADS-B Exchange API outage/error. Users should be informed if an error/outage is preventing spots from being tweeted. (`down_tweet` option in config file is a placeholder for this)

 
 ## Contributing
 Contributions are welcome, including those from new/novice contributors. Source code contributions should be via pull requests. Bug reports and feature requests via opening issues. If you want to suggest a specific aircraft type or registration number for @phxairspots or another airspotbot-powered account to monitor, please contact the account directly rather than changing `watchlist.csv` in this repository.
 
 ## License
 airspotbot is licensed under GNU General Public License v3.0. See `LICENSE.md` for details.

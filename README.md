[![build status shield](https://img.shields.io/github/workflow/status/rouyng/airspotbot/test%20and%20lint%20airspotbot)](https://github.com/rouyng/airspotbot/actions?query=workflow%3A%22test+and+lint+airspotbot%22) [![license shield](https://img.shields.io/github/license/rouyng/airspotbot)](https://github.com/rouyng/airspotbot/blob/master/LICENSE.md)
# airspotbot
airspotbot is a Twitter bot designed to provide simple, flexible way to report interesting aircraft activity in a designated area via twitter posts. It uses [Tweepy](https://www.tweepy.org/) and the [ADS-B exchange API](https://www.adsbexchange.com/data/). airspotbot is designed to be extremely configurable, so it can be used to monitor diverse kinds of activity.


## What can it do?
You can configure airspotbot to tweet multiple kinds of aircraft activity within a certain area. The list below provides some examples.  See the "Configuration" section for details on how to configure airspotbot for one of these use cases. airspotbot is designed so that a single bot can be configured to fulfill multiple use cases simultaneously. 

* I want to tweet when an aircraft with a specific civil [registration number](https://en.wikipedia.org/wiki/Aircraft_registration) is active in a certain area
* I want to tweet when a military aircraft with a specific serial number (for example, see [US](https://en.wikipedia.org/wiki/United_States_military_aircraft_serial_numbers) and [UK](https://en.wikipedia.org/wiki/United_Kingdom_military_aircraft_serial_numbers) serial numbers) is active in a certain area
* I want to tweet when an aircraft with a specific [unique ICAO transponder address](https://en.wikipedia.org/wiki/Aviation_transponder_interrogation_modes#ICAO_24-bit_address) is active in a certain area
* I want to tweet all military aircraft activity in a certain area
* I want to tweet when any aircraft with a certain [type code](https://en.wikipedia.org/wiki/List_of_aircraft_type_designators) (i.e. make and model of aircraft) is active in my area
* I want to tweet when any aircraft with a certain type code is active in my area, but only if they are military


### Limitations
Please note that due to limitations of the ADS-B Exchange API, airspotbot is designed to only track spots within a 1, 5, 10, 25, 100 or 250 nautical mile radius of the latitude and longitude specified in the configuration file. In other words, you can't use one instance of airspotbot to track aircraft across the world. airspotbot is intended to monitor a specific area, such as an airport or city.
 
airspotbot is only as good as the data it receives. While ADS-B Exchange is a great resource that provides a huge amount of unfiltered data, there are still gaps in coverage. There are also many military aircraft that cannot be tracked or identified using their transponders. See [the ADS-B Exchange FAQ](https://www.adsbexchange.com/faq/) for more details.

### Example accounts
airspotbot currently runs [@phxairspots on twitter](https://www.twitter.com/phxairspots). If you use airspotbot to run a Twitter account and would like it listed here, let me know via opening an issue or create a pull request adding it to this section in `README.md`.

## Usage

### Requirements

 - airspotbot requires Python 3.7 or later.
 - You must have a valid [Twitter API](https://developer.twitter.com/en/docs/twitter-api) key
 - You must also have a valid [ADS-B Exchange API](https://www.adsbexchange.com/data/) key. Please note that as of 2021, ADS-B Exchange is no longer giving API keys to all feeders, so their API is now solely accessed through [their RapidAPI endpoint](https://rapidapi.com/adsbx/api/adsbexchange-com1). The "adsbx" endpoint option in asb.config is provided for legacy support, or if you have some preexisting agreement with ADSBX to use their endpoint directly. 
 
Please operate your installation of airspotbot in accordance with all relevant API terms of service. 

### Setup
1. Clone this repository using git: `git clone https://github.com/rouyng/airspotbot.git` OR download a zip file of the repository using the green "Code" button at the top of the GitHub repository page.
2. **Optional:** If you would like to deploy airspotbot as a Docker container, a basic `Dockerfile` is included. If you choose to do this, you probably know what you are doing. Otherwise, for a regular, non-Docker installation, proceed to the next step.
3. **Optional:** Set up a python [virtual environment](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment), using Python 3.7 or greater. This is recommended because it prevents different installations of python packages from interfering with each other.
4. Install package requirements using `pip3 install -r requirements.txt`
5. Configure `config/asb.config` with your API keys and preferences. See details in "Configuring" section below.
6. Configure `config/watchlist.csv` with your desired watchlist. See details in "Configuring" section below.

### Running
Run airspotbot with `python3 -m airspotbot`

## Configuration
airspotbot has two files that must be configured before use: `asb.config` and `watchlist.csv`. Both are located in the `config/` subdirectory.  

### asb.config
This file, structured in INI format, contains various configuration options organized into four sections:
- `[TWITTER]`: Twitter API credentials and options related to tweet interval and format.
- `[ADSB]`: ADS-B Exchange API credentials, spotting location information and filters to determine which aircraft are spotted/tweeted.
- `[LOCATION]`: Options for configuring location descriptions and reverse geocoding of aircraft locations. Has options for manually specifying a location description or connecting to Pelias and 3geonames APIs. See "Location description" section below for more details
- `[MISC]`: Various debugging options for testing and logging purposes.

Additional documentation on each individual option is provided as comments in the example `asb.config` file included in this repository.


### Location description
airspotbot has several options for representing the geographical location of spotted aircraft. The location description can be entered manually or determined via reverse geocoding.  These options are configured in the `[LOCATION]` section of `asb.config`.
* `location_type`: enter one of the following options:
    * "manual": Use some string of text, like a place/region name. This is useful if your spotting coordinates and radius is close to a distinct landmark/area and you don't need any more granular location representation. For example, if airspotbot is set up to spot aircraft in a 1 nm radius of 51.4736, -0.4688, you might set this option to "manual" and "location_description" to "near Heathrow Airport" so the bot just reports "*aircraft* is near Heathrow Airport".
    * "coordinate": Tweets latitude/longitude coordinates, rounded to 4 decimal places.
    * "3geonames": Use the free reverse geocoding API provided by [3geonames](https://3geonames.org) to reverse-lookup nearby place and/or city names based on the lat/long reported by ADSBx. Please note this is a free service that does not require signup, however requests may be throttled depending on the API provider's resource load. airspotbot also has a hardcoded 1 sec delay between requests to this API, in order to reduce load. 
    * "pelias": Use pelias geocoder to reverse-lookup nearby landmarks based on the lat/long reported by ADSBx. Useful if you need airspotbot to cover a large area, such as a city with many neighborhoods and landmarks. The "pelias_host" option must also have a valid url to access a running instance of Pelias. Please note that Pelias support is very experimental. If you encounter issues or can help test it, please let me know via Github Issues.
* `location_description`: If "location_type" is set to "manual", enter the text string you want to be tweeted along with the spot to identify the location (such as "near Heathrow Airport", "over Downtown Los Angeles", etc).
* `pelias_host`: Enter the url/port of an active Pelias instance running a reverse geocoding endpoint, such as "http://192.168.1.5:4000". Required if you are using "location_type = pelias". [Find more information about Pelias here](https://github.com/pelias/documentation).
* `pelias_port`: Port for API endpoint at host
* `pelias_area_layer`: Contains the pelias layer name used to determine the nearest area to the spotted aircraft. "neighbourhood" is a good default, but can be changed depending on how coarse/fine you need. If empty, the description will not include an area. See [the Pelias docs](https://github.com/pelias/documentation/blob/master/reverse.md) for information on valid layers for the reverse geocoding endpoint. 
* `pelias_point_layer`: Contains the pelias layer name used to determine the closest point of interest to the spotted aircraft. "venue" is a good default, but can be changed depending on how coarse/fine you need. If empty, the description will not include a nearby point of interest. See [the Pelias docs](https://github.com/pelias/documentation/blob/master/reverse.md) for information on valid layers for the reverse geocoding endpoint. 
  
### watchlist.csv
This is a CSV (comma separated value) file that contains a table of aircraft criteria used to tweet spots. It can be edited in your favorite spreadsheet program or by hand. This file is optional. If you delete `watchlist.csv`, airspotbot will only use rules set in `asb.config`.

By configuring this file, you can specify aircraft to spot by registration number, aircraft type code or ICAO hex code. Please note that setting `spot_unknown`, `spot_mil` and/or `spot_interesting` options to "Y" in `asb.config` will cause unknown, military and/or ADSBx-designated "interesting" aircraft to generate tweets regardless of what is set in `watchlist.csv`. If you only want to spot aircraft from the watchlist, make sure those options are set to "N".

`watchlist.csv` contains:

* "Key": (required) Sets the aircraft registration number, ICAO type code or ICAO hex code.
* "Type": (required) Must be one of the following values
  * "RN" for registration number/serial number
  * "TC" for ICAO type code. [List of valid codes.](https://en.wikipedia.org/wiki/List_of_aircraft_type_designators)
  * "IA" for ICAO hex address (also known as ID or hex code). These are unique 24-bit addresses assigned to each individual aircraft. [See this article for more details.](https://en.wikipedia.org/wiki/Aviation_transponder_interrogation_modes#Mode_S) Please note that some military aircraft may use duplicate and/or spoofed addresses.  
* "Mil Only": (optional) Set to Y or N. This column only has an effect for rows with type set to "TC". When set to Y, only military aircraft with that type code will be tweeted. This feature exists because many military aircraft show up on ADS-B Exchange with civilian type codes. For example, a UH-72 Lakota will appear with a EC45 type code (referring to the Eurocopter EC145 civilian model it is based on). If you are only interested in spotting military UH-72s but not civilian EC145 helicopters, setting "Mil only" to Y will only show those aircraft with a type code of EC45 that are flagged as military.
* "Description": (optional) if filled in this will replace the type code in the tweet's text. 
* "Image": (optional) filename of image file in the `images/` subdirectory to associate with this watchlist item. The specified image will be added to tweets of that watchlist item. This field is case-sensitive. Any media type accepted by Twitter is allowable (JPEG, GIF, and PNG).

**Warning**: The watchlist file must have all five column headers present and each row must have five columns (demarcated with four commas) even if some columns are left empty. Most watchlist-related errors are caused by missing commas. 

Here is an example of a valid `watchlist.csv` file:

```csv
Key,Type,Mil Only,Description,Image
H60,TC,N,Sikorsky H-60,uh-60.jpg
EC45,TC,Y,UH-72 Lakota,uh72.jpg
NASA941,RN,,NASA Super Guppy,
508035,IA,,Antonov AN-225 Mriya,
P28A,TC,N,Piper PA-28,test.png
N174SY,RN,,,
```


## TODO list
Here are some planned features/fixes. You are welcome to work on these if you are interested and able (see "Contributing" section below)
* Add new "reply" column to watchlist. This will automatically reply to the spot tweet with the content in the reply cell. Sometimes, you want to add additional context such as an explanation or link.
* Add automatic tweeting to notify followers of ADS-B Exchange API outage/error. Bot followers should be informed if an error/outage is preventing spots from being tweeted. (`down_tweet` option in config file is a placeholder for this)
* Allow setting of configuration file paths with command-line arguments, currently the paths are hardcoded.
* Fetch aircraft photos using [Planespotters.net API](https://www.planespotters.net/photo/api)
* Set custom user agent string for all API requests

 ## Contributing
 Contributions are welcome, including those from new/novice contributors. Source code contributions should be via pull requests. Bug reports and feature requests via opening issues. 
 
If you want to suggest a specific aircraft type or registration number for @phxairspots or another airspotbot-powered account to monitor, please contact the account directly.
 
 ## License
 airspotbot is licensed under GNU General Public License v3.0. See `LICENSE.md` for details.

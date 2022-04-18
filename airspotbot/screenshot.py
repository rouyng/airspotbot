"""
Module to get screenshots of plane location map from https://globe.adsbexchange.com.
Uses Selenium WebDriver to control a headless instance of the Chrome web browser
"""

import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from sys import platform


logger = logging.getLogger(__name__)

# Path to chromedriver executable when using a Windows system
# Since airspotbot is intended to be deployed in a server environment (such as a docker container)
#  this is primarily for testing purposes.
WINDOWS_CHROMEDRIVER_PATH = "./webdrivers/chromedriver.exe"


def start_webdriver() -> webdriver.Chrome:
    """
    Start headless chrome webdriver for selenium scraping.
    Specifies certain options to use a headless browser and work in Docker.

    Returns:
        webdriver object
    """
    options = webdriver.ChromeOptions()  # create ChromeOptions object to set webdriver options
    options.add_argument('headless')  # set chrome webdriver to run in headless mode
    options.add_argument('window-size=1200x600')
    options.add_argument(
        'disable-dev-shm-usage')  # This option helps the webdriver play nice in Docker environment
    options.add_argument(
        'no-sandbox')  # This option helps the webdriver play nice in Docker environment
    options.add_argument(
        'log-level=3')  # suppress chrome logging messages
    if platform == 'win32':
        driver = webdriver.Chrome(
            executable_path=WINDOWS_CHROMEDRIVER_PATH,
            options=options)
        logger.debug(f'Starting windows chromedriver executable from: {WINDOWS_CHROMEDRIVER_PATH}')
    else:
        # When running as Docker container, we don't need to specify a path to webdriver,
        # as it is included in system path.
        driver = webdriver.Chrome(options=options)
        logger.debug('Starting linux chromedriver from system path')
    return driver


def get_globe_screenshot(icao: str, driver: webdriver.Chrome) -> str:
    """
    Retrieve a screenshot showing the map location and flightpath of an aircraft with the
    specified ICAO address.

    Args:
        icao: ICAO address of plane to screenshot
        driver: Selenium webdriver instance to use
    Returns:
         Screenshot as base64 encoded string
    """
    map_element = driver.find_element(by=By.CSS_SELECTOR, value="canvas.ol-layer")
    return map_element.screenshot_as_base64

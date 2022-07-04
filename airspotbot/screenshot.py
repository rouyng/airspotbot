"""
Module to get screenshots of plane location map from https://globe.adsbexchange.com.
Uses Selenium WebDriver to control a headless instance of the Chrome web browser
"""

import logging

import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from sys import platform
from time import sleep, perf_counter

logger = logging.getLogger(__name__)

# Path to chromedriver executable when using a Windows system
# Since airspotbot is intended to be deployed in a server environment (such as a docker container)
#  this is primarily for testing purposes.
WINDOWS_CHROMEDRIVER_PATH = "./webdrivers/chromedriver.exe"


class Screenshotter:

    def __init__(self, zoom_level: int):
        if 1 <= zoom_level <= 20:
            self.zoom = int(zoom_level)
        else:
            logger.warning(f"Screenshot zoom level is set to {zoom_level}, it should be an integer "
                           f"from 1-20. Defaulting to 12.")
            self.zoom = 12
        self.driver = self._start_webdriver()

    def _start_webdriver(self) -> webdriver.Chrome:
        """
        Start headless chrome webdriver for selenium scraping.
        Specifies certain options to use a headless browser and work in Docker.

        Returns:
            webdriver object
        """
        options = webdriver.ChromeOptions()  # create ChromeOptions object to set webdriver options
        options.add_argument('headless')  # set chrome webdriver to run in headless mode
        options.add_argument('window-size=1200x800')
        # The following two options help the webdriver play nice in Docker environment
        options.add_argument('disable-dev-shm-usage')
        options.add_argument('no-sandbox')
        if logger.parent.level == 50:
            options.add_argument('log-level="SEVERE"')
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
        elif logger.parent.level == 10:
            options.add_argument('log-level="DEBUG"')
        else:
            options.add_argument('log-level="INFO"')
        if platform == 'win32':
            driver = webdriver.Chrome(
                executable_path=WINDOWS_CHROMEDRIVER_PATH,
                options=options)
            logger.debug(
                f'Starting windows chromedriver executable from: {WINDOWS_CHROMEDRIVER_PATH}')
        else:
            # When running as Docker container, we don't need to specify a path to webdriver,
            # as it is included in system path.
            driver = webdriver.Chrome(options=options)
            logger.debug('Starting chromedriver from system path')
        return driver

    def get_globe_screenshot(self, icao: str) -> str | None:
        """
        Retrieve a screenshot showing the map location and flightpath of an aircraft with the
        specified ICAO address.

        Args:
            icao: ICAO address of plane to screenshot
        Returns:
             PNG screenshot as binary data
        """
        logger.debug(f"Getting browser screenshot for ICAO {icao}")
        start_time = perf_counter()
        url = f"https://globe.adsbexchange.com/?icao={icao}&zoom={self.zoom}"
        try:
            self.driver.get(url)
            map_element = WebDriverWait(self.driver, timeout=10)\
                .until(presence_of_element_located((By.CSS_SELECTOR, "div.ol-layer")))
            sleep(5)  # hardcoded delay to let map canvas render fully
        except selenium.common.exceptions.TimeoutException:
            logger.error(f"Screenshotter could not find canvas.ol-layer element at {url}, "
                         f"timed out")
            logger.debug(f"Page source: {self.driver.page_source}")
            return None
        self.driver.execute_script("""
            // javascript snippet to hide ad banner elements
            var ad_selectors = [".FIOnDemandWrapper"]; // banner selectors
            for (var i=0;i<ad_selectors.length;i++) {
                let ad_element = document.querySelector(ad_selectors[i])
                if ( ad_element )
                    ad_element.style.display = "none";
            }
        """)
        end_time = perf_counter()
        logger.debug(f"Screenshot generated in {end_time-start_time:0.3f} seconds")
        return map_element.screenshot_as_png

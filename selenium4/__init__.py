# -*- coding: utf-8 -*-

from typing import Optional
import time

from . import driveroption
from . import driver
from . import browser
from . import elements
from . import waitfor

from .. import log

from selenium import webdriver


def open(is_headless=True, chrome_log_filepath: Optional[str] = None) -> Optional[webdriver.Chrome]:
    return driver.create(driver_option=driveroption.DriverOption(is_headless=is_headless, chrome_log_filepath=chrome_log_filepath))


def close(chromedriver: webdriver.Chrome) -> bool:
    return driver.destroy(chromedriver=chromedriver)


def page_load(chromedriver: webdriver.Chrome, url: str):
    browser.size(chromedriver)
    browser.loadurl(chromedriver, url)
    waitfor.page_load(chromedriver)
    waitfor.network_idle(chromedriver)


def wait_for_page_load(chromedriver: webdriver.Chrome):
    waitfor.page_load(chromedriver)


def screen_shot(chromedriver: webdriver.Chrome, file: str = "screen_shot_01.png"):
    browser.screen_shot(chromedriver, file)


def get_element_by_xpath(chromedriver: webdriver.Chrome, xpath: str):
    return elements.get_by_xpath_from_driver(chromedriver, xpath)


def get_element_by_class(chromedriver: webdriver.Chrome, classname: str):
    return elements.get_by_class_from_driver(chromedriver, classname)


def find_elements_by_class(chromedriver: webdriver.Chrome, classname: str):
    return elements.find_by_class_from_driver(chromedriver, classname)


def click_by_xpath(chromedriver: webdriver.Chrome, xpath: str) -> bool:
    waitfor.click_xpath(chromedriver, xpath)
    el = elements.get_by_xpath_from_driver(chromedriver, xpath)
    try:
        el.click()
        time.sleep(1)
        return True
    except Exception as ex:
        log.e(ex)
    return False


def click_by_id(chromedriver: webdriver.Chrome, id: str) -> bool:
    waitfor.click_id(chromedriver, id)
    el = elements.get_by_id_from_driver(chromedriver, id)
    try:
        el.click()
        time.sleep(1)
        return True
    except Exception as ex:
        log.e(ex)
    return False

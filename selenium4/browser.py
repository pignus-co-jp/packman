# -*- coding: utf-8 -*-

from typing import Optional
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from .. import log


def window_size(driver: webdriver.Chrome, w: int, h: int):
    if driver:
        driver.set_window_size(w, h)
    pass


def screen_shot(driver: webdriver.Chrome, file: str = "screenshot.png") -> bool:
    try:
        driver.save_screenshot(file)
    except Exception as ex:
        log.e(ex)
        return False
    return True


def loadurl(driver: webdriver.Chrome, url: str):
    if driver:
        try:
            driver.get(url)
        except Exception as ex:
            log.e(ex)
    pass


def wait4jsready(driver: webdriver.Chrome, timeout: int = 10):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script(
                "return document.readyState") == "complete"
        )
    except Exception as ex:
        log.e(ex)
    pass

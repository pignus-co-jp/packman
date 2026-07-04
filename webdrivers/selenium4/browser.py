# -*- coding: utf-8 -*-

from typing import Optional
from selenium import webdriver
from ... import log


def size(chromedriver: webdriver.Chrome, w: int = 1280, h: int = 720):
    if chromedriver:
        chromedriver.set_window_size(w, h)
    pass


def screen_shot(chromedriver: webdriver.Chrome, file: str = "screenshot.png") -> bool:
    try:
        chromedriver.save_screenshot(file)
    except Exception as ex:
        log.e(ex)
        return False
    return True


def loadurl(chromedriver: webdriver.Chrome, url: str):
    if chromedriver:
        try:
            chromedriver.get(url)
        except Exception as ex:
            log.e(ex)
    pass

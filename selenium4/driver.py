# -*- coding: utf-8 -*-

# 必要なライブラリをインストール
#!pip install selenium
#!pip install python-dateutil

# ブラウザ（chromium）とドライバをインストール
# !apt-get update
# !apt-get install -y chromium-browser chromium-chromedriver

from typing import Optional
from selenium import webdriver
from . import driveroption
from .. import log


def create(driver_option: Optional[driveroption.DriverOption] = None) -> Optional[webdriver.Chrome]:
    if driver_option is None:
        driver_option = driveroption.DriverOption()
    try:
        return webdriver.Chrome(service=driver_option.get_service(), options=driver_option.get_options())
    except Exception as ex:
        log.e(ex)
    return None


def destroy(chromedriver: webdriver.Chrome) -> bool:
    try:
        chromedriver.quit()
    except Exception as ex:
        log.e(ex)
        return False
    return True

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


def create_driver(driver_option: driveroption.DriverOption = driveroption.DriverOption()) -> Optional[webdriver.Chrome]:
    try:
        return webdriver.Chrome(service=driver_option.get_service(), options=driver_option.get_options())
    except Exception as ex:
        log.e(ex)
    return None


def destroy(driver: webdriver.Chrome) -> bool:
    try:
        driver.quit()
    except Exception as ex:
        log.e(ex)
        return False
    return True

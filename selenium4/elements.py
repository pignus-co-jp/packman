# -*- coding: utf-8 -*-

from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from .. import log


def find_by_class_from_driver(driver: webdriver.Chrome, classname: str) -> List[WebElement]:
    if driver:
        try:
            els = driver.find_elements(By.CLASS_NAME, classname)
            if els:
                return els
        except Exception as ex:
            log.e(ex)
    return []


def get_by_class_from_driver(driver: webdriver.Chrome, classname: str) -> Optional[WebElement]:
    if driver:
        try:
            el = driver.find_element(By.CLASS_NAME, classname)
            if el:
                return el
        except Exception as ex:
            log.e(ex)
    return None


def find_by_class(element: WebElement, classname: str) -> List[WebElement]:
    if element:
        try:
            els = element.find_elements(By.CLASS_NAME, classname)
            if els:
                return els
        except Exception as ex:
            log.e(ex)
    return []


def get_by_class(element: WebElement, classname: str) -> Optional[WebElement]:
    if element:
        try:
            el = element.find_element(By.CLASS_NAME, classname)
            if el:
                return el
        except Exception as ex:
            log.e(ex)
    return None


def find_by_tag_from_driver(driver: webdriver.Chrome, tag: str) -> List[WebElement]:
    if driver:
        try:
            els = driver.find_elements(By.TAG_NAME, tag)
            if els:
                return els
        except Exception as ex:
            log.e(ex)
    return []


def get_by_tag_from_driver(driver: webdriver.Chrome, tag: str) -> Optional[WebElement]:
    if driver:
        try:
            el = driver.find_element(By.TAG_NAME, tag)
            if el:
                return el
        except Exception as ex:
            log.e(ex)
    return None
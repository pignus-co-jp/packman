# -*- coding: utf-8 -*-

from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from .. import log


def find_by_class_from_driver(chromedriver: webdriver.Chrome, classname: str) -> List[WebElement]:
    p1 = By.CLASS_NAME
    p2 = classname
    if ' ' in classname:
        classes = [c.strip() for c in classname.split() if c.strip()]        
        escaped_classes = [c.replace(':', r'\:') for c in classes]
        selector = '.' + '.'.join(escaped_classes)
        p1 = By.CSS_SELECTOR
        p2 = selector
    else:
        if ':' in classname:
            escaped_classname = classname.replace(':', r'\:')
            selector = f".{escaped_classname}"
            p1 = By.CSS_SELECTOR
            p2 = selector
        else:
            p1 = By.CLASS_NAME
            p2 = classname

    if chromedriver:
        try:
            els = chromedriver.find_elements(p1, p2)
            if els:
                return els
        except Exception as ex:
            log.e(ex)
    return []


def get_by_class_from_driver(chromedriver: webdriver.Chrome, classname: str) -> Optional[WebElement]:
    p1 = By.CLASS_NAME
    p2 = classname
    if ' ' in classname:
        classes = [c.strip() for c in classname.split() if c.strip()]        
        escaped_classes = [c.replace(':', r'\:') for c in classes]
        selector = '.' + '.'.join(escaped_classes)
        p1 = By.CSS_SELECTOR
        p2 = selector
    else:
        if ':' in classname:
            escaped_classname = classname.replace(':', r'\:')
            selector = f".{escaped_classname}"
            p1 = By.CSS_SELECTOR
            p2 = selector
        else:
            p1 = By.CLASS_NAME
            p2 = classname

    if chromedriver:
        try:
            el = chromedriver.find_element(p1, p2)
            if el:
                return el
        except Exception as ex:
            log.e(ex)
    return None

def find_by_tag_from_driver(chromedriver: webdriver.Chrome, tag: str) -> List[WebElement]:
    if chromedriver:
        try:
            els = chromedriver.find_elements(By.TAG_NAME, tag)
            if els:
                return els
        except Exception as ex:
            log.e(ex)
    return []


def get_by_tag_from_driver(chromedriver: webdriver.Chrome, tag: str) -> Optional[WebElement]:
    if chromedriver:
        try:
            el = chromedriver.find_element(By.TAG_NAME, tag)
            if el:
                return el
        except Exception as ex:
            log.e(ex)
    return None


def find_by_xpath_from_driver(chromedriver: webdriver.Chrome, xpath: str) -> List[WebElement]:
    if chromedriver:
        try:
            els = chromedriver.find_elements(By.XPATH, xpath)
            if els:
                return els
        except Exception as ex:
            log.e(ex)
    return []


def get_by_xpath_from_driver(chromedriver: webdriver.Chrome, xpath: str) -> Optional[WebElement]:
    if chromedriver:
        try:
            el = chromedriver.find_element(By.XPATH, xpath)
            if el:
                return el
        except Exception as ex:
            log.e(ex)
    return None


def get_by_id_from_driver(chromedriver: webdriver.Chrome, id: str) -> Optional[WebElement]:
    if chromedriver:
        try:
            el = chromedriver.find_element(By.ID, id)
            if el:
                return el
        except Exception as ex:
            log.e(ex)
    return None


def find_by_class(element: WebElement, classname: str) -> List[WebElement]:
    p1 = By.CLASS_NAME
    p2 = classname
    if ' ' in classname:
        classes = [c.strip() for c in classname.split() if c.strip()]        
        escaped_classes = [c.replace(':', r'\:') for c in classes]
        selector = '.' + '.'.join(escaped_classes)
        p1 = By.CSS_SELECTOR
        p2 = selector
    else:
        if ':' in classname:
            escaped_classname = classname.replace(':', r'\:')
            selector = f".{escaped_classname}"
            p1 = By.CSS_SELECTOR
            p2 = selector
        else:
            p1 = By.CLASS_NAME
            p2 = classname

    if element:
        try:
            els = element.find_elements(p1, p2)
            if els:
                return els
        except Exception as ex:
            log.e(ex)
    return []


def get_by_class(element: WebElement, classname: str) -> Optional[WebElement]:
    p1 = By.CLASS_NAME
    p2 = classname
    if ' ' in classname:
        classes = [c.strip() for c in classname.split() if c.strip()]        
        escaped_classes = [c.replace(':', r'\:') for c in classes]
        selector = '.' + '.'.join(escaped_classes)
        p1 = By.CSS_SELECTOR
        p2 = selector
    else:
        if ':' in classname:
            escaped_classname = classname.replace(':', r'\:')
            selector = f".{escaped_classname}"
            p1 = By.CSS_SELECTOR
            p2 = selector
        else:
            p1 = By.CLASS_NAME
            p2 = classname

    if element:
        try:
            el = element.find_element(p1, p2)
            if el:
                return el
        except Exception as ex:
            log.e(ex)
    return None


def find_by_tag(element: WebElement, tag: str) -> List[WebElement]:
    if element:
        try:
            els = element.find_elements(By.TAG_NAME, tag)
            if els:
                return els
        except Exception as ex:
            log.e(ex)
    return []


def get_by_tag(element: WebElement, tag: str) -> Optional[WebElement]:
    if element:
        try:
            el = element.find_element(By.TAG_NAME, tag)
            if el:
                return el
        except Exception as ex:
            log.e(ex)
    return None


def find_by_xpath(element: WebElement, xpath: str) -> List[WebElement]:
    if element:
        try:
            els = element.find_elements(By.XPATH, xpath)
            if els:
                return els
        except Exception as ex:
            log.e(ex)
    return []


def get_by_xpath(element: WebElement, xpath: str) -> Optional[WebElement]:
    if element:
        try:
            el = element.find_element(By.XPATH, xpath)
            if el:
                return el
        except Exception as ex:
            log.e(ex)
    return None


def get_by_id(element: WebElement, id: str) -> Optional[WebElement]:
    if element:
        try:
            el = element.find_element(By.ID, id)
            if el:
                return el
        except Exception as ex:
            log.e(ex)
    return None

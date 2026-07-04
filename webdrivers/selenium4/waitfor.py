# -*- coding: utf-8 -*-
import time
from typing import Optional
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from .. import log

def page_load(chromedriver: webdriver.Chrome, timeout: int = 15) -> bool:
    try:
        WebDriverWait(chromedriver, timeout).until(
            lambda d: d.execute_script(
                "return document.readyState") == "complete"
        )
        return True
    except Exception as ex:
        log.e(ex)

    return False

def show_class(chromedriver: webdriver.Chrome, classname: str, timeout: int = 15) -> bool:
    # 複数クラスの場合はCSS_SELECTORに変換
    if ' ' in classname:
        classes = [c.strip() for c in classname.split() if c.strip()]
        
        # コロンをエスケープ（f-string外で処理）
        escaped_classes = [c.replace(':', r'\:') for c in classes]
        
        # CSSセレクタを構築
        selector = '.' + '.'.join(escaped_classes)
        locator = (By.CSS_SELECTOR, selector)
    else:
        # 単一クラスでもコロンがある場合はエスケープ
        if ':' in classname:
            escaped_classname = classname.replace(':', r'\:')
            selector = f".{escaped_classname}"
            locator = (By.CSS_SELECTOR, selector)
        else:
            locator = (By.CLASS_NAME, classname)

    try:
        WebDriverWait(chromedriver, timeout).until(EC.presence_of_element_located(locator))
        return True
    except Exception as ex:
        log.e(ex)
    
    return False

def show_xpath(chromedriver: webdriver.Chrome, xpath: str, timeout: int = 15) -> bool:
    try:
        WebDriverWait(chromedriver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return True
    except Exception as ex:
        log.e(ex)
    
    return False

def show_id(chromedriver: webdriver.Chrome, id: str, timeout: int = 15) -> bool:
    try:
        WebDriverWait(chromedriver, timeout).until(
            EC.presence_of_element_located((By.ID, id))
        )
        return True
    except Exception as ex:
        log.e(ex)
    
    return False


def click_xpath(chromedriver: webdriver.Chrome, xpath: str, timeout: int = 15) -> bool:
    try:
        WebDriverWait(chromedriver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        return True
    except Exception as ex:
        log.e(ex)
    
    return False


def click_id(chromedriver: webdriver.Chrome, id: str, timeout: int = 15) -> bool:
    try:
        WebDriverWait(chromedriver, timeout).until(
            EC.element_to_be_clickable((By.ID, id))
        )
        return True
    except Exception as ex:
        log.e(ex)
    
    return False



def network_idle(chromedriver: webdriver.Chrome, idle_time: int = 2, timeout: int =30):
    """
    ネットワーク通信が落ち着くまで待つ
    
    Args:
        idle_time: 通信が止まってから待つ秒数
        timeout: 最大待機時間
    """
    start_time = time.time()
    last_activity = time.time()
    
    # 初期のリソース数
    initial_count = chromedriver.execute_script(
        'return window.performance.getEntriesByType("resource").length'
    )
    
    while time.time() - start_time < timeout:
        # 現在のリソース数
        current_count = chromedriver.execute_script(
            'return window.performance.getEntriesByType("resource").length'
        )
        
        # リソースが増えた = 新しい通信があった
        if current_count > initial_count:
            last_activity = time.time()
            initial_count = current_count
        
        # 指定時間通信がなければ完了
        if time.time() - last_activity >= idle_time:
            log.d("ネットワークアイドル検出")
            return True
        
        time.sleep(0.5)
    
    log.w("ネットワークアイドル待機タイムアウト")
    return False

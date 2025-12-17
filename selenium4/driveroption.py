# -*- coding: utf-8 -*-

from typing import Optional
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


class DriverOption():
    def __init__(self,
                 is_headless: bool = True,
                 download_dir: Optional[str] = None,
                 chrome_log_filepath: Optional[str] = None,
                 ):
        self.is_headless = is_headless
        self.download_dir = download_dir
        self.chrome_log_filepath = chrome_log_filepath
        pass

    def get_options(self) -> Optional[Options]:
        options = Options()
        if self.is_headless:
            options.add_argument('--headless')  # ヘッドレスモードで実行
            options.add_argument('--disable-gpu')  # ヘッドレスモードで推奨
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--lang=ja-JP")

        prefs = {
            "download.prompt_for_download": False,  # ダウンロードダイアログを無効化
            "profile.default_content_settings.popups": 0,  # ポップアップを無効化
            "profile.default_content_setting_values.automatic_downloads": 1  # 自動ダウンロードを許可
        }
        if self.download_dir:
            prefs["download.default_directory"] = self.download_dir

        options.add_experimental_option("prefs", prefs)
        return options

    def get_service(self) -> Service:
        if self.chrome_log_filepath:
            return Service(log_output=self.chrome_log_filepath)
        return None

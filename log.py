# -*- coding: utf-8 -*-

import os
import logging
from typing import List

'''
| レベル名 | 数値 | 備考 |
|---------|------|------|
| CRITICAL | 50 | 公式 |
| ERROR | 40 | 公式 |
| WARNING | 30 | 公式 |
| INFO | 20 | 公式 |
| DEBUG | 10 | 公式 |
| NOTSET | 0 | 公式 |
'''

DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
FULL_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d <%(funcName)s> %(message)s"
ERROR_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s"


# -------------------------
# ロガー初期化
# -------------------------
__logger = logging.getLogger(__name__)
__logger.setLevel(logging.DEBUG)  # ロガー自体は常にDEBUGレベルに設定し、ハンドラーでフィルタリング

stream_handlers: List[logging.StreamHandler] = []
file_handlers: List[logging.FileHandler] = []


def _set_handler(handler: logging.Handler, level: int) -> logging.Handler:
    """ハンドラーにレベル、フィルター、フォーマッターを設定"""
    handler.setLevel(level)
    handler.addFilter(lambda record: record.levelno == level)

    # レベルに応じたフォーマット選択
    if level == logging.INFO:
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
    elif level in (logging.WARNING, logging.ERROR):
        formatter = logging.Formatter(ERROR_LOG_FORMAT)
    else:
        formatter = logging.Formatter(FULL_LOG_FORMAT)

    handler.setFormatter(formatter)

    # ハンドラーに元のレベルを保存
    handler._original_level = level

    __logger.addHandler(handler)
    return handler


# 初期ハンドラー設定
for level in (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR):
    stream_handlers.append(_set_handler(logging.StreamHandler(), level))


def start_debug_mode():
    """Debugモード切り替え（全ハンドラーを有効化）"""
    for handler in stream_handlers + file_handlers:
        handler.setLevel(handler._original_level)


def start_default_mode():
    """通常モード切り替え（DEBUGハンドラーを無効化）"""
    for handler in stream_handlers + file_handlers:
        if handler._original_level == logging.DEBUG:
            handler.setLevel(logging.CRITICAL + 1)  # 実質無効化
        else:
            handler.setLevel(handler._original_level)


def enable_file_output(
    filepath: str,
    level: int = logging.INFO,
    encoding: str = "utf-8"
) -> logging.FileHandler:
    """ファイルハンドラーを追加"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    handler = logging.FileHandler(filepath, encoding=encoding)
    return _set_handler(handler, level)


def set_logfile_all(filepath: str = os.path.join("logs", "packman.log")):
    """全レベルのファイル出力を設定"""
    for level in (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR):
        file_handlers.append(enable_file_output(filepath, level))


def d(*args):
    """DEBUGログ出力"""
    msg = " ".join(str(a) for a in args)
    __logger.debug(msg, stacklevel=2)


def i(*args):
    """INFOログ出力"""
    msg = " ".join(str(a) for a in args)
    __logger.info(msg, stacklevel=2)


def w(*args):
    """WARNINGログ出力"""
    msg = " ".join(str(a) for a in args)
    __logger.warning(msg, stacklevel=2)


def e(*args):
    """ERRORログ出力"""
    msg = " ".join(str(a) for a in args)
    __logger.error(msg, stacklevel=2)


def c(*args):
    """CRITICALログ出力（追加）"""
    msg = " ".join(str(a) for a in args)
    __logger.critical(msg, stacklevel=2)


# デフォルトモードで開始
start_default_mode()

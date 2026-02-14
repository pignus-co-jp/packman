# -*- coding: utf-8 -*-

import logging

DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
FULL_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d <%(funcName)s> %(message)s"
ERROR_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s"


# -------------------------
# ロガー初期化
# -------------------------
logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)  # 全レベルを通す


# -------------------------
# INFO ハンドラ
# -------------------------
__info_handler = logging.StreamHandler()
__info_handler.setLevel(logging.INFO)
__info_handler.addFilter(lambda record: record.levelno == logging.INFO)
__info_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
logger.addHandler(__info_handler)


# -------------------------
# WARNING ハンドラ
# -------------------------
__warn_handler = logging.StreamHandler()
__warn_handler.setLevel(logging.WARNING)
__warn_handler.addFilter(lambda record: record.levelno == logging.WARNING)
__warn_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
logger.addHandler(__warn_handler)


# -------------------------
# ERROR ハンドラ
# -------------------------
__error_handler = logging.StreamHandler()
__error_handler.setLevel(logging.ERROR)
__error_handler.addFilter(lambda record: record.levelno == logging.ERROR)
__error_handler.setFormatter(logging.Formatter(ERROR_LOG_FORMAT))
logger.addHandler(__error_handler)


# -------------------------
# DEBUG ハンドラ（デフォルトでは無効）
# -------------------------
__debug_handler = logging.StreamHandler()
__debug_handler.setLevel(logging.DEBUG)
__debug_handler.addFilter(lambda record: record.levelno == logging.DEBUG)
__debug_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
# startDebugMode() で addHandler する


# -------------------------
# Debug モード切り替え
# -------------------------
def startDebugMode():
    """DEBUG モードでは FULL_LOG_FORMAT を使う"""
    __debug_handler.setFormatter(logging.Formatter(FULL_LOG_FORMAT))
    logger.addHandler(__debug_handler)


# -------------------------
# ラッパ関数
# -------------------------
def d(*args):
    msg = " ".join(str(a) for a in args)
    logger.debug(msg, stacklevel=2)


def w(*args):
    msg = " ".join(str(a) for a in args)
    logger.warning(msg, stacklevel=2)


def i(*args):
    msg = " ".join(str(a) for a in args)
    logger.info(msg, stacklevel=2)


def e(*args):
    msg = " ".join(str(a) for a in args)
    logger.error(msg, stacklevel=2)
# -*- coding: utf-8 -*-

import inspect
from datetime import datetime

def _is_toplevel(function_name: str) -> bool:
    if function_name == "<module>" or function_name == "<cell line: 0>":
        return True
    return False


def d(*arg):
    function_name = ""
    try:
        frame = inspect.currentframe().f_back
        function_name = frame.f_code.co_name
        if _is_toplevel(function_name):
            function_name = "main"
    except Exception as ex:
        pass
    print(datetime.now().strftime("%H:%M:%S.%f")[:-3], f"<{function_name}>", *arg)


def i(*arg):
    function_name = ""
    try:
        frame = inspect.currentframe().f_back
        function_name = frame.f_code.co_name
        if _is_toplevel(function_name):
            function_name = "main"
    except Exception as ex:
        pass
    print(datetime.now().strftime("%H:%M:%S.%f")[:-3], f"<{function_name}>", *arg)


def e(*arg):
    function_name = ""
    try:
        frame = inspect.currentframe().f_back
        function_name = frame.f_code.co_name
        if _is_toplevel(function_name):
            function_name = "main"
    except Exception as ex:
        pass
    print(datetime.now().strftime("%H:%M:%S.%f")[:-3], f"<{function_name}>", *arg)


def td(tag, *arg):
    function_name = ""
    try:
        frame = inspect.currentframe().f_back
        function_name = frame.f_code.co_name
        if _is_toplevel(function_name):
            function_name = "main"
    except Exception as ex:
        print(ex)
    print(datetime.now().strftime("%H:%M:%S.%f")[:-3], f"[{tag}]", f"<{function_name}>", *arg)


def ti(tag, *arg):
    function_name = ""
    try:
        frame = inspect.currentframe().f_back
        function_name = frame.f_code.co_name
        if _is_toplevel(function_name):
            function_name = "main"
    except Exception as ex:
        print(ex)
    print(datetime.now().strftime("%H:%M:%S.%f")[:-3], f"[{tag}]", f"<{function_name}>", *arg)


def te(tag, *arg):
    function_name = ""
    try:
        frame = inspect.currentframe().f_back
        function_name = frame.f_code.co_name
        if _is_toplevel(function_name):
            function_name = "main"
    except Exception as ex:
        print(ex)
    print(datetime.now().strftime("%H:%M:%S.%f")[:-3], f"[{tag}]", f"<{function_name}>", *arg)

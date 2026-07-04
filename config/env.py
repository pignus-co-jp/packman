import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


def get_config(keys: List):
    setting = {}
    for key in keys:
        setting[key] = os.getenv(key)
    return setting


def get_env_by_key(key):
    return os.getenv(key)

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


def get_by_key(key) -> Optional[str]:
    return os.getenv(key)

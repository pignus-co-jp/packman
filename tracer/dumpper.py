from typing import Optional
import json
import os
import time

from .. import log


def jsondumpper(dumpper, filepath: Optional[str] = None):
    try:
        dumpfilepath = os.path.join("logs", "dumpper", "json", str(
            int(time.time() * 1000))+"_jsondump.json")

        if filepath and len(filepath) > 1:
            dumpfilepath = filepath
        os.makedirs(os.path.dirname(dumpfilepath), exist_ok=True)
        with open(dumpfilepath, "w", encoding="utf-8") as f:
            json.dump(dumpper, f, ensure_ascii=False, indent=2)
    except Exception as ex:
        log.e("jsondumpper", ex)


def textdumpper(dumpper, filepath: Optional[str] = None):
    try:
        dumpfilepath = os.path.join("logs", "dumpper", "text", str(
            int(time.time() * 1000))+"_dump.txt")

        if filepath and len(filepath) > 1:
            dumpfilepath = filepath
        os.makedirs(os.path.dirname(dumpfilepath), exist_ok=True)
        with open(dumpfilepath, "w", encoding="utf-8") as f:
            f.write(str(dumpper))
    except Exception as ex:
        log.e("textdumpper", ex)

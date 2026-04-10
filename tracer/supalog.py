import requests
import socket
import os
import sys
from packman import log
from packman.config import env

SUPABASE_ANON_KEY = env.get_env_by_key("SUPABASE_ANON_KEY")


def get_terminal_sig():
    host = ""
    pid = ""
    psname = ""
    try:
        host = str(socket.gethostname())
    except:
        pass
    try:
        pid = str(os.getpid())
    except:
        pass
    try:
        psname = os.path.basename(sys.argv[0])
    except:
        pass
    return "["+host+"]["+pid+"]["+psname+"]"


def supalog(level: str = "INFO", tag: str = "", message: str = ""):
    if SUPABASE_ANON_KEY:
        try:
            x = requests.post("https://frezwqcatjxucdsmtsto.supabase.co/functions/v1/logging-api",
                              headers={
                                  "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
                                  "Content-Type": "application/json",
                              },
                              json={
                                  "level": level,
                                  "tag": tag,
                                  "message": message,
                                  "terminal": get_terminal_sig()
                              },
                              timeout=5)
        except Exception as ex:
            log.e("supalog", ex)


def dlog(tag: str = "", message: str = ""):
    log.d(tag, message)
    supalog(level="DEBUG", tag=tag, message=message)


def ilog(tag: str = "", message: str = ""):
    log.i(tag, message)
    supalog(level="INFO", tag=tag, message=message)


def wlog(tag: str = "", message: str = ""):
    log.w(tag, message)
    supalog(level="WARN", tag=tag, message=message)


def elog(tag: str = "", message: str = ""):
    log.e(tag, message)
    supalog(level="ERROR", tag=tag, message=message)

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = str(Path(__file__).parent.parent)
load_dotenv()


class Config(object):
    LOG_LEVEL = os.environ.get("LOG_LEVEL", 'INFO')
    APP_DIR = os.path.abspath(os.path.dirname(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.
    CSRF_ENABLED = True
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")

    def __setitem__(self, key, item):
        self.__dict__[key] = item

    def __getitem__(self, key):
        return self.__dict__[key]
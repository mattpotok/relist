# Rename this program as 'relist'

import logging.config
import sys
from pathlib import Path

import tomlkit
from fake_useragent import UserAgent
from selenium import webdriver

from relist.sites import craigslist

CONFIG_PATH = Path.home() / ".config/relist/settings.toml"
LOG_PATH = Path.home() / ".local/share/relist/relist.log"

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "format": "%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
        },
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": str(LOG_PATH),
            "formatter": "default",
            "level": "DEBUG",
        },
        "stdout": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO",
        },
    },
    "loggers": {
        "": {
            "handlers": ["file", "stdout"],
            "level": "DEBUG",
        },
        "craigslist": {
            "handlers": ["file", "stdout"],
            "level": "DEBUG",
        },
    },
}


def main():
    # TODO make this headless
    # TODO add a fake user agent
    # TODO make the browser choice configurable
    log_dir_path = LOG_PATH.parent
    log_dir_path.mkdir(parents=True, exist_ok=True)

    logging.config.dictConfig(LOGGING_CONFIG)

    try:
        data = CONFIG_PATH.read_text()
        config = tomlkit.loads(data)
    except FileNotFoundError:
        logging.exception(f"Unable to read config file '{CONFIG_PATH}")
        sys.exit(1)
    except tomlkit.exceptions.ParseError:
        logging.exception(f"Unable to parse config file '{CONFIG_PATH}")
        sys.exit(1)
    except Exception:
        logging.exception("Unknown exception occured")
        sys.exit(1)

    # TODO make this configurable
    # TODO allow for options here
    options = webdriver.FirefoxOptions()
    options.headless = True
    options.add_argument(f"user-agent={UserAgent().random}")
    browser = webdriver.Firefox()

    if craigslist_config := config.get("craigslist"):
        craigslist.relist(browser, craigslist_config)

    if facebook_config := config.get("facebook"):
        pass

    browser.close()

    CONFIG_PATH.write_text(tomlkit.dumps(config))


if __name__ == "__main__":
    main()

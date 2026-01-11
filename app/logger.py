"""
logger_setup.py
===============

Logger setup utility.

Sets up application logging to both file and stdout using the
configuration in config/logger_config.json.

Features:
- Daily rotated log files named by date.
- Automatic deletion of log files older than 7 days.
"""

import json
import logging.config
import pathlib
from datetime import datetime


def setup_logging():
    """
    Configure logging for the application.

    Reads the JSON configuration, ensures the logs directory exists,
    sets up the log file name based on the current date, and applies
    the logging configuration.

    :return: None
    """
    log_dir = pathlib.Path("logs")
    log_dir.mkdir(exist_ok=True)

    config_file = pathlib.Path("config/logger_config.json")
    with open(config_file) as f_in:
        config = json.load(f_in)

    today = datetime.now().strftime("%Y-%m-%d")
    log_path = log_dir / f"app_{today}.log"
    config["handlers"]["file"]["filename"] = str(log_path)

    logging.config.dictConfig(config)

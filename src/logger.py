"""
Logger class that sets up file and stdout logging using the
config/logger_config.json file.

File logs are named with the date of creation and are automatically
rotated daily, with logs older than 7 days being deleted.
"""

import json
import logging.config
import pathlib
from datetime import datetime


class Logger:
    @staticmethod
    def setup_logging():
        log_dir = pathlib.Path("logs")
        log_dir.mkdir(exist_ok=True)

        config_file = pathlib.Path("../config/logger_config.json")
        with open(config_file) as f_in:
            config = json.load(f_in)

        today = datetime.now().strftime("%Y-%m-%d")
        log_path = log_dir / f"app_{today}.log"
        config["handlers"]["file"]["filename"] = str(log_path)

        logging.config.dictConfig(config)

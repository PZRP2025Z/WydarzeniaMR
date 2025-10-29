from logger import Logger
import logging


logger = logging.getLogger(__name__)


def main():
    Logger.setup_logging()
    logging.debug("debug message", extra={"x": "hello"})
    logging.info("info message")
    logging.warning("warning message", "")
    logging.error("error message")
    logging.critical("critical message")


if __name__ == "__main__":
    main()

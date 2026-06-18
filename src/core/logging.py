import logging
import sys


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("SmartShelf")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


logger = setup_logger()
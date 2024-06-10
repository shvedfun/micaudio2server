import logging
import sys
from config import log_format


def get_logger(log_level) -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    formatter = logging.Formatter(
        fmt=log_format,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

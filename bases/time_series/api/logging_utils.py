import logging
import sys

from loguru import logger
from time_series.settings import get_settings


class InterceptHandler(logging.Handler):
    """
    Intercepts standard logging messages and redirects them to loguru.

    From: https://pawamoy.github.io/posts/unify-logging-for-a-gunicorn-uvicorn-app/#uvicorn-only-version
    """

    def emit(self, record):
        # Get corresponding loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where the logging call originated
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging() -> None:
    settings = get_settings()

    # Intercept standard logging
    logging.root.handlers.clear()
    logging.root.addHandler(InterceptHandler())
    logging.root.setLevel(settings.log_level.value)

    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers.clear()
        logging.getLogger(name).propagate = True

    logger.configure(handlers=[{"sink": sys.stdout, "serialize": False}])

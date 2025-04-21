# pylint: disable=line-too-long

"""
Logger module for the CAC Core package.

This module provides a standardized logging configuration for all CAC components.
It creates loggers with consistent formatting and behavior, making it easy to
maintain uniform logging across the application.

The module exposes a simple factory function `new()` that returns a properly
configured logger instance that can be used throughout the application.

Example:
    >>> import cac_core
    >>> logger = cac_core.logger.new(__name__)
    >>> logger.info("Application started")
    2025-04-18 12:34:56 [INFO] (MainProcess MainThread) module:10: Application started
"""

import logging

def new(name, level=logging.INFO, format_string=None) -> logging.Logger:
    """
    Create and configure a logger for the cac class.

    Args:
        name (str): Name for the logger, typically __name__ from the calling module
        level (int, optional): Log level. Default is logging.INFO
        format_string (str, optional): Custom format string for log messages

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Only add handler if the logger doesn't already have handlers
    # TODO: this doesn't work; the handler will only be added once, and since we haven't parse the args yet,
    # the level will be set to INFO by default. We need to set the level to DEBUG if we want to see debug messages.
    if not logger.handlers:
        logger.setLevel(level)
        sh = logging.StreamHandler()

        # Use provided format or default
        if not format_string:
            if level == logging.DEBUG:
                format_string = "%(asctime)s [%(levelname)s] (%(processName)s %(threadName)s) %(module)s:%(lineno)d: %(message)s"
            else:
                format_string = "%(asctime)s [%(levelname)s] %(message)s"

        formatter = logging.Formatter(format_string)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    return logger

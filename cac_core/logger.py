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

    # Normalize string level names (e.g. "DEBUG") to their numeric value so
    # level comparisons below work regardless of how the caller passed it.
    if isinstance(level, str):
        level = logging.getLevelName(level.upper())
        if not isinstance(level, int):
            level = logging.INFO

    # Always update the level so callers can reconfigure after initial creation
    # (e.g., switching to DEBUG after parsing --verbose)
    logger.setLevel(level)

    # Choose the format: verbose (DEBUG or lower) gets the detailed layout.
    # Use <= so sub-DEBUG numeric levels also get the verbose format.
    if not format_string:
        if level <= logging.DEBUG:
            format_string = "%(asctime)s [%(levelname)s] (%(processName)s %(threadName)s) %(module)s:%(lineno)d: %(message)s"
        else:
            format_string = "%(asctime)s [%(levelname)s] %(message)s"

    formatter = logging.Formatter(format_string)

    if not logger.handlers:
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        logger.addHandler(sh)
    else:
        # Reconfigure existing handlers so a later new(name, level=DEBUG) call
        # (e.g. after parsing --verbose) actually updates the output format.
        for handler in logger.handlers:
            handler.setFormatter(formatter)

    # This logger has its own handler; don't also bubble records to ancestor
    # handlers (e.g. root) and emit every line twice. Set unconditionally so
    # propagation is disabled even when handlers were configured elsewhere.
    logger.propagate = False

    return logger

import logging

def new(name) -> logging.Logger:
    """
    Create and configure a logger for the cac class.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    sh = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] (%(processName)s %(threadName)s) %(module)s:%(lineno)d: %(message)s"
    )
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    return logger

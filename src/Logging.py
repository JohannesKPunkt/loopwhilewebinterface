#  Logging.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#
#

import logging

_global_log_level = "DEBUG"
_global_handler = None

def set_global_options(level, logfile):
    global _global_handler
    logging.basicConfig(format="%(asctime)-15s - %(name)s - %(levelname)s - %(message)s")
    if level is not None:
        _global_log_level = level
    
    logger = logging.getLogger("__main__")
    logger.setLevel(_global_log_level)
    logger.debug("Debug logging enabled")
    
    if logfile is not None:
        logger.info("Logging to file " + logfile)
        _global_handler = logging.FileHandler(logfile) #TODO use RotatingFileHandler instead
        
        formatter = logging.Formatter("%(asctime)-15s - %(name)s - %(levelname)s - %(message)s")
        _global_handler.setFormatter(formatter)


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(_global_log_level)
    if _global_handler is not None:
        logger.addHandler(_global_handler)
    return logger

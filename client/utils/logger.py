# client/utils/logger.py
import logging
from logging.handlers import RotatingFileHandler
import os
from config import LOG_LEVEL, LOG_FORMAT, LOG_FILE, LOG_DIR, MAX_LOG_SIZE, BACKUP_COUNT
def setup_logger(name="client"):
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    log_path = os.path.join(LOG_DIR, LOG_FILE)
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))
    if not logger.handlers:
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(file_handler)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(console_handler)
    return logger

# server/managers/log_manager.py
import os
import logging
from logging.handlers import RotatingFileHandler
class LogManager:
    def __init__(self, log_level="INFO", log_format="%(asctime)s - %(levelname)s - %(message)s"):
        self.log_level = log_level
        self.log_format = log_format
        self.logger = None
        self.log_callback = None
    def setup_logging(self):
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        logger = logging.getLogger()
        logger.setLevel(getattr(logging, self.log_level))
        file_handler = logging.FileHandler(os.path.join(log_dir, "server.log"))
        file_handler.setFormatter(logging.Formatter(self.log_format))
        logger.addHandler(file_handler)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(self.log_format))
        logger.addHandler(console_handler)
        self.logger = logger
        return logger
    def set_callback(self, callback):
        self.log_callback = callback
    def log(self, message, level="INFO"):
        if self.logger:
            log_method = getattr(self.logger, level.lower(), self.logger.info)
            log_method(message)
        if self.log_callback:
            self.log_callback(message)

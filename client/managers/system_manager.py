# client/managers/system_manager.py
import logging
from collectors.system_collector import SystemCollector
logger = logging.getLogger("client.system_manager")
class SystemManager:
    def __init__(self):
        self.collector = SystemCollector()
        self.running = False
        self.cached_info = None
    def start(self):
        self.running = True
        logger.info("Iniciando gerenciador de sistema")
        self.cached_info = self.collector.collect_all()
    def stop(self):
        self.running = False
        logger.info("Gerenciador de sistema parado")
    def get_info(self):
        if not self.cached_info:
            self.cached_info = self.collector.collect_all()
        return self.cached_info
    def get_usage(self):
        return self.collector.collect_usage_info()
    def get_disk_info(self):
        return self.collector.collect_disk_info()
    def get_network_info(self):
        return self.collector.collect_network_info()

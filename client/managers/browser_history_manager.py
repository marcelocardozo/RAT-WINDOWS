# client/managers/browser_history_manager.py
import logging
import threading
from collectors.browser_history_collector import BrowserHistoryCollector
logger = logging.getLogger("client.browser_history_manager")
class BrowserHistoryManager:
    def __init__(self):
        self.collector = BrowserHistoryCollector()
        self.running = False
        self.collection_lock = threading.Lock()
        self.last_error = None
    def start(self):
        self.running = True
        logger.info("Browser history manager started")
    def stop(self):
        self.running = False
        logger.info("Browser history manager stopped")
    def collect_history(self):
        if not self.running:
            logger.warning("Coleta ignorada: gerenciador parado")
            return json.dumps({"error": "Gerenciador parado"})
        lock_acquired = False
        try:
            lock_acquired = self.collection_lock.acquire(blocking=False)
            if not lock_acquired:
                logger.info("Já existe uma coleta em andamento, ignorando solicitação")
                return json.dumps({"error": "Coleta já em andamento"})
            logger.info("Iniciando coleta de histórico de navegadores")
            history_data = self.collector.collect_all_browsers_history()
            return history_data
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Erro ao coletar histórico de navegadores: {str(e)}")
            return json.dumps({"error": str(e)})
        finally:
            if lock_acquired:
                self.collection_lock.release()

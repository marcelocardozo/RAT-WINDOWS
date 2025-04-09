# client/managers/screenshot_manager.py
import logging
import threading
from collectors.screenshot_collector import ScreenshotCollector
logger = logging.getLogger("client.screenshot_manager")
class ScreenshotManager:
    def __init__(self):
        self.collector = ScreenshotCollector()
        self.running = False
        self.capture_enabled = True
        self.capture_lock = threading.Lock()
        self.current_capture_id = None
    def start(self):
        self.running = True
        self.capture_enabled = True
        logger.info("Iniciando gerenciador de capturas de tela")
    def stop(self):
        self.running = False
        logger.info("Gerenciador de capturas de tela parado")
    def stop_capture(self):
        self.capture_enabled = False
        logger.info("Capturas de tela desabilitadas")
    def enable_capture(self):
        self.capture_enabled = True
        logger.info("Capturas de tela habilitadas")
    def capture(self):
        if not self.running or not self.capture_enabled:
            logger.warning("Captura ignorada: gerenciador parado ou capturas desabilitadas")
            return None
        lock_acquired = False
        try:
            lock_acquired = self.capture_lock.acquire(blocking=False)
            if not lock_acquired:
                logger.info("Já existe uma captura em andamento, ignorando solicitação")
                return None
            if not self.capture_enabled:
                logger.info("Capturas desabilitadas após adquirir lock")
                return None
            image_bytes = self.collector.capture()
            if image_bytes:
                logger.info(f"Captura realizada: {len(image_bytes) / 1024:.2f} KB")
            else:
                logger.error("Falha na captura")
            return image_bytes
        except Exception as e:
            logger.error(f"Erro ao capturar tela: {str(e)}")
            return None
        finally:
            if lock_acquired:
                self.capture_lock.release()

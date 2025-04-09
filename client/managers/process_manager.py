# client/managers/process_manager.py
import logging
from collectors.process_collector import ProcessCollector
from utils.process_utils import kill_process
logger = logging.getLogger("client.process_manager")
class ProcessManager:
    def __init__(self):
        self.collector = ProcessCollector()
        self.running = False
    def start(self):
        self.running = True
        logger.info("Iniciando gerenciador de processos")
    def stop(self):
        self.running = False
        logger.info("Gerenciador de processos parado")
    def get_process_list(self, detailed=False):
        return self.collector.get_process_list(detailed)
    def kill_process(self, pid):
        try:
            logger.info(f"Tentando encerrar processo com PID {pid}")
            pid = int(pid)
            result = kill_process(pid)
            if result:
                logger.info(f"Processo {pid} encerrado com sucesso")
            else:
                logger.error(f"Falha ao encerrar processo {pid}")
            return result
        except ValueError as e:
            logger.error(f"PID inválido: {pid}, erro: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erro ao encerrar processo {pid}: {str(e)}")
            return False

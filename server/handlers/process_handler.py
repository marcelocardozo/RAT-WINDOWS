# server/handlers/process_handler.py
import logging
import json
import struct
from core.protocol import *
logger = logging.getLogger("server.process_handler")
class ProcessHandler:
    def __init__(self, server):
        self.server = server
        self.process_manager = None
    def set_process_manager(self, process_manager):
        self.process_manager = process_manager
    def request_process_list(self, client_address, detailed=False):
        if client_address not in self.server.connection_manager.client_handlers:
            logger.error(f"Cliente não encontrado: {client_address}")
            return False
        return self.server.connection_manager.client_handlers[client_address].request_process_list(detailed)
    def request_kill_process(self, client_address, pid):
        if client_address not in self.server.connection_manager.client_handlers:
            logger.error(f"Cliente não encontrado: {client_address}")
            return False
        logger.info(f"Solicitando encerramento do processo {pid} para {client_address}")
        return self.server.connection_manager.client_handlers[client_address].request_kill_process(pid)
    def process_list_response(self, client_address, process_list):
        client_key = f"{client_address[0]}:{client_address[1]}"
        try:
            logger.info(f"Processando lista de {len(process_list)} processos de {client_key}")
            if self.process_manager:
                formatted_list = self.process_manager.process_list(client_key, process_list)
                if self.server.process_list_callback:
                    self.server.process_list_callback(client_address, formatted_list)
                    return True
            elif self.server.process_list_callback:
                self.server.process_list_callback(client_address, process_list)
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao processar lista de processos: {str(e)}")
            if self.server.process_list_callback:
                try:
                    self.server.process_list_callback(client_address, process_list)
                    return True
                except:
                    pass
            return False

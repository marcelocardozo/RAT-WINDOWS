# server/core/connection_manager.py
import socket
import logging
import threading
from handlers.client_handler import ClientHandler
logger = logging.getLogger("server.connection_manager")
class ConnectionManager:
    def __init__(self, server):
        self.server = server
        self.clients = {}
        self.client_sockets = {}
        self.client_handlers = {}
        self.monitoring_status = {}
    def accept_connections(self):
        logger.info("Iniciando thread de aceitação de conexões")
        while self.server.is_running:
            try:
                client_socket, client_address = self.server.server_socket.accept()
                logger.info(f"Nova conexão de {client_address[0]}:{client_address[1]}")
                client_key = f"{client_address[0]}:{client_address[1]}"
                self.monitoring_status[client_key] = False
                handler = ClientHandler(self.server, client_socket, client_address)
                self.client_handlers[client_address] = handler
                handler.start()
            except OSError:
                if self.server.is_running:
                    logger.error("Socket do servidor fechado inesperadamente")
                break
            except Exception as e:
                if self.server.is_running:
                    logger.error(f"ERRO ao aceitar conexão: {str(e)}")
        logger.info("Thread de aceitação de conexões encerrada")
    def start_accept_thread(self):
        accept_thread = threading.Thread(target=self.accept_connections)
        accept_thread.daemon = True
        accept_thread.start()
        return accept_thread
    def disconnect_all_clients(self):
        for client_addr in list(self.client_handlers.keys()):
            try:
                for _ in range(3):
                    try:
                        self.client_handlers[client_addr].send_command({"action": "stop_screenshot"})
                    except:
                        pass
                    import time
                    time.sleep(0.05)
                try:
                    self.client_handlers[client_addr].stop()
                except Exception as e:
                    logger.error(f"Erro ao parar manipulador de cliente: {str(e)}")
            except Exception as e:
                logger.error(f"Erro ao desconectar cliente: {str(e)}")
    def clear_all_clients(self):
        self.clients.clear()
        self.client_sockets.clear()
        self.client_handlers.clear()
        self.monitoring_status.clear()
    def get_client_count(self):
        return len(self.clients)
    def get_clients(self):
        return self.clients.copy()
    def get_client_handler(self, client_address):
        return self.client_handlers.get(client_address)
    def register_client(self, client_address, client_socket, client_info):
        self.client_sockets[client_address] = client_socket
        self.clients[client_address] = client_info
        client_key = f"{client_address[0]}:{client_address[1]}"
        self.monitoring_status[client_key] = False
    def unregister_client(self, client_address):
        if client_address in self.clients:
            del self.clients[client_address]
        if client_address in self.client_sockets:
            try:
                self.client_sockets[client_address].close()
            except:
                pass
            del self.client_sockets[client_address]
        if client_address in self.client_handlers:
            del self.client_handlers[client_address]
        client_key = f"{client_address[0]}:{client_address[1]}"
        if client_key in self.monitoring_status:
            del self.monitoring_status[client_key]

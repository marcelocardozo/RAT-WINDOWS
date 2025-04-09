# client/core/client_connector.py
import socket
import json
import logging
import time
import threading
from config import SOCKET_TIMEOUT, RECONNECT_DELAY_INITIAL, RECONNECT_DELAY_MAX
logger = logging.getLogger("client.client_connector")
class ClientConnector:
    def __init__(self, server_host, server_port):
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = None
        self.is_connected = False
        self.running = False
        self.reconnect_delay = RECONNECT_DELAY_INITIAL
        self.socket_lock = threading.Lock()
        self.command_handler = None
        self.data_sender = None
        self.last_reconnect_attempt = 0
    def set_handlers(self, command_handler, data_sender):
        self.command_handler = command_handler
        self.data_sender = data_sender
    def connect(self, system_info):
        if self.is_connected:
            return True
        try:
            with self.socket_lock:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.settimeout(SOCKET_TIMEOUT)
                self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                if hasattr(socket, 'TCP_KEEPIDLE'):
                    self.client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 30)
                if hasattr(socket, 'TCP_KEEPINTVL'):
                    self.client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 5)
                if hasattr(socket, 'TCP_KEEPCNT'):
                    self.client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)
                self.client_socket.connect((self.server_host, self.server_port))
                self.client_socket.send(json.dumps(system_info).encode('utf-8'))
                response = self.client_socket.recv(1024)
                if not response:
                    raise Exception("Nenhuma resposta recebida do servidor")
                response_data = json.loads(response.decode('utf-8'))
                if response_data.get("status") == "connected":
                    self.is_connected = True
                    logger.info(f"Conectado ao servidor {self.server_host}:{self.server_port}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Erro ao conectar ao servidor: {str(e)}")
            self._cleanup_socket()
            return False
    def disconnect(self):
        self._cleanup_socket()
        self.is_connected = False
    def _cleanup_socket(self):
        with self.socket_lock:
            if self.client_socket:
                try:
                    self.client_socket.close()
                except:
                    pass
                self.client_socket = None
    def start_communication(self):
        self.running = True
        comm_thread = threading.Thread(target=self._communication_loop)
        comm_thread.daemon = True
        comm_thread.start()
        return comm_thread
    def _communication_loop(self):
        while self.running:
            if not self.is_connected:
                self._try_reconnect()
                continue
            try:
                if self.data_sender:
                    try:
                        self.data_sender.send_updates()
                    except Exception as e:
                        logger.error(f"Erro ao enviar atualizações: {str(e)}")
                        self.is_connected = False
                        continue
                try:
                    self._check_server_messages()
                except ConnectionResetError:
                    logger.error("Conexão reiniciada, tentando reconectar")
                    self.is_connected = False
                    continue
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Erro na comunicação: {str(e)}")
                self.is_connected = False
                self._cleanup_socket()
    def _try_reconnect(self):
        current_time = time.time()
        if current_time - self.last_reconnect_attempt < self.reconnect_delay:
            time.sleep(0.1)
            return False
        self.last_reconnect_attempt = current_time
        logger.info(f"Tentando reconectar em {self.reconnect_delay} segundos...")
        time.sleep(self.reconnect_delay)
        if not self.running:
            return False
        if self.data_sender and self.data_sender.reconnect():
            logger.info("Reconexão bem-sucedida")
            self.reconnect_delay = RECONNECT_DELAY_INITIAL
            return True
        else:
            logger.warning("Falha na reconexão, tentando novamente mais tarde")
            self.reconnect_delay = min(RECONNECT_DELAY_MAX, self.reconnect_delay + 5)
            return False
    def _check_server_messages(self):
        if not self.client_socket or not self.command_handler:
            return
        try:
            self.client_socket.settimeout(1.0)  # Changed from 0.1 to 1.0
            cmd_data = self.client_socket.recv(4)
            if not cmd_data:
                logger.warning("Conexão fechada pelo servidor")
                self.is_connected = False
                return
            if self.command_handler:
                self.command_handler.process_command(cmd_data)
        except socket.timeout:
            pass
        except ConnectionAbortedError as e:
            logger.error(f"Conexão abortada: {str(e)}")
            logger.info("Tentando reconectar automaticamente...")
            self.is_connected = False
            self._cleanup_socket()
        except ConnectionResetError as e:
            logger.error(f"Conexão reiniciada pelo peer: {str(e)}")
            logger.info("Tentando reconectar automaticamente...")
            self.is_connected = False
            self._cleanup_socket()
        except ConnectionError as e:
            logger.error(f"Erro de conexão: {str(e)}")
            self.is_connected = False
            self._cleanup_socket()
        except Exception as e:
            logger.error(f"Erro ao verificar mensagens: {str(e)}")
            if "WinError 10053" in str(e) or "WinError 10054" in str(e):
                logger.info("Conexão abortada pelo host, tentando reconectar...")
                self.is_connected = False
                self._cleanup_socket()

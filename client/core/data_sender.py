# client/core/data_sender.py
import json
import logging
import time
import struct
from utils.network_utils import send_binary_command
from core.protocol import CMD_UPDATE, CMD_PING
from config import UPDATE_INTERVAL, PING_INTERVAL
logger = logging.getLogger("client.data_sender")
class DataSender:
    def __init__(self, connector, system_manager):
        self.connector = connector
        self.system_manager = system_manager
        self.last_update_time = 0
        self.last_ping_time = 0
        self.last_cpu = None
        self.last_ram = None
    def send_updates(self):
        try:
            self._send_system_updates()
            self._send_ping()
        except Exception as e:
            logger.error(f"Erro ao enviar atualizações: {str(e)}")
            raise
    def _send_system_updates(self):
        current_time = time.time()
        if current_time - self.last_update_time < UPDATE_INTERVAL:
            return False
        self.last_update_time = current_time
        try:
            update_info = self.system_manager.get_usage()
            try:
                cpu_value = float(update_info["cpu_usage"].rstrip('%'))
                ram_value = float(update_info["ram_usage"].rstrip('%'))
            except:
                cpu_value = -1
                ram_value = -1
            should_update = False
            if self.last_cpu is None or self.last_ram is None:
                should_update = True
            elif abs(cpu_value - self.last_cpu) >= 1.0 or abs(ram_value - self.last_ram) >= 1.0:
                should_update = True
            if should_update:
                self.last_cpu = cpu_value
                self.last_ram = ram_value
                update_info["action"] = "update"
                json_data = json.dumps(update_info).encode('utf-8')
                socket = self.connector.client_socket
                if socket:
                    header = struct.pack('>I', CMD_UPDATE)
                    size = struct.pack('>I', len(json_data))
                    socket.sendall(header + size + json_data)
                    return True
            return False
        except Exception as e:
            logger.error(f"Erro ao enviar atualização: {str(e)}")
            raise
    def _send_ping(self):
        current_time = time.time()
        if current_time - self.last_ping_time < PING_INTERVAL:
            return False
        self.last_ping_time = current_time
        socket = self.connector.client_socket
        if socket:
            try:
                return send_binary_command(socket, CMD_PING)
            except Exception as e:
                logger.error(f"Erro ao enviar ping: {str(e)}")
                raise
        return False
    def reconnect(self):
        try:
            system_info = self.system_manager.get_info()
            return self.connector.connect(system_info)
        except Exception as e:
            logger.error(f"Erro ao tentar reconectar: {str(e)}")
            raise

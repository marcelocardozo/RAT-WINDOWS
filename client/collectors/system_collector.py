# client/collectors/system_collector.py
import os
import sys
import platform
import socket
import psutil
import getpass
from datetime import datetime
import logging
from utils.system_utils import get_machine_info, get_cpu_info, get_memory_info, get_disk_info
from utils.network_utils import get_ip_address
logger = logging.getLogger("client.system_collector")
class SystemCollector:
    def collect_basic_info(self):
        try:
            machine_info = get_machine_info()
            basic_info = {
                "hostname": socket.gethostname(),
                "username": getpass.getuser(),
                "os": machine_info["os"],
                "os_version": machine_info["version"],
                "platform": platform.platform(),
                "architecture": platform.machine(),
                "python_version": sys.version.split()[0],
                "cpu_count": psutil.cpu_count(logical=True),
                "total_ram": round(psutil.virtual_memory().total / (1024 ** 3), 2),
                "ip_address": get_ip_address(),
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
            }
            return basic_info
        except Exception as e:
            logger.error(f"Erro ao coletar informações básicas: {str(e)}")
            return {"error": str(e)}
    def collect_disk_info(self):
        return get_disk_info()
    def collect_network_info(self):
        try:
            net_io = psutil.net_io_counters()
            return {
                "bytes_sent": round(net_io.bytes_sent / (1024 ** 2), 2),
                "bytes_recv": round(net_io.bytes_recv / (1024 ** 2), 2),
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            }
        except Exception as e:
            logger.error(f"Erro ao coletar informações de rede: {str(e)}")
            return {"error": str(e)}
    def collect_usage_info(self):
        try:
            return {
                "cpu_usage": f"{psutil.cpu_percent(interval=0.5)}%",
                "ram_usage": f"{psutil.virtual_memory().percent}%"
            }
        except Exception as e:
            logger.error(f"Erro ao coletar informações de uso: {str(e)}")
            return {"cpu_usage": "N/A", "ram_usage": "N/A"}
    def collect_all(self):
        try:
            info = self.collect_basic_info()
            info["disks"] = self.collect_disk_info()
            info["network"] = self.collect_network_info()
            usage = self.collect_usage_info()
            info["cpu_usage"] = usage["cpu_usage"]
            info["ram_usage"] = usage["ram_usage"]
            return info
        except Exception as e:
            logger.error(f"Erro ao coletar informações do sistema: {str(e)}")
            return {"error": str(e)}

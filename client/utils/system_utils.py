# client/utils/system_utils.py
import os
import platform
import psutil
import socket
import logging
from utils.network_utils import get_ip_address
logger = logging.getLogger("client.system_utils")
def get_system_name():
    return platform.system()
def get_os_version():
    if platform.system() == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            build = winreg.QueryValueEx(key, "CurrentBuild")[0]
            if int(build) >= 22000:
                return f"Windows 11 ({platform.version()})"
            else:
                return f"{platform.system()} {platform.release()} ({platform.version()})"
        except Exception as e:
            logger.warning(f"Erro ao verificar versão do Windows no registro: {str(e)}")
            return f"{platform.system()} {platform.release()} ({platform.version()})"
    else:
        return f"{platform.system()} {platform.release()} ({platform.version()})"
def get_machine_info():
    os_version = get_os_version()
    system_info = {
        "system": platform.system(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "hostname": socket.gethostname(),
        "ip_address": get_ip_address()
    }
    if "Windows 11" in os_version:
        system_info["release"] = "11"
        system_info["os"] = "Windows 11"
        system_info["version"] = platform.version()
    else:
        system_info["release"] = platform.release()
        system_info["os"] = f"{platform.system()} {platform.release()}"
        system_info["version"] = platform.version()
    return system_info
def get_cpu_info():
    try:
        return {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "usage_percent": psutil.cpu_percent(interval=0.5)
        }
    except Exception as e:
        logger.error(f"Erro ao obter informações da CPU: {str(e)}")
        return {"error": str(e)}
def get_memory_info():
    try:
        mem = psutil.virtual_memory()
        return {
            "total": mem.total,
            "total_gb": round(mem.total / (1024**3), 2),
            "available": mem.available,
            "available_gb": round(mem.available / (1024**3), 2),
            "percent": mem.percent
        }
    except Exception as e:
        logger.error(f"Erro ao obter informações de memória: {str(e)}")
        return {"error": str(e)}
def get_disk_info():
    try:
        disks = []
        for part in psutil.disk_partitions(all=False):
            if os.name == 'nt' and ('cdrom' in part.opts or part.fstype == ''):
                continue
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "percent": usage.percent
            })
        return disks
    except Exception as e:
        logger.error(f"Erro ao obter informações de disco: {str(e)}")
        return []

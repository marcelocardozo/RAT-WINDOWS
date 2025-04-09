# client/collectors/process_collector.py
import psutil
import time
import logging
from config import PROCESS_SCAN_INTERVAL
logger = logging.getLogger("client.process_collector")
class ProcessCollector:
    def __init__(self):
        self.last_scan_time = 0
    def get_process_list(self, detailed=False):
        try:
            current_time = time.time()
            if current_time - self.last_scan_time < PROCESS_SCAN_INTERVAL and detailed:
                logger.debug(f"Aguardando intervalo entre scans ({PROCESS_SCAN_INTERVAL}s)")
                time.sleep(PROCESS_SCAN_INTERVAL - (current_time - self.last_scan_time))
            if detailed:
                self.last_scan_time = time.time()
            process_list = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'status', 'create_time', 'ppid']):
                try:
                    pid = proc.info['pid']
                    process_info = {
                        'pid': pid,
                        'name': proc.info['name'],
                        'status': proc.info['status'],
                        'username': proc.info['username'] or "N/A",
                        'ppid': proc.info.get('ppid', 0)
                    }
                    try:
                        create_time = proc.info['create_time']
                        if create_time:
                            uptime_seconds = int(current_time - create_time)
                            process_info['uptime'] = uptime_seconds
                    except:
                        process_info['uptime'] = -1
                    if detailed:
                        try:
                            process_info['cpu_percent'] = round(proc.cpu_percent(interval=0.1), 1)
                            mem_info = proc.memory_info()
                            process_info['memory_rss'] = mem_info.rss // (1024 * 1024)
                            process_info['memory_percent'] = round(proc.memory_percent(), 1)
                            process_info['threads'] = proc.num_threads()
                            process_info['exe'] = proc.exe() if hasattr(proc, 'exe') else "N/A"
                        except:
                            pass
                    process_list.append(process_info)
                except:
                    pass
            if detailed:
                process_list.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            else:
                process_list.sort(key=lambda x: x.get('name', '').lower())
            logger.info(f"Obtidos {len(process_list)} processos")
            return process_list
        except Exception as e:
            logger.error(f"Erro ao obter lista de processos: {str(e)}")
            return []

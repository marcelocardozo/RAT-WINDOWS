# server/managers/process_manager.py
import json
import logging
from datetime import datetime, timedelta
logger = logging.getLogger("server.process_manager")
class ProcessManager:
    def __init__(self):
        self.client_processes = {}
    def process_list(self, client_key, process_list):
        try:
            self.client_processes[client_key] = {
                'timestamp': datetime.now(),
                'processes': process_list
            }
            process_count = len(process_list) if process_list else 0
            logger.info(f"Recebida lista com {process_count} processos do cliente {client_key}")
            return self._format_process_list(process_list)
        except Exception as e:
            logger.error(f"Erro ao processar lista de processos: {str(e)}")
            return []
    def _format_process_list(self, process_list):
        if not process_list:
            return []
        for proc in process_list:
            if 'uptime' in proc and proc['uptime'] > 0:
                proc['uptime_seconds'] = proc['uptime']
                seconds = proc['uptime']
                delta = timedelta(seconds=seconds)
                if seconds < 60:
                    proc['uptime_formatted'] = f"{seconds} segundos"
                elif seconds < 3600:
                    proc['uptime_formatted'] = f"{delta.seconds // 60} minutos"
                elif seconds < 86400:
                    hours = delta.seconds // 3600
                    minutes = (delta.seconds % 3600) // 60
                    proc['uptime_formatted'] = f"{hours}h {minutes}m"
                else:
                    days = delta.days
                    hours = (delta.seconds // 3600)
                    proc['uptime_formatted'] = f"{days}d {hours}h"
            else:
                proc['uptime_seconds'] = -1
                proc['uptime_formatted'] = "N/A"
        return process_list
    def get_client_processes(self, client_key):
        if client_key not in self.client_processes:
            return None
        return self.client_processes[client_key]['processes']
    def clear_client_data(self, client_key):
        if client_key in self.client_processes:
            del self.client_processes[client_key]
            logger.info(f"Dados de processos do cliente {client_key} removidos")
    def find_process_by_pid(self, client_key, pid):
        if client_key not in self.client_processes:
            return None
        processes = self.client_processes[client_key]['processes']
        for proc in processes:
            if proc.get('pid') == pid:
                return proc
        return None
    def find_processes_by_name(self, client_key, name, case_sensitive=False):
        if client_key not in self.client_processes:
            return []
        processes = self.client_processes[client_key]['processes']
        result = []
        if case_sensitive:
            for proc in processes:
                if name in proc.get('name', ''):
                    result.append(proc)
        else:
            name_lower = name.lower()
            for proc in processes:
                if name_lower in proc.get('name', '').lower():
                    result.append(proc)
        return result
    def get_process_stats(self, client_key):
        if client_key not in self.client_processes:
            return None
        processes = self.client_processes[client_key]['processes']
        if not processes:
            return {
                'count': 0,
                'timestamp': self.client_processes[client_key]['timestamp']
            }
        users = {}
        for proc in processes:
            username = proc.get('username', 'Unknown')
            if username in users:
                users[username] += 1
            else:
                users[username] = 1
        return {
            'count': len(processes),
            'users': users,
            'timestamp': self.client_processes[client_key]['timestamp']
        }

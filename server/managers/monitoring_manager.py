# server/managers/monitoring_manager.py
import logging
import time
from datetime import datetime
logger = logging.getLogger("server.monitoring_manager")
class MonitoringManager:
    def __init__(self, server):
        self.server = server
        self.client_monitoring = {}
        self.monitoring_intervals = {}
        self.monitoring_history = {}
        self.history_limit = 100
    def register_client(self, client_key):
        if client_key not in self.client_monitoring:
            self.client_monitoring[client_key] = {
                'last_update': time.time(),
                'update_count': 0,
                'status': 'connected',
                'cpu_usage': [],
                'ram_usage': []
            }
    def unregister_client(self, client_key):
        if client_key in self.client_monitoring:
            del self.client_monitoring[client_key]
        if client_key in self.monitoring_intervals:
            del self.monitoring_intervals[client_key]
        if client_key in self.monitoring_history:
            del self.monitoring_history[client_key]
    def update_client_data(self, client_key, update_data):
        if client_key not in self.client_monitoring:
            self.register_client(client_key)
        client_data = self.client_monitoring[client_key]
        client_data['last_update'] = time.time()
        client_data['update_count'] += 1
        if 'cpu_usage' in update_data:
            try:
                cpu_value = float(update_data['cpu_usage'].rstrip('%'))
                client_data['cpu_usage'].append(cpu_value)
                if len(client_data['cpu_usage']) > self.history_limit:
                    client_data['cpu_usage'].pop(0)
            except (ValueError, AttributeError):
                pass
        if 'ram_usage' in update_data:
            try:
                ram_value = float(update_data['ram_usage'].rstrip('%'))
                client_data['ram_usage'].append(ram_value)
                if len(client_data['ram_usage']) > self.history_limit:
                    client_data['ram_usage'].pop(0)
            except (ValueError, AttributeError):
                pass
        return True
    def set_monitoring_interval(self, client_key, interval):
        self.monitoring_intervals[client_key] = interval
    def get_monitoring_interval(self, client_key):
        return self.monitoring_intervals.get(client_key, 0)
    def get_client_status(self, client_key):
        if client_key not in self.client_monitoring:
            return 'disconnected'
        last_update = self.client_monitoring[client_key]['last_update']
        time_since_update = time.time() - last_update
        if time_since_update > 10:
            return 'stalled'
        else:
            return 'connected'
    def get_client_cpu_usage(self, client_key):
        if client_key not in self.client_monitoring:
            return []
        return self.client_monitoring[client_key]['cpu_usage']
    def get_client_ram_usage(self, client_key):
        if client_key not in self.client_monitoring:
            return []
        return self.client_monitoring[client_key]['ram_usage']
    def get_client_monitoring_data(self, client_key):
        if client_key not in self.client_monitoring:
            return None
        data = self.client_monitoring[client_key].copy()
        data['current_status'] = self.get_client_status(client_key)
        if data['cpu_usage']:
            data['avg_cpu'] = sum(data['cpu_usage']) / len(data['cpu_usage'])
        else:
            data['avg_cpu'] = 0
        if data['ram_usage']:
            data['avg_ram'] = sum(data['ram_usage']) / len(data['ram_usage'])
        else:
            data['avg_ram'] = 0
        return data
    def record_history_point(self, client_key):
        if client_key not in self.client_monitoring:
            return
        if client_key not in self.monitoring_history:
            self.monitoring_history[client_key] = []
        client_data = self.client_monitoring[client_key]
        last_cpu = client_data['cpu_usage'][-1] if client_data['cpu_usage'] else 0
        last_ram = client_data['ram_usage'][-1] if client_data['ram_usage'] else 0
        history_point = {
            'timestamp': datetime.now().isoformat(),
            'cpu': last_cpu,
            'ram': last_ram
        }
        self.monitoring_history[client_key].append(history_point)
        if len(self.monitoring_history[client_key]) > self.history_limit:
            self.monitoring_history[client_key].pop(0)
    def get_client_history(self, client_key):
        return self.monitoring_history.get(client_key, [])

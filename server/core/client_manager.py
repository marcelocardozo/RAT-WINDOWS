# server/core/client_manager.py
import logging
import time
logger = logging.getLogger("server.client_manager")
class ClientManager:
    def __init__(self, server):
        self.server = server
        self.update_pending = False
        self.last_ui_update = 0
        self.UI_UPDATE_INTERVAL = 0.5
    def update_client_ui(self):
        if hasattr(self, '_scheduled_update') and self._scheduled_update:
            return
        self._scheduled_update = True
        self.server.update_ui_callback()
    def _check_ui_update(self):
        current_time = time.time()
        if self.update_pending and (current_time - self.last_ui_update) >= self.UI_UPDATE_INTERVAL:
            if self.server.update_ui_callback:
                self.server.update_ui_callback()
            self.update_pending = False
            self.last_ui_update = current_time
    def trigger_ui_update(self):
        self.update_pending = True
        self._check_ui_update()
    def register_client_update(self, client_address, update_data):
        if client_address not in self.server.connection_manager.clients:
            return False
        client_info = self.server.connection_manager.clients[client_address]
        changed = False
        if "cpu_usage" in update_data and client_info.get("cpu_usage") != update_data["cpu_usage"]:
            client_info["cpu_usage"] = update_data["cpu_usage"]
            changed = True
        if "ram_usage" in update_data and client_info.get("ram_usage") != update_data["ram_usage"]:
            client_info["ram_usage"] = update_data["ram_usage"]
            changed = True
        if changed:
            self.trigger_ui_update()
        return changed

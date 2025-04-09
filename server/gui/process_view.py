# server/gui/process_view.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import logging
from datetime import datetime
from gui.process_list import ProcessListComponent
logger = logging.getLogger("server.process_view")
class ProcessWindow:
    def __init__(self, parent, client_address, client_key, server, log_callback):
        self.parent = parent
        self.client_address = client_address
        self.client_key = client_key
        self.server = server
        self.log = log_callback
        self.is_closing = False
        self.last_update = 0
        self.update_interval = 3
        self.auto_refresh = tk.BooleanVar(value=True)
        self.show_stopped = tk.BooleanVar(value=False)
        self.update_timer = None
        self.status_var = tk.StringVar(value="Aguardando dados...")
        self.process_count_var = tk.StringVar(value="Processos: 0")
        self.filtered_count_var = tk.StringVar(value="")
        self.total_processes = 0
        self.window = tk.Toplevel(parent)
        self.window.title(f"Processos - {client_key}")
        self.window.geometry("800x600")
        self.window.minsize(700, 400)
        self._create_process_window()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        self._request_processes()
    def _create_process_window(self):
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        self._create_control_panel(main_frame)
        self._create_filter_panel(main_frame)
        process_frame = ttk.Frame(main_frame)
        process_frame.pack(fill=tk.BOTH, expand=True)
        self.process_list = ProcessListComponent(
            process_frame,
            on_double_click=lambda e: self._kill_process(),
            kill_callback=self._kill_process
        )
        self.process_list.process_count_var = self.process_count_var
        self.process_list.filtered_count_var = self.filtered_count_var
        self._create_status_bar()
    def _create_control_panel(self, parent):
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        self.refresh_button = ttk.Button(
            control_frame, 
            text="Atualizar", 
            command=self._request_processes
        )
        self.refresh_button.pack(side=tk.LEFT, padx=(0, 10))
        self.auto_refresh_check = ttk.Checkbutton(
            control_frame,
            text="Auto-atualizar",
            variable=self.auto_refresh,
            command=self._toggle_auto_refresh
        )
        self.auto_refresh_check.pack(side=tk.LEFT, padx=10)
        self.show_stopped_check = ttk.Checkbutton(
            control_frame,
            text="Mostrar Processos Parados",
            variable=self.show_stopped,
            command=self._on_toggle_show_stopped
        )
        self.show_stopped_check.pack(side=tk.LEFT, padx=10)
        self.kill_button = ttk.Button(
            control_frame,
            text="Forçar Parada",
            command=self._kill_process
        )
        self.kill_button.pack(side=tk.LEFT, padx=10)
        self.total_count_label = ttk.Label(
            control_frame,
            text="Total: 0"
        )
        self.total_count_label.pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Label(
            control_frame,
            textvariable=self.process_count_var
        ).pack(side=tk.RIGHT)
    def _create_filter_panel(self, parent):
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(
            filter_frame, 
            text="Filtrar por nome:"
        ).pack(side=tk.LEFT, padx=(0, 5))
        self.filter_entry = ttk.Entry(filter_frame, width=30)
        self.filter_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(
            filter_frame,
            text="Filtrar",
            command=self._apply_filter
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            filter_frame,
            text="Limpar",
            command=self._clear_filter
        ).pack(side=tk.LEFT, padx=5)
        self.filter_entry.bind("<Return>", lambda event: self._apply_filter())
        ttk.Label(
            filter_frame,
            textvariable=self.filtered_count_var
        ).pack(side=tk.RIGHT, padx=5)
    def _create_status_bar(self):
        status_frame = ttk.Frame(self.window, relief=tk.SUNKEN, padding=(5, 2))
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        status_label = ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W)
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    def _request_processes(self):
        if self.is_closing:
            return
        self.refresh_button.config(state=tk.DISABLED)
        try:
            detailed = False
            self.log(f"Solicitando lista de processos de {self.client_key}")
            self.status_var.set("Solicitando lista de processos...")
            success = self.server.request_process_list(self.client_address, detailed)
            if not success:
                self.log(f"Falha ao solicitar lista de processos de {self.client_key}")
                self.status_var.set("Falha ao solicitar lista de processos")
                messagebox.showerror("Erro", "Falha ao solicitar lista de processos", parent=self.window)
            self.window.after(1000, lambda: self.refresh_button.config(state=tk.NORMAL))
        except Exception as e:
            self.log(f"Erro ao solicitar lista de processos: {str(e)}")
            self.status_var.set(f"Erro: {str(e)}")
            self.refresh_button.config(state=tk.NORMAL)
    def _apply_filter(self):
        if hasattr(self, 'process_list'):
            filter_text = self.filter_entry.get()
            self.log(f"Aplicando filtro: '{filter_text}'")
            self.process_list.apply_filter(filter_text)
    def _clear_filter(self):
        if hasattr(self, 'filter_entry') and hasattr(self, 'process_list'):
            self.filter_entry.delete(0, tk.END)
            self.log("Filtro removido")
            self.process_list.clear_filter()
    def _on_toggle_show_stopped(self):
        if hasattr(self, 'all_processes'):
            self.update_process_list(self.all_processes)
            self.log(f"{'Mostrando' if self.show_stopped.get() else 'Ocultando'} processos parados")
    def update_process_list(self, processes):
        if self.is_closing or not hasattr(self, 'process_list'):
            return
        try:
            self.last_update = time.time()
            self.all_processes = processes
            self.total_processes = len(processes)
            if not self.show_stopped.get():
                processes = [proc for proc in processes if 'status' not in proc or proc['status'].lower() != 'stopped']
            self.process_list.set_processes(processes)
            self.total_count_label.config(text=f"Total: {self.total_processes}")
            timestamp = datetime.now().strftime("%H:%M:%S")
            status_text = f"Última atualização: {timestamp}"
            if not self.show_stopped.get() and self.total_processes > len(processes):
                status_text += f" | {self.total_processes - len(processes)} processos parados ocultos"
            self.status_var.set(status_text)
            self._schedule_auto_refresh()
        except Exception as e:
            self.log(f"Erro ao atualizar lista de processos: {str(e)}")
            self.status_var.set(f"Erro ao atualizar: {str(e)}")
    def _kill_process(self):
        if not hasattr(self, 'process_list'):
            return
        selected_process = self.process_list.get_selected_process()
        if not selected_process:
            messagebox.showinfo("Aviso", "Selecione um processo para forçar a parada.", parent=self.window)
            return
        pid = selected_process["pid"]
        proc_name = selected_process["name"]
        if not messagebox.askyesno("Confirmar", f"Deseja realmente forçar a parada do processo '{proc_name}' (PID: {pid})?", parent=self.window):
            return
        try:
            self.log(f"ProcessView: Solicitando parada do processo {pid} ({proc_name})")
            logger.info(f"ProcessView: Solicitando parada do processo {pid} ({proc_name})")
            self.status_var.set(f"Solicitando parada do processo {pid}...")
            self.kill_button.config(state=tk.DISABLED)
            if hasattr(self.process_list, 'remove_process'):
                self.process_list.remove_process(pid)
            success = self.server.request_kill_process(self.client_address, int(pid))
            logger.info(f"ProcessView: Resultado da solicitação de parada: {success}")
            if success:
                self.log(f"Solicitação de parada enviada para o processo {pid}")
                self.status_var.set(f"Solicitação de parada enviada para o processo {pid}")
                messagebox.showinfo("Sucesso", f"Solicitação de parada do processo {pid} enviada com sucesso", parent=self.window)
                self.window.after(2000, self._force_update_processes)
            else:
                self.log(f"Falha ao solicitar parada do processo {pid}")
                self.status_var.set("Falha ao solicitar parada do processo")
                messagebox.showerror("Erro", f"Falha ao solicitar parada do processo {pid}", parent=self.window)
                self.window.after(2000, self._force_update_processes)
            self.kill_button.config(state=tk.NORMAL)
        except Exception as e:
            logger.error(f"Erro ao solicitar parada do processo: {str(e)}", exc_info=True)
            self.log(f"Erro ao solicitar parada do processo: {str(e)}")
            self.status_var.set(f"Erro: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao solicitar parada do processo: {str(e)}", parent=self.window)
            self.window.after(3000, self._force_update_processes)
            self.kill_button.config(state=tk.NORMAL)
    def _force_update_processes(self):
        if self.is_closing:
            return
        self.log(f"Atualizando lista de processos após tentativa de encerramento")
        self._request_processes()
    def _toggle_auto_refresh(self):
        if self.auto_refresh.get():
            self.log(f"Ativando atualização automática para {self.client_key}")
            self._schedule_auto_refresh()
        else:
            self.log(f"Desativando atualização automática para {self.client_key}")
            if self.update_timer:
                self.window.after_cancel(self.update_timer)
                self.update_timer = None
    def _schedule_auto_refresh(self):
        if not hasattr(self, 'window') or not self.window.winfo_exists():
            return
        if self.update_timer:
            self.window.after_cancel(self.update_timer)
            self.update_timer = None
        if not self.auto_refresh.get() or self.is_closing:
            return
        elapsed = time.time() - self.last_update
        interval = 3
        if elapsed < interval:
            remaining = interval - elapsed
            ms_remaining = int(remaining * 1000)
            self.update_timer = self.window.after(ms_remaining, self._request_processes)
        else:
            self.update_timer = self.window.after(100, self._request_processes)
    def _on_close(self):
        self.is_closing = True
        if self.update_timer:
            try:
                self.window.after_cancel(self.update_timer)
            except:
                pass
            self.update_timer = None
        try:
            self.window.destroy()
        except:
            pass
        self.log(f"Janela de processos fechada para {self.client_key}")

# server/gui/shell_view.py
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import logging
import json
import threading
from datetime import datetime
logger = logging.getLogger("server.shell_view")
class ShellWindow:
    def __init__(self, parent, client_address, client_key, server, log_callback):
        self.parent = parent
        self.client_address = client_address
        self.client_key = client_key
        self.server = server
        self.log = log_callback
        self.is_closing = False
        self.command_history = []
        self.history_index = 0
        self.window = tk.Toplevel(parent)
        self.window.title(f"Shell Remota - {client_key}")
        self.window.geometry("800x600")
        self.window.minsize(600, 400)
        self._create_shell_window()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        self._append_to_output("Shell remota conectada a " + client_key)
        self._append_to_output("Digite 'exit' ou 'quit' para fechar a conexão.")
        self._append_to_output("-" * 50)
    def _create_shell_window(self):
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        output_frame = ttk.LabelFrame(main_frame, text="Saída", padding=5)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.output_text = scrolledtext.ScrolledText(
            output_frame, 
            wrap=tk.WORD, 
            background="black", 
            foreground="white",
            font=("Consolas", 10)
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.output_text.config(state=tk.DISABLED)
        input_frame = ttk.LabelFrame(main_frame, text="Comando", padding=5)
        input_frame.pack(fill=tk.X)
        self.command_entry = ttk.Entry(input_frame)
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.send_button = ttk.Button(
            input_frame, 
            text="Enviar", 
            command=self._send_command
        )
        self.send_button.pack(side=tk.RIGHT)
        self.command_entry.bind("<Return>", lambda e: self._send_command())
        self.command_entry.bind("<Up>", self._previous_command)
        self.command_entry.bind("<Down>", self._next_command)
        self.status_var = tk.StringVar(value="Pronto")
        status_bar = ttk.Label(
            self.window, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.command_entry.focus_set()
    def _append_to_output(self, text, command=False):
        self.output_text.config(state=tk.NORMAL)
        if command:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.output_text.insert(tk.END, f"\n[{timestamp}] > {text}\n", "command")
        else:
            self.output_text.insert(tk.END, f"{text}\n", "output")
        self.output_text.tag_config("command", foreground="cyan")
        self.output_text.tag_config("output", foreground="white")
        self.output_text.tag_config("error", foreground="red")
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
    def process_shell_response(self, response_data):
        if self.is_closing:
            return
        try:
            self._last_processed_hash = getattr(self, '_last_processed_hash', None)
            current_hash = hash(response_data)
            if self._last_processed_hash == current_hash:
                return
            self._last_processed_hash = current_hash
            try:
                response_text = response_data.decode('utf-8', errors='replace')
            except Exception as e:
                response_text = f"[Erro ao decodificar resposta: {str(e)}]"
            self._append_to_output(response_text, False)
            self.status_var.set("Pronto")
            self.command_entry.config(state=tk.NORMAL)
            self.send_button.config(state=tk.NORMAL)
            self.command_entry.focus_set()
        except Exception as e:
            logger.error(f"Erro ao processar resposta da shell: {str(e)}")
    def _send_command(self):
        command = self.command_entry.get().strip()
        if not command:
            return
        if not self.command_history or self.command_history[-1] != command:
            self.command_history.append(command)
        self.history_index = len(self.command_history)
        self._append_to_output(command, True)
        if command.lower() in ['exit', 'quit']:
            self._append_to_output("Encerrando shell remota...", False)
            self.window.after(1000, self._on_close)
            return
        self.command_entry.delete(0, tk.END)
        self.command_entry.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)
        self.status_var.set("Executando comando...")
        try:
            success = self._send_shell_command(command)
            if not success:
                self.status_var.set("Falha ao enviar comando")
                self._append_to_output("Falha ao enviar comando ao cliente", False)
                self.output_text.tag_add("error", "end-2l", "end-1c")
                self.command_entry.config(state=tk.NORMAL)
                self.send_button.config(state=tk.NORMAL)
        except Exception as e:
            logger.error(f"Erro ao enviar comando: {str(e)}")
            self.status_var.set(f"Erro: {str(e)}")
            self._append_to_output(f"Erro ao enviar comando: {str(e)}", False)
            self.output_text.tag_add("error", "end-2l", "end-1c")
            self.command_entry.config(state=tk.NORMAL)
            self.send_button.config(state=tk.NORMAL)
    def _send_shell_command(self, command):
        from core.protocol import CMD_SHELL_COMMAND
        if self.client_address not in self.server.connection_manager.client_handlers:
            logger.error(f"Cliente não encontrado: {self.client_address}")
            return False
        client_handler = self.server.connection_manager.client_handlers[self.client_address]
        try:
            command_data = command.encode('utf-8')
            return client_handler._send_binary_command(CMD_SHELL_COMMAND, command_data)
        except Exception as e:
            logger.error(f"Erro ao enviar comando de shell: {str(e)}")
            return False
    def _previous_command(self, event=None):
        if not self.command_history:
            return
        if self.history_index > 0:
            self.history_index -= 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.command_history[self.history_index])
        return "break"  # Impede o comportamento padrão da tecla
    def _next_command(self, event=None):
        if not self.command_history:
            return
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.command_history[self.history_index])
        elif self.history_index == len(self.command_history) - 1:
            self.history_index = len(self.command_history)
            self.command_entry.delete(0, tk.END)
        return "break"  # Impede o comportamento padrão da tecla
    def _on_close(self):
        self.is_closing = True
        try:
            self.window.destroy()
        except:
            pass
        self.log(f"Janela de shell remota fechada para {self.client_key}")

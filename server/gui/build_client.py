# server/gui/build_client.py
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
import subprocess
import os
import sys
import logging
import shutil
import tempfile
import time
from datetime import datetime
import re
logger = logging.getLogger("server.build_client")
class BuildClientWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Construtor de Executável")
        self.window.geometry("700x600")
        self.window.minsize(600, 500)
        self.window.attributes('-topmost', True)
        self.is_building = False
        self.build_process = None
        self.build_thread = None
        self.create_ui()
        self.set_default_values()
        self.center_window()
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    def create_ui(self):
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        settings_frame = ttk.LabelFrame(main_frame, text="Configurações", padding=10)
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        server_frame = ttk.Frame(settings_frame)
        server_frame.pack(fill=tk.X, pady=5)
        ttk.Label(server_frame, text="Servidor:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.host_entry = ttk.Entry(server_frame, width=20)
        self.host_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(server_frame, text="Porta:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.port_entry = ttk.Entry(server_frame, width=8)
        self.port_entry.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        process_frame = ttk.Frame(settings_frame)
        process_frame.pack(fill=tk.X, pady=5)
        ttk.Label(process_frame, text="Nome do Processo:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.process_name_entry = ttk.Entry(process_frame, width=30)
        self.process_name_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        output_frame = ttk.Frame(settings_frame)
        output_frame.pack(fill=tk.X, pady=5)
        ttk.Label(output_frame, text="Diretório de Saída:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.output_dir_entry = ttk.Entry(output_frame, width=40)
        self.output_dir_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        output_frame.columnconfigure(1, weight=1)
        browse_button = ttk.Button(output_frame, text="Procurar...", command=self.browse_output_dir)
        browse_button.grid(row=0, column=2, sticky=tk.E, padx=5, pady=5)
        generate_button_frame = ttk.Frame(main_frame)
        generate_button_frame.pack(fill=tk.X, pady=(0, 10))
        self.build_button = ttk.Button(
            generate_button_frame, 
            text="Gerar Executável",
            command=self.start_build
        )
        self.build_button.pack(side=tk.RIGHT, padx=5)
        self.close_button = ttk.Button(
            generate_button_frame, 
            text="Fechar",
            command=self.on_close
        )
        self.close_button.pack(side=tk.RIGHT, padx=5)
        advanced_frame = ttk.LabelFrame(main_frame, text="Opções Avançadas", padding=10)
        advanced_frame.pack(fill=tk.X, pady=(0, 10))
        self.one_file_var = tk.BooleanVar(value=True)
        one_file_check = ttk.Checkbutton(
            advanced_frame, 
            text="Criar arquivo executável único",
            variable=self.one_file_var
        )
        one_file_check.pack(anchor=tk.W, pady=2)
        self.hide_console_var = tk.BooleanVar(value=True)
        hide_console_check = ttk.Checkbutton(
            advanced_frame, 
            text="Ocultar janela do console durante execução",
            variable=self.hide_console_var
        )
        hide_console_check.pack(anchor=tk.W, pady=2)
        icon_frame = ttk.Frame(advanced_frame)
        icon_frame.pack(fill=tk.X, pady=5)
        self.use_custom_icon_var = tk.BooleanVar(value=False)
        use_custom_icon_check = ttk.Checkbutton(
            icon_frame, 
            text="Usar ícone personalizado:",
            variable=self.use_custom_icon_var,
            command=self.toggle_icon_entry
        )
        use_custom_icon_check.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.icon_path_entry = ttk.Entry(icon_frame, width=30, state="disabled")
        self.icon_path_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        icon_frame.columnconfigure(1, weight=1)
        self.icon_browse_button = ttk.Button(
            icon_frame, 
            text="Procurar...", 
            command=self.browse_icon,
            state="disabled"
        )
        self.icon_browse_button.grid(row=0, column=2, sticky=tk.E, padx=5, pady=5)
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            wrap=tk.WORD, 
            font=("Consolas", 9),
            background="#f0f0f0"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
    def set_default_values(self):
        self.host_entry.insert(0, "127.0.0.1")
        self.port_entry.insert(0, "5000")
        self.process_name_entry.insert(0, "MonitorClient")
        try:
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            if os.path.exists(desktop_path):
                self.output_dir_entry.insert(0, desktop_path)
        except:
            pass
    def toggle_icon_entry(self):
        if self.use_custom_icon_var.get():
            self.icon_path_entry.config(state="normal")
            self.icon_browse_button.config(state="normal")
        else:
            self.icon_path_entry.config(state="disabled")
            self.icon_browse_button.config(state="disabled")
    def browse_output_dir(self):
        self.window.attributes('-topmost', False)
        directory = filedialog.askdirectory(
            title="Selecionar Diretório de Saída",
            initialdir=self.output_dir_entry.get() if self.output_dir_entry.get() else os.path.expanduser("~")
        )
        self.window.attributes('-topmost', True)
        self.window.focus_force()
        if directory:
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, directory)
    def browse_icon(self):
        self.window.attributes('-topmost', False)
        icon_file = filedialog.askopenfilename(
            title="Selecionar Arquivo de Ícone",
            filetypes=[("Arquivos de Ícone", "*.ico"), ("Todos os arquivos", "*.*")]
        )
        self.window.attributes('-topmost', True)
        self.window.focus_force()
        if icon_file:
            self.icon_path_entry.delete(0, tk.END)
            self.icon_path_entry.insert(0, icon_file)
    def center_window(self):
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.parent.winfo_width() - width) // 2 + self.parent.winfo_x()
        y = (self.parent.winfo_height() - height) // 2 + self.parent.winfo_y()
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    def log_message(self, message, error=False):
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        if error:
            self.log_text.insert(tk.END, f"[{timestamp}] ERROR: {message}\n", "error")
            self.log_text.tag_config("error", foreground="red")
        else:
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    def start_build(self):
        if not self.validate_inputs():
            return
        self.is_building = True
        self.build_button.config(state=tk.DISABLED)
        self.close_button.config(state=tk.DISABLED)
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.build_thread = threading.Thread(target=self.build_executable)
        self.build_thread.daemon = True
        self.build_thread.start()
    def validate_inputs(self):
        host = self.host_entry.get().strip()
        if not host:
            self.log_message("O host do servidor não pode estar vazio", error=True)
            return False
        port = self.port_entry.get().strip()
        try:
            port_num = int(port)
            if port_num < 1 or port_num > 65535:
                raise ValueError("A porta deve estar entre 1 e 65535")
        except ValueError:
            self.log_message("Número de porta inválido", error=True)
            return False
        process_name = self.process_name_entry.get().strip()
        if not process_name:
            self.log_message("O nome do processo não pode estar vazio", error=True)
            return False
        output_dir = self.output_dir_entry.get().strip()
        if not output_dir:
            self.log_message("O diretório de saída não pode estar vazio", error=True)
            return False
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                self.log_message(f"Diretório de saída criado: {output_dir}")
            except Exception as e:
                self.log_message(f"Falha ao criar diretório de saída: {str(e)}", error=True)
                return False
        if self.use_custom_icon_var.get():
            icon_path = self.icon_path_entry.get().strip()
            if not icon_path:
                self.log_message("Caminho do ícone não pode estar vazio quando o ícone personalizado está ativado", error=True)
                return False
            if not os.path.exists(icon_path):
                self.log_message(f"Arquivo de ícone não existe: {icon_path}", error=True)
                return False
        return True
    def build_executable(self):
        try:
            host = self.host_entry.get().strip()
            port = self.port_entry.get().strip()
            process_name = self.process_name_entry.get().strip()
            output_dir = self.output_dir_entry.get().strip()
            one_file = self.one_file_var.get()
            hide_console = self.hide_console_var.get()
            use_custom_icon = self.use_custom_icon_var.get()
            icon_path = self.icon_path_entry.get().strip() if use_custom_icon else None
            self.log_message(f"Iniciando processo de geração para {process_name}")
            self.log_message(f"Configuração do servidor: {host}:{port}")
            self.log_message(f"Diretório de saída: {output_dir}")
            self.log_message("Verificando PyInstaller...")
            self.check_pyinstaller()
            self.edit_config_file(host, port)
            pyinstaller_cmd = self.prepare_pyinstaller_command(
                process_name, 
                output_dir, 
                one_file, 
                hide_console, 
                icon_path,                
            )
            self.log_message("Executando PyInstaller com o seguinte comando:")
            self.log_message(" ".join(pyinstaller_cmd))
            self.log_message("Este processo pode levar vários minutos...")
            self.execute_pyinstaller(pyinstaller_cmd)
            self.log_message("Processo de geração concluído!")
            output_path = os.path.join(output_dir, "dist", process_name)
            if one_file:
                output_path = os.path.join(output_path + ".exe")
            if os.path.exists(output_path):
                self.log_message(f"Executável criado com sucesso em:")
                self.log_message(output_path)
            else:
                self.log_message("Não foi possível encontrar o executável. Verifique o log para erros.", error=True)
        except Exception as e:
            self.log_message(f"Falha na geração: {str(e)}", error=True)
        finally:
            self.is_building = False
            self.build_process = None
            self.window.after(0, self.reset_ui_state)
    def check_pyinstaller(self):
        try:
            import PyInstaller
            self.log_message("PyInstaller está instalado")
        except ImportError:
            self.log_message("PyInstaller não encontrado. Tentando instalar...")
            pip_cmd = [sys.executable, "-m", "pip", "install", "pyinstaller"]
            try:
                proc = subprocess.Popen(
                    pip_cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                for line in proc.stdout:
                    self.log_message(line.strip())
                proc.wait()
                if proc.returncode != 0:
                    raise Exception("Falha ao instalar PyInstaller")
                self.log_message("PyInstaller instalado com sucesso")
            except Exception as e:
                raise Exception(f"Falha ao instalar PyInstaller: {str(e)}")
    def edit_config_file(self, host, port):
        try:
            client_dir = self.find_client_directory()
            self.log_message(f"Using client directory: {client_dir}")
            config_path = os.path.join(client_dir, "config.py")
            with open(config_path, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            conteudo_novo = re.sub(r'DEFAULT_SERVER_HOST\s*=\s*".*?"', f'DEFAULT_SERVER_HOST = "{host}"', conteudo)
            conteudo_novo = re.sub(r'DEFAULT_SERVER_PORT\s*=\s*\d+', f'DEFAULT_SERVER_PORT = {port}', conteudo_novo)
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(conteudo_novo)
            self.log_message(f"Configuração atualizada com sucesso: HOST={host}, PORTA={port}")
        except FileNotFoundError as e:
            erro = f"Arquivo config.py não encontrado em: {config_path}"
            self.log_message(erro)
            print(erro)
            raise Exception(erro)
        except Exception as e:
            erro = f"Erro ao editar config.py: {str(e)}"
            self.log_message(erro)
            print(erro)
            raise Exception(erro)
    def prepare_pyinstaller_command(self, process_name, output_dir, one_file, hide_console, icon_path):
        client_dir = self.find_client_directory()
        if not client_dir:
            raise Exception("Could not find the client directory")
        self.log_message(f"Using client directory: {client_dir}")
        cmd = [
            sys.executable,
            "-m",
            "PyInstaller"
        ]
        if one_file:
            cmd.append("--onefile")
        else:
            cmd.append("--onedir")
        if hide_console:
            cmd.append("--noconsole")
        if icon_path:
            cmd.extend(["--icon", icon_path])
        cmd.extend([
            "--name", process_name,
            "--distpath", os.path.join(output_dir, "dist"),
            "--workpath", os.path.join(output_dir, "build"),
            "--specpath", output_dir
        ])
        cmd.extend([
            "--paths", client_dir,
        ])
        main_script = os.path.join(client_dir, "main.py")
        cmd.append(main_script)
        return cmd
    def find_client_directory(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        server_dir = os.path.dirname(current_dir)
        root_dir = os.path.dirname(server_dir)
        client_dir = os.path.join(root_dir, "client")
        if os.path.exists(client_dir) and os.path.isdir(client_dir):
            return client_dir
        self.log_message("Diretório do cliente não encontrado no local esperado, procurando...")
        for parent_dir, dirs, files in os.walk(root_dir):
            if "client" in dirs:
                possible_client = os.path.join(parent_dir, "client")
                if os.path.exists(os.path.join(possible_client, "main.py")):
                    return possible_client
        return None
    def execute_pyinstaller(self, cmd):
        self.build_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        for line in self.build_process.stdout:
            if not self.is_building:
                break
            self.log_message(line.strip())
            self.window.update_idletasks()
        self.build_process.wait()
        if self.build_process.returncode != 0:
            self.log_message(f"PyInstaller falhou com código de saída {self.build_process.returncode}", error=True)
            raise Exception("A geração do executável falhou")
    def cancel_build(self):
        if not self.is_building:
            return
        self.log_message("Cancelando processo de geração...")
        self.is_building = False
        if self.build_process:
            try:
                self.build_process.terminate()
            except:
                pass
        self.reset_ui_state()
    def reset_ui_state(self):
        self.build_button.config(state=tk.NORMAL)
        self.close_button.config(state=tk.NORMAL)
    def on_close(self):
        if self.is_building:
            if not tk.messagebox.askyesno(
                "Cancelar Geração", 
                "Um processo de geração está em andamento. Deseja cancelá-lo e fechar a janela?",
                parent=self.window
            ):
                return
            self.cancel_build()
        self.window.destroy()

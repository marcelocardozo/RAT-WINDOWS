# server/gui/log_view.py
import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
class LogPanel:
    def __init__(self, parent):
        self.frame = ttk.LabelFrame(parent, text="Log do Servidor", padding=10)
        self.frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.log_area = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD, height=10)
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.configure(state=tk.DISABLED, font=('Consolas', 9))
        self._create_controls()
    def _create_controls(self):
        buttons_frame = ttk.Frame(self.frame)
        buttons_frame.pack(fill=tk.X, pady=(5, 0))
        self.auto_scroll = tk.BooleanVar(value=True)
        auto_scroll_check = ttk.Checkbutton(
            buttons_frame, 
            text="Auto-scroll", 
            variable=self.auto_scroll
        )
        auto_scroll_check.pack(side=tk.LEFT)
        clear_button = ttk.Button(
            buttons_frame, 
            text="Limpar Log", 
            command=self.clear_log
        )
        clear_button.pack(side=tk.RIGHT)
    def add_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        if isinstance(self.frame, tk.Widget):
            self.frame.after(0, lambda: self._update_log(log_entry))
    def _update_log(self, log_entry):
        self.log_area.configure(state=tk.NORMAL)
        self.log_area.insert(tk.END, log_entry)
        if self.auto_scroll.get():
            self.log_area.see(tk.END)
        self.log_area.configure(state=tk.DISABLED)
    def clear_log(self):
        self.log_area.configure(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.configure(state=tk.DISABLED)

# server/utils/ui_utils.py
import tkinter as tk
from tkinter import ttk
import logging
logger = logging.getLogger("server.ui_utils")
def center_window(window, width=None, height=None):
    if width and height:
        window.geometry(f"{width}x{height}")
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    size = tuple(int(_) for _ in window.geometry().split('+')[0].split('x'))
    x = screen_width/2 - size[0]/2
    y = screen_height/2 - size[1]/2
    window.geometry("+%d+%d" % (x, y))
    return window
def create_scrollable_frame(parent):
    container = ttk.Frame(parent)
    canvas = tk.Canvas(container)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    container.pack(fill="both", expand=True)
    return scrollable_frame
def create_labeled_entry(parent, label_text, default_value="", width=None):
    frame = ttk.Frame(parent)
    label = ttk.Label(frame, text=label_text)
    label.pack(side=tk.LEFT, padx=(0, 5))
    entry = ttk.Entry(frame, width=width)
    if default_value:
        entry.insert(0, default_value)
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    return frame, entry
def create_button_pair(parent, confirm_text, cancel_text, confirm_command, cancel_command):
    frame = ttk.Frame(parent)
    cancel_button = ttk.Button(frame, text=cancel_text, command=cancel_command)
    cancel_button.pack(side=tk.RIGHT, padx=5)
    confirm_button = ttk.Button(frame, text=confirm_text, command=confirm_command)
    confirm_button.pack(side=tk.RIGHT)
    return frame, confirm_button, cancel_button
def show_message(parent, title, message, message_type="info"):
    toplevel = tk.Toplevel(parent)
    toplevel.title(title)
    toplevel.transient(parent)
    toplevel.grab_set()
    frame = ttk.Frame(toplevel, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)
    if message_type == "error":
        icon_label = ttk.Label(frame, text="❌", font=("", 24))
    elif message_type == "warning":
        icon_label = ttk.Label(frame, text="⚠️", font=("", 24))
    else:
        icon_label = ttk.Label(frame, text="ℹ️", font=("", 24))
    icon_label.pack(pady=(0, 10))
    message_label = ttk.Label(frame, text=message, wraplength=300)
    message_label.pack(pady=10)
    button = ttk.Button(frame, text="OK", command=toplevel.destroy)
    button.pack(pady=10)
    center_window(toplevel, 350, 200)
    toplevel.focus_set()
    button.focus_set()

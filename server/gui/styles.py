# server/gui/styles.py
from tkinter import ttk
def setup_styles():
    style = ttk.Style()
    try:
        style.theme_use('clam')
    except:
        pass
    style.configure('TFrame', background='#f5f5f5')
    style.configure('Config.TFrame', background='#f0f0f0', relief='groove', borderwidth=1)
    style.configure('TLabel', background='#f5f5f5', font=('Segoe UI', 10))
    style.configure('TButton', font=('Segoe UI', 10))
    style.configure('Header.TLabel', font=('Segoe UI', 11, 'bold'))
    style.configure('Title.TLabel', font=('Segoe UI', 12, 'bold'))
    style.configure('Status.TLabel', background='#e0e0e0', padding=2)
    style.configure('Status.TFrame', background='#e0e0e0')
    style.configure('Log.Text', background='#ffffff', font=('Consolas', 9))
    style.configure('Treeview', 
                    background='#ffffff',
                    fieldbackground='#ffffff',
                    rowheight=25)
    style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'))
    style.configure('Danger.TButton', foreground='#cc0000')
    style.configure('Success.TButton', foreground='#007700')
    style.configure('Warning.TLabel', foreground='#cc7700')
    style.configure('Error.TLabel', foreground='#cc0000')

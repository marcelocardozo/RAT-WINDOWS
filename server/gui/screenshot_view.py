# server/gui/screenshot_view.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import base64
from PIL import Image, ImageTk
import io
from utils.image_utils import decode_base64_image, resize_image
class ScreenshotWindow:
    def __init__(self, parent, client_address, client_key, screenshot_data, server, 
                 log_callback, monitoring_dict, closing_windows):
        self.parent = parent
        self.client_address = client_address
        self.client_key = client_key
        self.server = server
        self.log = log_callback
        self.monitoring_dict = monitoring_dict
        self.closing_windows = closing_windows
        self.is_closing = False
        self.window = tk.Toplevel(parent)
        self.window.title(f"Captura de tela - {client_key}")
        self._create_screenshot_window(screenshot_data)
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
    def _create_screenshot_window(self, screenshot_data):
        image_data = base64.b64decode(screenshot_data)
        image = Image.open(io.BytesIO(image_data))
        screen_width = self.parent.winfo_screenwidth() - 100
        screen_height = self.parent.winfo_screenheight() - 100
        window_width = min(image.width, screen_width)
        window_height = min(image.height + 50, screen_height)
        self.window.geometry(f"{window_width}x{window_height}")
        frame = tk.Frame(self.window)
        frame.pack(fill=tk.BOTH, expand=True)
        h_scrollbar = tk.Scrollbar(frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        v_scrollbar = tk.Scrollbar(frame)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas = tk.Canvas(frame, 
                             xscrollcommand=h_scrollbar.set,
                             yscrollcommand=v_scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        h_scrollbar.config(command=self.canvas.xview)
        v_scrollbar.config(command=self.canvas.yview)
        self.photo = ImageTk.PhotoImage(image)
        self.image_item = self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        self.canvas.image = self.photo
        self._create_control_panel()
    def _create_control_panel(self):
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=5)
        self.refresh_button = ttk.Button(button_frame, text="Atualizar", 
                                      command=self._request_screenshot)
        self.refresh_button.pack(side=tk.LEFT, padx=5)
        self.save_button = ttk.Button(button_frame, text="Salvar", 
                                    command=self._save_screenshot)
        self.save_button.pack(side=tk.LEFT, padx=5)
        self.close_button = ttk.Button(button_frame, text="Fechar", 
                                     command=self._on_close)
        self.close_button.pack(side=tk.LEFT, padx=5)
    def _request_screenshot(self):
        if self.client_address not in self.server.connection_manager.client_sockets:
            messagebox.showerror("Erro", "Cliente não está mais conectado.", parent=self.window)
            return
        self.refresh_button.config(state=tk.DISABLED)
        try:
            self.log(f"Solicitando nova captura de {self.client_key}")
            self.server.send_command(self.client_address, {"action": "screenshot"})
            self.window.after(1000, lambda: self.refresh_button.config(state=tk.NORMAL))
        except Exception as e:
            self.log(f"Erro ao solicitar captura: {str(e)}")
            messagebox.showerror("Erro", f"Falha ao solicitar captura: {str(e)}", parent=self.window)
            self.refresh_button.config(state=tk.NORMAL)
    def _save_screenshot(self):
        self.save_button.config(state=tk.DISABLED)
        try:
            filename = filedialog.asksaveasfilename(
                parent=self.window,  # Importante: usar a janela correta como pai
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
            )
            if filename:
                try:
                    if hasattr(self.canvas, 'image') and self.canvas.image:
                        image = ImageTk.getimage(self.canvas.image)
                        image.save(filename)
                        messagebox.showinfo("Sucesso", f"Imagem salva em {filename}", parent=self.window)
                except Exception as e:
                    messagebox.showerror("Erro", f"Falha ao salvar imagem: {str(e)}", parent=self.window)
        finally:
            self.save_button.config(state=tk.NORMAL)
    def _on_close(self):
        self.close_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        self.refresh_button.config(state=tk.DISABLED)
        self.closing_windows.add(self.client_key)
        self.log(f"Fechando janela para {self.client_key}")
        self.is_closing = True
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.image = None
        try:
            self.window.destroy()
        except Exception as e:
            self.log(f"Erro ao destruir janela: {str(e)}")
        def final_cleanup():
            try:
                if self.client_key in self.monitoring_dict:
                    del self.monitoring_dict[self.client_key]
                    self.log(f"Recursos de visualização limpos para {self.client_key}")
                self.closing_windows.discard(self.client_key)
            except Exception as e:
                self.log(f"Erro na limpeza final: {str(e)}")
                self.closing_windows.discard(self.client_key)
        self.parent.after(100, final_cleanup)
    def update_image(self, screenshot_data):
        if self.is_closing:
            return
        try:
            image_data = base64.b64decode(screenshot_data)
            image = Image.open(io.BytesIO(image_data))
            photo = ImageTk.PhotoImage(image)
            self.canvas.itemconfig(self.image_item, image=photo)
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
            if hasattr(self.canvas, 'old_image'):
                self.canvas.old_image = None
            self.canvas.old_image = self.canvas.image
            self.canvas.image = photo
        except Exception as e:
            self.log(f"Erro ao atualizar imagem: {str(e)}")
    def get_monitoring_info(self):
        return {
            "window": self.window,
            "canvas": self.canvas,
            "image_item": self.image_item,
            "client_address": self.client_address,
            "is_closing": False,
            "refresh_button": self.refresh_button,
            "update_image": self.update_image
        }

# server/gui/webcam_view.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import base64
from PIL import Image, ImageTk
import io
import json
import time
import os
from datetime import datetime
from utils.image_utils import decode_base64_image, resize_image
from core.protocol import *
import logging
from collections import deque
logger = logging.getLogger("server.webcam_view")
class WebcamWindow:
    def __init__(self, parent, client_address, client_key, server, 
                 log_callback, monitoring_dict, closing_windows):
        self.parent = parent
        self.client_address = client_address
        self.client_key = client_key
        self.server = server
        self.log = log_callback
        self.monitoring_dict = monitoring_dict
        self.closing_windows = closing_windows
        self.is_closing = False
        self.available_cameras = []
        self.selected_camera_id = 0
        self.streaming = False
        self.last_frame_time = 0
        self.frames_received = 0
        self.fps = 0
        self.last_fps_update = time.time()
        self.frame_buffer = deque(maxlen=5)  # Buffer para até 5 frames
        self.next_render_time = 0
        self.render_interval = 1/30  # Renderizar a ~30fps para economizar CPU
        self.window = tk.Toplevel(parent)
        self.window.title(f"Webcam - {client_key}")
        self._create_webcam_window()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        self._start_render_timer()
        self._request_camera_list()
    def _create_webcam_window(self):
        main_frame = tk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True)
        control_frame = ttk.Frame(main_frame, padding=5)
        control_frame.pack(fill=tk.X)
        ttk.Label(control_frame, text="Câmera:").pack(side=tk.LEFT, padx=(0, 5))
        self.camera_var = tk.StringVar()
        self.camera_combo = ttk.Combobox(control_frame, textvariable=self.camera_var, state="readonly", width=30)
        self.camera_combo.pack(side=tk.LEFT, padx=5)
        self.camera_combo.bind("<<ComboboxSelected>>", self._on_camera_selected)
        self.capture_button = ttk.Button(control_frame, text="Capturar", command=self._capture_single_frame)
        self.capture_button.pack(side=tk.LEFT, padx=5)
        self.stream_button = ttk.Button(control_frame, text="Iniciar Stream", command=self._toggle_streaming)
        self.stream_button.pack(side=tk.LEFT, padx=5)
        self.save_button = ttk.Button(control_frame, text="Salvar Imagem", command=self._save_image)
        self.save_button.pack(side=tk.LEFT, padx=5)
        self.refresh_button = ttk.Button(control_frame, text="Atualizar Lista", command=self._request_camera_list)
        self.refresh_button.pack(side=tk.LEFT, padx=5)
        quality_frame = ttk.Frame(main_frame, padding=5)
        quality_frame.pack(fill=tk.X)
        ttk.Label(quality_frame, text="Qualidade:").pack(side=tk.LEFT, padx=(0, 5))
        self.quality_var = tk.IntVar(value=50)
        self.quality_scale = ttk.Scale(quality_frame, from_=10, to=90, 
                                      orient=tk.HORIZONTAL, variable=self.quality_var,
                                      length=150)
        self.quality_scale.pack(side=tk.LEFT, padx=5)
        self.quality_label = ttk.Label(quality_frame, text="50%", width=4)
        self.quality_label.pack(side=tk.LEFT)
        self.quality_var.trace_add("write", lambda *args: self.quality_label.config(
            text=f"{self.quality_var.get()}%"))
        self.apply_quality_btn = ttk.Button(quality_frame, text="Aplicar", 
                                           command=self._apply_quality_settings)
        self.apply_quality_btn.pack(side=tk.LEFT, padx=5)
        self.image_frame = ttk.Frame(main_frame, padding=5)
        self.image_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(self.image_frame, bg='black')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        status_frame = ttk.Frame(self.window, relief=tk.SUNKEN)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_label = ttk.Label(status_frame, text="Pronto", anchor=tk.W, padding=(5, 2))
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.fps_label = ttk.Label(status_frame, text="0 FPS", anchor=tk.E, padding=(5, 2))
        self.fps_label.pack(side=tk.RIGHT)
        self.photo = None
        self.canvas.image = None
        self.window.geometry("800x600")
        self.window.minsize(640, 480)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
    def _on_canvas_configure(self, event):
        if hasattr(self, 'photo') and self.photo:
            self.center_image_in_canvas()
    def _start_render_timer(self):
        if not self.is_closing:
            self._render_from_buffer()
            self.window.after(10, self._start_render_timer)  # Verificar a cada 10ms
    def _render_from_buffer(self):
        current_time = time.time()
        if current_time >= self.next_render_time and self.frame_buffer:
            image_data = self.frame_buffer.pop()
            self._update_canvas_image(image_data)
            self.next_render_time = current_time + self.render_interval
    def _update_canvas_image(self, image_data):
        try:
            image = Image.open(io.BytesIO(image_data))
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            if canvas_width > 1 and canvas_height > 1:
                image = resize_image(image, max(canvas_width, canvas_height))
            self.photo = ImageTk.PhotoImage(image)
            if not hasattr(self, 'image_on_canvas') or not self.image_on_canvas:
                self.image_on_canvas = self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
            else:
                self.canvas.itemconfig(self.image_on_canvas, image=self.photo)
            self.center_image_in_canvas()
            self.canvas.image = self.photo
        except Exception as e:
            logger.error(f"Erro ao atualizar imagem no canvas: {str(e)}")
    def _request_camera_list(self):
        if self.is_closing:
            return
        self._set_loading("Solicitando lista de câmeras...")
        self._set_controls_state(tk.DISABLED)
        try:
            if self.client_address not in self.server.connection_manager.client_handlers:
                self._set_error("Cliente não está conectado")
                self._set_controls_state(tk.NORMAL)
                return
            client_handler = self.server.connection_manager.client_handlers[self.client_address]
            success = client_handler._send_binary_command(CMD_WEBCAM_LIST)
            if not success:
                self._set_error("Falha ao solicitar lista de câmeras")
                self._set_controls_state(tk.NORMAL)
                return
            self.log(f"Solicitação de lista de câmeras enviada para {self.client_key}")
        except Exception as e:
            self._set_error(f"Erro ao solicitar lista de câmeras: {str(e)}")
            self._set_controls_state(tk.NORMAL)
    def _capture_single_frame(self):
        if self.is_closing or self.streaming:
            return  # Ignorar se já estiver em streaming
        self._set_loading("Capturando imagem...")
        self._set_controls_state(tk.DISABLED)
        try:
            if self.client_address not in self.server.connection_manager.client_handlers:
                self._set_error("Cliente não está conectado")
                self._set_controls_state(tk.NORMAL)
                return
            client_handler = self.server.connection_manager.client_handlers[self.client_address]
            params = {
                "camera_id": self.selected_camera_id,
                "quality": self.quality_var.get()
            }
            params_json = json.dumps(params).encode('utf-8')
            success = client_handler._send_binary_command(CMD_WEBCAM_CAPTURE, params_json)
            if not success:
                self._set_error("Falha ao solicitar captura de webcam")
                self._set_controls_state(tk.NORMAL)
                return
            self.log(f"Solicitação de captura da webcam {self.selected_camera_id} enviada para {self.client_key}")
        except Exception as e:
            self._set_error(f"Erro ao solicitar captura de webcam: {str(e)}")
            self._set_controls_state(tk.NORMAL)
    def _toggle_streaming(self):
        if self.is_closing:
            return
        if self.streaming:
            self._stop_streaming()
        else:
            self._start_streaming()
    def _apply_quality_settings(self):
        if self.streaming:
            current_camera = self.selected_camera_id
            self._stop_streaming()
            self.selected_camera_id = current_camera  # Garantir que a câmera não mude
            self.window.after(500, self._start_streaming)
        else:
            self._set_status(f"Qualidade definida para {self.quality_var.get()}%")
    def _start_streaming(self):
        self._set_loading("Iniciando stream...")
        self._set_controls_state(tk.DISABLED)
        try:
            if self.client_address not in self.server.connection_manager.client_handlers:
                self._set_error("Cliente não está conectado")
                self._set_controls_state(tk.NORMAL)
                return
            client_handler = self.server.connection_manager.client_handlers[self.client_address]
            params = {
                "camera_id": self.selected_camera_id,
                "interval": 0.033,  # Intervalo entre frames
                "quality": self.quality_var.get()  # Aplicar a qualidade definida
            }
            params_json = json.dumps(params).encode('utf-8')
            success = client_handler._send_binary_command(CMD_WEBCAM_STREAM_START, params_json)
            if not success:
                self._set_error("Falha ao iniciar stream de webcam")
                self._set_controls_state(tk.NORMAL)
                return
            self.frame_buffer.clear()
            self.streaming = True
            self.stream_button.config(text="Parar Stream")
            self.capture_button.config(state=tk.DISABLED)
            self.frames_received = 0
            self.last_frame_time = 0
            self.last_fps_update = time.time()
            self.fps = 0
            self.log(f"Iniciado streaming da webcam {self.selected_camera_id} para {self.client_key}")
            self._set_status(f"Streaming da câmera {self.selected_camera_id}")
            self._set_controls_state(tk.NORMAL)
        except Exception as e:
            self._set_error(f"Erro ao iniciar streaming: {str(e)}")
            self._set_controls_state(tk.NORMAL)
    def _stop_streaming(self):
        self._set_loading("Parando stream...")
        self._set_controls_state(tk.DISABLED)
        try:
            if self.client_address not in self.server.connection_manager.client_handlers:
                self._set_error("Cliente não está conectado")
                self.streaming = False
                self.stream_button.config(text="Iniciar Stream")
                self.capture_button.config(state=tk.NORMAL)
                self._set_controls_state(tk.NORMAL)
                return
            client_handler = self.server.connection_manager.client_handlers[self.client_address]
            success = client_handler._send_binary_command(CMD_WEBCAM_STREAM_STOP)
            if not success:
                self._set_error("Falha ao parar stream de webcam")
            else:
                self.log(f"Parado streaming da webcam para {self.client_key}")
                self._set_status("Stream parado")
            self.frame_buffer.clear()
            self.streaming = False
            self.stream_button.config(text="Iniciar Stream")
            self.capture_button.config(state=tk.NORMAL)
            self._set_controls_state(tk.NORMAL)
        except Exception as e:
            self._set_error(f"Erro ao parar streaming: {str(e)}")
            self.streaming = False
            self.stream_button.config(text="Iniciar Stream")
            self.capture_button.config(state=tk.NORMAL)
            self._set_controls_state(tk.NORMAL)
    def _save_image(self):
        if not hasattr(self, 'canvas') or not self.canvas.image:
            messagebox.showinfo("Aviso", "Nenhuma imagem disponível para salvar", parent=self.window)
            return
        try:
            was_streaming = self.streaming
            if was_streaming:
                self.streaming = False
                self._set_status("Streaming pausado para salvar imagem...")
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"webcam_{self.client_key.replace(':', '_')}_{now}.png"
            filename = filedialog.asksaveasfilename(
                parent=self.window,
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")],
                initialfile=default_name
            )
            if filename:
                if hasattr(self.canvas, 'image') and self.canvas.image:
                    image = ImageTk.getimage(self.canvas.image)
                    image.save(filename)
                    self._set_status(f"Imagem salva como {os.path.basename(filename)}")
                    messagebox.showinfo("Sucesso", f"Imagem salva em {filename}", parent=self.window)
            if was_streaming:
                self.streaming = True
                self._set_status(f"Streaming da câmera {self.selected_camera_id}")
        except Exception as e:
            self._set_error(f"Erro ao salvar imagem: {str(e)}")
            messagebox.showerror("Erro", f"Falha ao salvar imagem: {str(e)}", parent=self.window)
    def _on_camera_selected(self, event):
        try:
            selected_item = self.camera_combo.get()
            for camera in self.available_cameras:
                if f"{camera['name']} ({camera['resolution']})" == selected_item:
                    old_camera_id = self.selected_camera_id
                    self.selected_camera_id = camera['id']
                    self._set_status(f"Câmera {camera['name']} selecionada")
                    self.log(f"Selecionada câmera ID {self.selected_camera_id} para {self.client_key}")
                    if self.streaming and old_camera_id != self.selected_camera_id:
                        self._set_status(f"Reiniciando stream com a câmera {camera['name']}...")
                        self._stop_streaming()
                        self.window.after(500, self._start_streaming)
                    return
        except Exception as e:
            self._set_error(f"Erro ao selecionar câmera: {str(e)}")
    def process_camera_list(self, data):
        if self.is_closing:
            return
        self._set_controls_state(tk.NORMAL)
        try:
            cameras = json.loads(data.decode('utf-8'))
            if isinstance(cameras, dict) and 'error' in cameras:
                self._set_error(f"Erro ao listar câmeras: {cameras['error']}")
                return
            if not cameras:
                self._set_error("Nenhuma câmera encontrada no cliente")
                return
            self.available_cameras = cameras
            camera_options = []
            for camera in cameras:
                camera_options.append(f"{camera['name']} ({camera['resolution']})")
            self.camera_combo['values'] = camera_options
            if camera_options:
                current_camera_id = self.selected_camera_id
                current_index = 0
                for i, camera in enumerate(cameras):
                    if camera['id'] == current_camera_id:
                        current_index = i
                        break
                self.camera_combo.current(current_index)
                self.selected_camera_id = cameras[current_index]['id']
            self._set_status(f"Encontradas {len(cameras)} câmeras")
            self.log(f"Recebidas {len(cameras)} câmeras do cliente {self.client_key}")
        except Exception as e:
            self._set_error(f"Erro ao processar lista de câmeras: {str(e)}")
    def process_webcam_frame(self, header, frame_data):
        if self.is_closing:
            return
        try:
            camera_id = header.get("camera_id", 0)
            if camera_id != self.selected_camera_id and self.streaming:
                return
            if self.streaming:
                self.frame_buffer.append(frame_data)
                self.frames_received += 1
                current_time = time.time()
                time_diff = current_time - self.last_fps_update
                if time_diff >= 1.0:  # Atualizar FPS a cada segundo
                    frames_in_period = self.frames_received - self.last_frame_time
                    self.fps = frames_in_period / time_diff
                    self.fps_label.config(text=f"{self.fps:.1f} FPS")
                    self.last_frame_time = self.frames_received
                    self.last_fps_update = current_time
                    try:
                        temp_image = Image.open(io.BytesIO(frame_data))
                        self._set_status(f"Streaming da câmera {camera_id} ({temp_image.width}x{temp_image.height})")
                    except:
                        self._set_status(f"Streaming da câmera {camera_id}")
            else:
                image = Image.open(io.BytesIO(frame_data))
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                if canvas_width > 1 and canvas_height > 1:
                    image = resize_image(image, max(canvas_width, canvas_height))
                self.photo = ImageTk.PhotoImage(image)
                if not hasattr(self, 'image_on_canvas') or not self.image_on_canvas:
                    self.image_on_canvas = self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
                else:
                    self.canvas.itemconfig(self.image_on_canvas, image=self.photo)
                self.center_image_in_canvas()
                self.canvas.image = self.photo
                self._set_status(f"Capturado frame da câmera {camera_id} ({image.width}x{image.height})")
            self._set_controls_state(tk.NORMAL)
        except Exception as e:
            self._set_error(f"Erro ao processar frame de webcam: {str(e)}")
            self.log(f"Erro ao processar frame de webcam: {str(e)}")
    def center_image_in_canvas(self):
        if not hasattr(self, 'photo') or not self.photo:
            return
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        img_width = self.photo.width()
        img_height = self.photo.height()
        x = max(0, (canvas_width - img_width) // 2)
        y = max(0, (canvas_height - img_height) // 2)
        if hasattr(self, 'image_on_canvas') and self.image_on_canvas:
            self.canvas.coords(self.image_on_canvas, x, y)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
    def _set_status(self, message):
        self.status_label.config(text=message)
    def _set_loading(self, message):
        self.status_label.config(text=message)
    def _set_error(self, message):
        self.status_label.config(text=f"Erro: {message}")
        self.log(f"Erro na janela de webcam: {message}")
    def _set_controls_state(self, state):
        self.camera_combo.config(state="readonly" if state == tk.NORMAL else tk.DISABLED)
        self.capture_button.config(state=state)
        self.refresh_button.config(state=state)
        self.save_button.config(state=state)
        if not self.streaming or state == tk.NORMAL:
            self.stream_button.config(state=state)
    def _on_close(self):
        if self.streaming:
            self._stop_streaming()
        self.frame_buffer.clear()
        self.photo = None
        if hasattr(self, 'canvas'):
            self.canvas.image = None
        self.is_closing = True
        self.closing_windows.add(self.client_key)
        try:
            self.window.destroy()
        except:
            pass
        self.log(f"Janela de webcam fechada para {self.client_key}")
        def final_cleanup():
            try:
                if self.client_key in self.monitoring_dict:
                    del self.monitoring_dict[self.client_key]
                self.closing_windows.discard(self.client_key)
            except:
                pass
        self.parent.after(100, final_cleanup)
    def get_monitoring_info(self):
        return {
            "window": self.window,
            "client_address": self.client_address,
            "is_closing": self.is_closing,
            "process_camera_list": self.process_camera_list,
            "process_webcam_frame": self.process_webcam_frame
        }

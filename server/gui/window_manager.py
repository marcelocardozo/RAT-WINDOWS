# server/gui/window_manager.py
import logging
import tkinter as tk
from tkinter import messagebox
from gui.screenshot_view import ScreenshotWindow
from gui.process_view import ProcessWindow
from gui.shell_view import ShellWindow
from gui.file_manager_view import FileManagerWindow
from gui.webcam_view import WebcamWindow
from gui.screen_stream_view import ScreenStreamWindow
import core.protocol
import json
logger = logging.getLogger("server.window_manager")
class WindowManager:
    def __init__(self, server, main_window):
        self.server = server
        self.server.set_window_manager(self)
        self.main_window = main_window
        self.screenshot_windows = {}
        self.process_windows = {}
        self.shell_windows = {}
        self.file_manager_windows = {}
        self.webcam_windows = {}
        self.screen_stream_windows = {}  # Novo dicionário para janelas de stream de tela
        self.closing_windows = set()
    def display_screenshot(self, client_address, screenshot_data):
        client_key = f"{client_address[0]}:{client_address[1]}"
        if client_key in self.closing_windows:
            logger.info(f"Ignorando screenshot para cliente em fechamento: {client_key}")
            return
        window_exists = False
        if client_key in self.screenshot_windows:
            window_info = self.screenshot_windows[client_key]
            if "window" in window_info and hasattr(window_info["window"], "winfo_exists"):
                try:
                    if window_info["window"].winfo_exists():
                        window_exists = True
                except:
                    pass
        if window_exists:
            self._update_screenshot_window(client_key, screenshot_data)
        else:
            self._create_new_screenshot_window(client_address, client_key, screenshot_data)
    def display_process_list(self, client_address, process_list):
        client_key = f"{client_address[0]}:{client_address[1]}"
        if client_key in self.closing_windows:
            logger.info(f"Ignorando lista de processos para cliente em fechamento: {client_key}")
            return
        window_exists = False
        if client_key in self.process_windows:
            window_info = self.process_windows[client_key]
            if "window" in window_info and hasattr(window_info["window"], "winfo_exists"):
                try:
                    if window_info["window"].winfo_exists():
                        window_exists = True
                except:
                    pass
        if window_exists:
            logger.info(f"Atualizando janela de processos existente para {client_key}")
            try:
                if "update_process_list" in self.process_windows[client_key]:
                    self.process_windows[client_key]["update_process_list"](process_list)
            except Exception as e:
                logger.error(f"Erro ao atualizar janela de processos: {str(e)}")
        else:
            logger.info(f"Criando nova janela de processos para {client_key}")
            self._create_process_window(client_address, client_key, process_list)
    def process_shell_response(self, client_address, response_data):
        client_key = f"{client_address[0]}:{client_address[1]}"
        if client_key in self.closing_windows:
            return
        try:
            if client_key in self.shell_windows:
                window_info = self.shell_windows[client_key]
                if "window" in window_info and hasattr(window_info["window"], "winfo_exists"):
                    try:
                        if window_info["window"].winfo_exists():
                            if "process_response" in window_info and callable(window_info["process_response"]):
                                window_info["process_response"](response_data)
                                return
                    except Exception as e:
                        self.server.log(f"Erro ao processar resposta de shell para janela existente: {str(e)}")
            self.server.log(f"Recebida resposta de shell para cliente {client_key}, mas nenhuma janela correspondente foi encontrada")
        except Exception as e:
            self.server.log(f"Erro ao processar resposta de shell: {str(e)}")
    def process_file_response(self, client_address, cmd, data):
        client_key = f"{client_address[0]}:{client_address[1]}"
        if client_key in self.closing_windows:
            return
        file_manager_exists = False
        file_manager_window = None
        if hasattr(self, 'file_manager_windows') and client_key in self.file_manager_windows:
            window_info = self.file_manager_windows[client_key]
            if "window" in window_info and hasattr(window_info["window"], "winfo_exists"):
                try:
                    if window_info["window"].winfo_exists():
                        file_manager_exists = True
                        file_manager_window = window_info
                except:
                    pass
        if not file_manager_exists:
            self.server.log(f"Recebida resposta de operação de arquivo para cliente {client_key}, mas nenhuma janela correspondente foi encontrada")
            return
        if cmd == core.protocol.CMD_FILE_LIST_RESPONSE:
            if "process_file_list_response" in file_manager_window and callable(file_manager_window["process_file_list_response"]):
                file_manager_window["process_file_list_response"](data)
        elif cmd == core.protocol.CMD_FILE_DOWNLOAD_RESPONSE:
            if "process_download_response" in file_manager_window and callable(file_manager_window["process_download_response"]):
                file_manager_window["process_download_response"](data)
        elif cmd == core.protocol.CMD_FILE_UPLOAD_RESPONSE:
            if "process_upload_response" in file_manager_window and callable(file_manager_window["process_upload_response"]):
                file_manager_window["process_upload_response"](data)
        elif cmd == core.protocol.CMD_FILE_DELETE_RESPONSE:
            if "process_delete_response" in file_manager_window and callable(file_manager_window["process_delete_response"]):
                file_manager_window["process_delete_response"](data)
        elif cmd == core.protocol.CMD_FILE_RENAME_RESPONSE:
            if "process_rename_response" in file_manager_window and callable(file_manager_window["process_rename_response"]):
                file_manager_window["process_rename_response"](data)
        elif cmd == core.protocol.CMD_FILE_MKDIR_RESPONSE:
            if "process_mkdir_response" in file_manager_window and callable(file_manager_window["process_mkdir_response"]):
                file_manager_window["process_mkdir_response"](data)
    def process_webcam_response(self, client_address, cmd, data):
        client_key = f"{client_address[0]}:{client_address[1]}"
        if client_key in self.closing_windows:
            return
        webcam_exists = False
        webcam_window = None
        if hasattr(self, 'webcam_windows') and client_key in self.webcam_windows:
            window_info = self.webcam_windows[client_key]
            if "window" in window_info and hasattr(window_info["window"], "winfo_exists"):
                try:
                    if window_info["window"].winfo_exists():
                        webcam_exists = True
                        webcam_window = window_info
                except:
                    pass
        if not webcam_exists:
            try:
                if cmd == core.protocol.CMD_WEBCAM_LIST_RESPONSE or cmd == core.protocol.CMD_WEBCAM_CAPTURE_RESPONSE:
                    self.server.log(f"Recebida resposta de webcam para {client_key}, abrindo janela")
                    window = self.open_webcam_window(client_address)
                    if window and client_key in self.webcam_windows:
                        webcam_window = self.webcam_windows[client_key]
                        webcam_exists = True
            except:
                pass
        if not webcam_exists:
            self.server.log(f"Recebida resposta de webcam para {client_key}, mas nenhuma janela foi encontrada")
            return
        try:
            if cmd == core.protocol.CMD_WEBCAM_LIST_RESPONSE:
                if "process_camera_list" in webcam_window and callable(webcam_window["process_camera_list"]):
                    webcam_window["process_camera_list"](data)
            elif cmd == core.protocol.CMD_WEBCAM_CAPTURE_RESPONSE:
                try:
                    header_size = int.from_bytes(data[:4], byteorder='big')
                    header_data = data[4:4+header_size]
                    header = json.loads(header_data.decode('utf-8'))
                    img_size_offset = 4 + header_size
                    img_size = int.from_bytes(data[img_size_offset:img_size_offset+4], byteorder='big')
                    img_data = data[img_size_offset+4:img_size_offset+4+img_size]
                    if "process_webcam_frame" in webcam_window and callable(webcam_window["process_webcam_frame"]):
                        webcam_window["process_webcam_frame"](header, img_data)
                except Exception as e:
                    self.server.log(f"Erro ao processar frame de webcam: {str(e)}")
            elif cmd == core.protocol.CMD_WEBCAM_STREAM_START:
                self.server.log(f"Resposta de início de streaming recebida para {client_key}")
            elif cmd == core.protocol.CMD_WEBCAM_STREAM_STOP:
                self.server.log(f"Resposta de parada de streaming recebida para {client_key}")
        except Exception as e:
            self.server.log(f"Erro ao processar resposta de webcam: {str(e)}")
    def open_shell_window(self, client_address):
        client_key = f"{client_address[0]}:{client_address[1]}"
        if client_key in self.closing_windows:
            self.server.log(f"Removendo {client_key} da lista de fechamento para permitir nova shell")
            self.closing_windows.discard(client_key)
        if client_key in self.shell_windows:
            window_info = self.shell_windows[client_key]
            if "window" in window_info and hasattr(window_info["window"], "winfo_exists"):
                try:
                    if window_info["window"].winfo_exists():
                        window_info["window"].focus_set()
                        return window_info["window"]
                except:
                    pass
        try:
            shell_window = ShellWindow(
                self.main_window,
                client_address,
                client_key,
                self.server,
                self.server.log
            )
            self.shell_windows[client_key] = {
                "window": shell_window.window,
                "process_response": shell_window.process_shell_response
            }
            return shell_window.window
        except Exception as e:
            self.server.log(f"Erro ao criar janela de shell: {str(e)}")
            return None
    def open_file_manager_window(self, client_address):
        client_key = f"{client_address[0]}:{client_address[1]}"
        if client_key in self.closing_windows:
            self.server.log(f"Removendo {client_key} da lista de fechamento para permitir novo gerenciador de arquivos")
            self.closing_windows.discard(client_key)
        if hasattr(self, 'file_manager_windows') and client_key in self.file_manager_windows:
            window_info = self.file_manager_windows[client_key]
            if "window" in window_info and hasattr(window_info["window"], "winfo_exists"):
                try:
                    if window_info["window"].winfo_exists():
                        window_info["window"].focus_set()
                        return window_info["window"]
                except:
                    pass
        try:
            file_manager_window = FileManagerWindow(
                self.main_window,
                client_address,
                client_key,
                self.server,
                self.server.log
            )
            if not hasattr(self, 'file_manager_windows'):
                self.file_manager_windows = {}
            self.file_manager_windows[client_key] = {
                "window": file_manager_window.window,
                "process_file_list_response": file_manager_window.process_file_list_response,
                "process_download_response": file_manager_window.process_download_response,
                "process_upload_response": file_manager_window.process_upload_response,
                "process_delete_response": file_manager_window.process_delete_response,
                "process_rename_response": file_manager_window.process_rename_response,
                "process_mkdir_response": file_manager_window.process_mkdir_response
            }
            return file_manager_window.window
        except Exception as e:
            self.server.log(f"Erro ao criar janela de gerenciador de arquivos: {str(e)}")
            return None
    def open_webcam_window(self, client_address):
        client_key = f"{client_address[0]}:{client_address[1]}"
        if client_key in self.closing_windows:
            self.server.log(f"Removendo {client_key} da lista de fechamento para permitir nova webcam")
            self.closing_windows.discard(client_key)
        if client_key in self.webcam_windows:
            window_info = self.webcam_windows[client_key]
            if "window" in window_info and hasattr(window_info["window"], "winfo_exists"):
                try:
                    if window_info["window"].winfo_exists():
                        window_info["window"].focus_set()
                        return window_info["window"]
                except:
                    pass
        try:
            webcam_window = WebcamWindow(
                self.main_window,
                client_address,
                client_key,
                self.server,
                self.server.log,
                self.webcam_windows,
                self.closing_windows
            )
            self.webcam_windows[client_key] = webcam_window.get_monitoring_info()
            return webcam_window.window
        except Exception as e:
            self.server.log(f"Erro ao criar janela de webcam: {str(e)}")
            return None
    def _create_new_screenshot_window(self, client_address, client_key, screenshot_data):
        try:
            screenshot_window = ScreenshotWindow(
                self.main_window,
                client_address,
                client_key,
                screenshot_data,
                self.server,
                self.server.log,
                self.screenshot_windows,
                self.closing_windows
            )
            self.screenshot_windows[client_key] = screenshot_window.get_monitoring_info()
            logger.info(f"Nova janela de captura criada para {client_key}")
        except Exception as e:
            logger.error(f"Erro ao criar janela de captura: {str(e)}")
            messagebox.showerror("Erro", f"Falha ao criar janela de captura: {str(e)}")
    def _update_screenshot_window(self, client_key, screenshot_data):
        try:
            if client_key not in self.screenshot_windows:
                logger.error(f"Cliente {client_key} não encontrado para atualizar imagem")
                return
            window_info = self.screenshot_windows[client_key]
            if window_info.get("is_closing", False):
                logger.info(f"Ignorando atualização para janela em fechamento: {client_key}")
                return
            if "update_image" in window_info and callable(window_info["update_image"]):
                window_info["update_image"](screenshot_data)
                logger.info(f"Imagem atualizada para {client_key}")
            else:
                logger.error(f"Método de atualização não encontrado para {client_key}")
        except Exception as e:
            logger.error(f"Erro ao atualizar imagem: {str(e)}")
    def _create_process_window(self, client_address, client_key, process_list):
        try:
            process_window = ProcessWindow(
                self.main_window,
                client_address,
                client_key,
                self.server,
                self.server.log
            )
            self.process_windows[client_key] = {
                "window": process_window.window,
                "update_process_list": process_window.update_process_list
            }
            process_window.update_process_list(process_list)
            logger.info(f"Janela de processos criada para {client_key}")
        except Exception as e:
            logger.error(f"Erro ao criar janela de processos: {str(e)}")
    def close_all_windows(self):
        for client_key, window_info in list(self.screenshot_windows.items()):
            if "window" in window_info and hasattr(window_info["window"], "winfo_exists"):
                try:
                    if window_info["window"].winfo_exists():
                        window_info["window"].destroy()
                except:
                    pass
        for client_key, window_info in list(self.process_windows.items()):
            if "window" in window_info and hasattr(window_info["window"], "winfo_exists"):
                try:
                    if window_info["window"].winfo_exists():
                        window_info["window"].destroy()
                except:
                    pass
        for client_key, window_info in list(self.shell_windows.items()):
            if "window" in window_info and hasattr(window_info["window"], "winfo_exists"):
                try:
                    if window_info["window"].winfo_exists():
                        window_info["window"].destroy()
                except:
                    pass
        if hasattr(self, 'file_manager_windows'):
            for client_key, window_info in list(self.file_manager_windows.items()):
                if "window" in window_info and hasattr(window_info["window"], "winfo_exists"):
                    try:
                        if window_info["window"].winfo_exists():
                            window_info["window"].destroy()
                    except:
                        pass
            self.file_manager_windows.clear()
        if hasattr(self, 'webcam_windows'):
            for client_key, window_info in list(self.webcam_windows.items()):
                if "window" in window_info and hasattr(window_info["window"], "winfo_exists"):
                    try:
                        if window_info["window"].winfo_exists():
                            window_info["window"].destroy()
                    except:
                        pass
            self.webcam_windows.clear()
        if hasattr(self, 'screen_stream_windows'):
            for client_key, window_info in list(self.screen_stream_windows.items()):
                if "window" in window_info and hasattr(window_info["window"], "winfo_exists"):
                    try:
                        if window_info["window"].winfo_exists():
                            window_info["window"].destroy()
                    except:
                        pass
            self.screen_stream_windows.clear()
        self.screenshot_windows.clear()
        self.process_windows.clear()
        self.shell_windows.clear()
        self.closing_windows.clear()
    def process_screen_stream_frame(self, client_address, data):
        client_key = f"{client_address[0]}:{client_address[1]}"
        if client_key in self.closing_windows:
            return
        screen_stream_exists = False
        screen_stream_window = None
        if client_key in self.screen_stream_windows:
            window_info = self.screen_stream_windows[client_key]
            if "window" in window_info and hasattr(window_info["window"], "winfo_exists"):
                try:
                    if window_info["window"].winfo_exists():
                        screen_stream_exists = True
                        screen_stream_window = window_info
                except:
                    pass
        if not screen_stream_exists:
            try:
                if core.protocol.CMD_SCREEN_STREAM_FRAME:
                    self.server.log(f"Recebido frame de stream de tela para {client_key}, abrindo janela")
                    window = self.open_screen_stream_window(client_address)
                    if window and client_key in self.screen_stream_windows:
                        screen_stream_window = self.screen_stream_windows[client_key]
                        screen_stream_exists = True
            except:
                pass
        if not screen_stream_exists:
            self.server.log(f"Recebido frame de stream de tela para {client_key}, mas nenhuma janela foi encontrada")
            return
        try:
            header_size = int.from_bytes(data[:4], byteorder='big')
            header_data = data[4:4+header_size]
            header = json.loads(header_data.decode('utf-8'))
            img_size_offset = 4 + header_size
            img_size = int.from_bytes(data[img_size_offset:img_size_offset+4], byteorder='big')
            img_data = data[img_size_offset+4:img_size_offset+4+img_size]
            if "process_screen_frame" in screen_stream_window and callable(screen_stream_window["process_screen_frame"]):
                screen_stream_window["process_screen_frame"](img_data)
        except Exception as e:
            self.server.log(f"Erro ao processar frame de stream de tela: {str(e)}")
    def open_screen_stream_window(self, client_address):
        client_key = f"{client_address[0]}:{client_address[1]}"
        if client_key in self.closing_windows:
            self.server.log(f"Removendo {client_key} da lista de fechamento para permitir stream de tela")
            self.closing_windows.discard(client_key)
        if client_key in self.screen_stream_windows:
            window_info = self.screen_stream_windows[client_key]
            if "window" in window_info and hasattr(window_info["window"], "winfo_exists"):
                try:
                    if window_info["window"].winfo_exists():
                        window_info["window"].focus_set()
                        return window_info["window"]
                except:
                    pass
        try:
            screen_stream_window = ScreenStreamWindow(
                self.main_window,
                client_address,
                client_key,
                self.server,
                self.server.log,
                self.screen_stream_windows,
                self.closing_windows
            )
            self.screen_stream_windows[client_key] = screen_stream_window.get_monitoring_info()
            return screen_stream_window.window
        except Exception as e:
            self.server.log(f"Erro ao criar janela de stream de tela: {str(e)}")
            return None
    def process_screen_stream_response(self, client_address, cmd, data):
        client_key = f"{client_address[0]}:{client_address[1]}"
        if client_key in self.closing_windows:
            return
        screen_stream_exists = False
        screen_stream_window = None
        if client_key in self.screen_stream_windows:
            window_info = self.screen_stream_windows[client_key]
            if "window" in window_info and hasattr(window_info["window"], "winfo_exists"):
                try:
                    if window_info["window"].winfo_exists():
                        screen_stream_exists = True
                        screen_stream_window = window_info
                except:
                    pass
        if not screen_stream_exists:
            self.server.log(f"Recebida resposta de streaming de tela para {client_key}, mas nenhuma janela foi encontrada")
            return
        try:
            response_text = data.decode('utf-8')
            self.server.log(f"Resposta de streaming de tela para {client_key}: {response_text}")
        except Exception as e:
            self.server.log(f"Erro ao processar resposta de streaming de tela: {str(e)}")

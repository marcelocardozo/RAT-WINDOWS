# client/managers/file_manager.py
import os
import json
import logging
import time
import shutil
import threading
logger = logging.getLogger("client.file_manager")
class FileManager:
    def __init__(self):
        self.running = False
        self.operation_lock = threading.RLock()
        self.last_error_time = 0
        self.consecutive_errors = 0
    def start(self):
        self.running = True
        logger.info("Gerenciador de arquivos iniciado")
    def stop(self):
        self.running = False
        logger.info("Gerenciador de arquivos parado")
    def _check_error_state(self):
        current_time = time.time()
        if current_time - self.last_error_time > 60:
            self.consecutive_errors = 0
            return True
        if self.consecutive_errors > 5:
            logger.warning(f"Muitos erros consecutivos ({self.consecutive_errors}), aplicando backoff")
            time.sleep(min(self.consecutive_errors * 0.5, 10))  # Máximo de 10 segundos de pausa
        return self.consecutive_errors < 20  # Falhar se ultrapassar 20 erros seguidos
    def _register_success(self):
        self.consecutive_errors = 0
    def _register_error(self):
        self.last_error_time = time.time()
        self.consecutive_errors += 1
    def list_directory(self, path):
        if not self._check_error_state():
            return {"error": "Muitos erros consecutivos, tentando recuperar"}
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                with self.operation_lock:
                    if not path:
                        path = "/"
                    path = path.replace('\\', '/')
                    if path == "/":
                        sys_path = os.path.abspath(os.sep)
                    else:
                        sys_path = os.path.abspath(path)
                    logger.info(f"Listando diretório: {sys_path}")
                    if not os.path.exists(sys_path):
                        self._register_error()
                        return {"error": f"Caminho não encontrado: {path}"}
                    if not os.path.isdir(sys_path):
                        self._register_error()
                        return {"error": f"O caminho não é um diretório: {path}"}
                    files = []
                    try:
                        entries = os.scandir(sys_path)
                        for entry in entries:
                            try:
                                stat_info = entry.stat()
                                file_info = {
                                    "name": entry.name,
                                    "type": "directory" if entry.is_dir() else "file",
                                    "size": stat_info.st_size if not entry.is_dir() else 0,
                                    "modified": stat_info.st_mtime
                                }
                                files.append(file_info)
                            except PermissionError:
                                pass
                            except Exception as e:
                                logger.warning(f"Erro ao obter informações do item {entry.name}: {str(e)}")
                    except PermissionError:
                        self._register_error()
                        return {"error": f"Permissão negada para listar o diretório: {path}"}
                    self._register_success()
                    return {
                        "path": path,
                        "files": files
                    }
            except Exception as e:
                logger.error(f"Erro ao listar diretório {path}: {str(e)}")
                retry_count += 1
                if retry_count >= max_retries:
                    self._register_error()
                    return {"error": f"Erro ao listar diretório: {str(e)}"}
                time.sleep(0.5)  # Pequeno delay entre tentativas
    def read_file(self, path):
        if not self._check_error_state():
            return {"error": "Muitos erros consecutivos, tentando recuperar"}
        try:
            with self.operation_lock:
                path = path.replace('\\', '/')
                sys_path = os.path.abspath(path)
                logger.info(f"Lendo arquivo: {sys_path}")
                if not os.path.exists(sys_path):
                    self._register_error()
                    return {"error": f"Arquivo não encontrado: {path}"}
                if not os.path.isfile(sys_path):
                    self._register_error()
                    return {"error": f"O caminho não é um arquivo: {path}"}
                size = os.path.getsize(sys_path)
                if size > 100 * 1024 * 1024:  # Limitar a 100MB
                    self._register_error()
                    return {"error": f"Arquivo muito grande ({size/1024/1024:.1f}MB). Limite: 100MB"}
                if size > 10 * 1024 * 1024:  # 10MB
                    logger.info(f"Lendo arquivo grande ({size/1024/1024:.1f}MB) em chunks")
                    try:
                        with open(sys_path, 'rb') as f:
                            content = f.read()
                        self._register_success()
                        return content
                    except MemoryError:
                        self._register_error()
                        return {"error": f"Arquivo muito grande para a memória disponível: {size/1024/1024:.1f}MB"}
                else:
                    with open(sys_path, 'rb') as f:
                        content = f.read()
                    self._register_success()
                    return content
        except PermissionError:
            logger.error(f"Permissão negada para ler o arquivo: {path}")
            self._register_error()
            return {"error": f"Permissão negada para ler o arquivo: {path}"}
        except Exception as e:
            logger.error(f"Erro ao ler arquivo {path}: {str(e)}")
            self._register_error()
            return {"error": f"Erro ao ler arquivo: {str(e)}"}
    def write_file(self, path, content):
        if not self._check_error_state():
            return {"error": "Muitos erros consecutivos, tentando recuperar"}
        try:
            with self.operation_lock:
                path = path.replace('\\', '/')
                sys_path = os.path.abspath(path)
                logger.info(f"Escrevendo arquivo: {sys_path}")
                parent_dir = os.path.dirname(sys_path)
                if not os.path.exists(parent_dir):
                    try:
                        os.makedirs(parent_dir)
                    except:
                        self._register_error()
                        return {"error": f"Não foi possível criar o diretório pai: {parent_dir}"}
                if isinstance(content, str):
                    try:
                        content = content.encode('utf-8')
                    except UnicodeEncodeError:
                        self._register_error()
                        return {"error": "Falha ao codificar string para bytes"}
                elif not isinstance(content, (bytes, bytearray)):
                    try:
                        content = bytes(content)
                    except:
                        self._register_error()
                        return {"error": f"Tipo de conteúdo não suportado: {type(content)}"}
                content_size = len(content)
                if content_size > 10 * 1024 * 1024:  # 10MB
                    logger.info(f"Gravando arquivo grande ({content_size/1024/1024:.1f}MB) em chunks")
                    try:
                        with open(sys_path, 'wb') as f:
                            chunk_size = 1024 * 1024  # 1MB chunks
                            for i in range(0, content_size, chunk_size):
                                f.write(content[i:i+chunk_size])
                        self._register_success()
                        return {
                            "status": "success",
                            "path": path,
                            "size": content_size
                        }
                    except Exception as e:
                        self._register_error()
                        logger.error(f"Erro ao gravar arquivo grande: {str(e)}")
                        return {"error": f"Erro ao gravar arquivo grande: {str(e)}"}
                else:
                    with open(sys_path, 'wb') as f:
                        f.write(content)
                    self._register_success()
                    return {
                        "status": "success",
                        "path": path,
                        "size": content_size
                    }
        except PermissionError:
            logger.error(f"Permissão negada para escrever no arquivo: {path}")
            self._register_error()
            return {"error": f"Permissão negada para escrever no arquivo: {path}"}
        except Exception as e:
            logger.error(f"Erro ao escrever arquivo {path}: {str(e)}")
            self._register_error()
            return {"error": f"Erro ao escrever arquivo: {str(e)}"}
    def delete_item(self, path):
        if not self._check_error_state():
            return {"error": "Muitos erros consecutivos, tentando recuperar"}
        try:
            with self.operation_lock:
                path = path.replace('\\', '/')
                sys_path = os.path.abspath(path)
                logger.info(f"Excluindo item: {sys_path}")
                if not os.path.exists(sys_path):
                    self._register_error()
                    return {"error": f"Item não encontrado: {path}"}
                if os.path.isdir(sys_path):
                    try:
                        shutil.rmtree(sys_path)
                    except:
                        os.rmdir(sys_path)
                else:
                    os.remove(sys_path)
                self._register_success()
                return {
                    "status": "success",
                    "path": path
                }
        except PermissionError:
            logger.error(f"Permissão negada para excluir o item: {path}")
            self._register_error()
            return {"error": f"Permissão negada para excluir o item: {path}"}
        except Exception as e:
            logger.error(f"Erro ao excluir item {path}: {str(e)}")
            self._register_error()
            return {"error": f"Erro ao excluir item: {str(e)}"}
    def rename_item(self, old_path, new_path):
        if not self._check_error_state():
            return {"error": "Muitos erros consecutivos, tentando recuperar"}
        try:
            with self.operation_lock:
                old_path = old_path.replace('\\', '/')
                new_path = new_path.replace('\\', '/')
                sys_old_path = os.path.abspath(old_path)
                sys_new_path = os.path.abspath(new_path)
                logger.info(f"Renomeando item: {sys_old_path} -> {sys_new_path}")
                if not os.path.exists(sys_old_path):
                    self._register_error()
                    return {"error": f"Item não encontrado: {old_path}"}
                if os.path.exists(sys_new_path):
                    self._register_error()
                    return {"error": f"Já existe um item com este nome: {new_path}"}
                os.rename(sys_old_path, sys_new_path)
                self._register_success()
                return {
                    "status": "success",
                    "old_path": old_path,
                    "new_path": new_path
                }
        except PermissionError:
            logger.error(f"Permissão negada para renomear o item: {old_path}")
            self._register_error()
            return {"error": f"Permissão negada para renomear o item: {old_path}"}
        except Exception as e:
            logger.error(f"Erro ao renomear item {old_path}: {str(e)}")
            self._register_error()
            return {"error": f"Erro ao renomear item: {str(e)}"}
    def create_directory(self, path):
        if not self._check_error_state():
            return {"error": "Muitos erros consecutivos, tentando recuperar"}
        try:
            with self.operation_lock:
                path = path.replace('\\', '/')
                sys_path = os.path.abspath(path)
                logger.info(f"Criando diretório: {sys_path}")
                if os.path.exists(sys_path):
                    self._register_error()
                    return {"error": f"Já existe um item com este nome: {path}"}
                os.makedirs(sys_path)
                self._register_success()
                return {
                    "status": "success",
                    "path": path
                }
        except PermissionError:
            logger.error(f"Permissão negada para criar o diretório: {path}")
            self._register_error()
            return {"error": f"Permissão negada para criar o diretório: {path}"}
        except Exception as e:
            logger.error(f"Erro ao criar diretório {path}: {str(e)}")
            self._register_error()
            return {"error": f"Erro ao criar diretório: {str(e)}"}

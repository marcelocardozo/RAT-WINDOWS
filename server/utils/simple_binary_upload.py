# server/utils/simple_binary_upload.py
import struct
import json
import logging
import os
import time
import tempfile
logger = logging.getLogger("utils.simple_binary_upload")
class SimpleBinaryUpload:
    @staticmethod
    def create_upload_payload(path, file_data):
        try:
            path = path.replace('\\', '/')
            header = {
                "path": path, 
                "size": len(file_data),
                "timestamp": int(os.path.getmtime(path) if os.path.exists(path) else time.time()),
                "file_extension": os.path.splitext(path)[1]
            }
            header_json = json.dumps(header)
            header_bytes = header_json.encode('utf-8')
            header_size = struct.pack('>I', len(header_bytes))
            return header_size + header_bytes + file_data
        except Exception as e:
            logger.error(f"Error creating upload payload: {str(e)}")
            raise
    @staticmethod
    def parse_upload_request(socket, max_file_size=100 * 1024 * 1024):  # Aumentado para 100MB
        try:
            header_size_bytes = socket.recv(4)
            if len(header_size_bytes) < 4:
                logger.error("Falha ao ler o tamanho do cabeçalho")
                return None
            header_size = struct.unpack('>I', header_size_bytes)[0]
            header_bytes = b''
            while len(header_bytes) < header_size:
                chunk = socket.recv(min(4096, header_size - len(header_bytes)))
                if not chunk:
                    logger.error("Conexão encerrada ao ler o cabeçalho")
                    return None
                header_bytes += chunk
            header_json = header_bytes.decode('utf-8')
            header = json.loads(header_json)
            file_size = header.get("size", 0)
            if file_size <= 0:
                logger.error(f"Tamanho de arquivo inválido: {file_size}")
                return None
            if file_size > max_file_size:
                logger.error(f"Tamanho de arquivo excede o limite: {file_size} > {max_file_size}")
                return None
            import tempfile
            import os
            TEMP_FILE_THRESHOLD = 10 * 1024 * 1024
            if file_size > TEMP_FILE_THRESHOLD:
                logger.info(f"Arquivo grande ({file_size/1024/1024:.1f}MB), usando arquivo temporário")
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                temp_path = temp_file.name
                file_data = None  # Não armazenar em memória
                bytes_read = 0
                chunk_size = 8192
                progress_interval = max(1, file_size // 20)  # Reportar progresso a cada 5%
                last_progress = 0
                try:
                    while bytes_read < file_size:
                        chunk = socket.recv(min(chunk_size, file_size - bytes_read))
                        if not chunk:
                            logger.error("Conexão encerrada ao ler dados do arquivo")
                            temp_file.close()
                            os.unlink(temp_path)
                            return None
                        temp_file.write(chunk)
                        bytes_read += len(chunk)
                        if bytes_read - last_progress >= progress_interval:
                            percent = (bytes_read / file_size) * 100
                            logger.info(f"Progresso do recebimento: {percent:.1f}% ({bytes_read}/{file_size} bytes)")
                            last_progress = bytes_read
                    temp_file.flush()
                    temp_file.close()
                    with open(temp_path, 'rb') as f:
                        file_data = f.read()
                    os.unlink(temp_path)
                    return {
                        "header": header,
                        "file_data": file_data,
                        "path": header.get("path", ""),
                        "size": file_size
                    }
                except Exception as e:
                    logger.error(f"Erro ao receber arquivo grande: {str(e)}")
                    try:
                        temp_file.close()
                        os.unlink(temp_path)
                    except:
                        pass
                    return None
            else:
                file_data = b''
                while len(file_data) < file_size:
                    chunk = socket.recv(min(4096, file_size - len(file_data)))
                    if not chunk:
                        logger.error("Conexão encerrada ao ler dados do arquivo")
                        return None
                    file_data += chunk
                return {
                    "header": header,
                    "file_data": file_data,
                    "path": header.get("path", ""),
                    "size": file_size
                }
        except Exception as e:
            logger.exception(f"Erro ao processar upload: {str(e)}")
            return None

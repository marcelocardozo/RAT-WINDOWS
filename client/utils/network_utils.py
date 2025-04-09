# client/utils/network_utils.py
import socket
import struct
import json
import logging
import time
logger = logging.getLogger("client.network_utils")
def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        logger.warning("Não foi possível obter IP, usando localhost")
        return "127.0.0.1"
def send_binary_command(socket, cmd, data=None):
    max_retries = 3
    retry_count = 0
    while retry_count < max_retries:
        try:
            if not socket:
                return False
            header = struct.pack('>I', cmd)
            if data:
                size = struct.pack('>I', len(data))
                socket.sendall(header + size + data)
            else:
                socket.sendall(header)
            return True
        except ConnectionError as e:
            logger.error(f"Erro de conexão ao enviar comando (tentativa {retry_count+1}/{max_retries}): {str(e)}")
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(0.5)  # Pequena pausa antes de tentar novamente
            else:
                raise
        except Exception as e:
            logger.error(f"Erro ao enviar comando: {str(e)}")
            return False
def send_raw_binary_command(socket, cmd, data):
    max_retries = 3
    retry_count = 0
    while retry_count < max_retries:
        try:
            if not socket:
                return False
            header = struct.pack('>I', cmd)
            socket.sendall(header + data)
            return True
        except ConnectionError as e:
            logger.error(f"Erro de conexão ao enviar comando (tentativa {retry_count+1}/{max_retries}): {str(e)}")
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(0.5)  # Pequena pausa antes de tentar novamente
            else:
                raise
        except Exception as e:
            logger.error(f"Erro ao enviar comando: {str(e)}")
            return False
def recv_exact(socket, size, timeout=30, buffer_size=8192):
    if size <= 0:
        return b""
    original_timeout = socket.gettimeout()
    max_chunk_size = min(buffer_size, size)
    try:
        socket.settimeout(timeout)
        data = bytearray(size)
        view = memoryview(data)
        bytes_recd = 0
        while bytes_recd < size:
            try:
                chunk_size = min(max_chunk_size, size - bytes_recd)
                chunk = socket.recv(chunk_size)
                if not chunk:
                    if bytes_recd == 0:
                        return None
                    raise ConnectionError("Conexão fechada pelo peer durante recebimento")
                n = len(chunk)
                view[bytes_recd:bytes_recd + n] = chunk
                bytes_recd += n
            except socket.timeout:
                logger.warning(f"Timeout ao receber dados ({timeout}s) - recebido {bytes_recd}/{size} bytes")
                raise
            except BlockingIOError:
                time.sleep(0.01)
                continue
            except ConnectionError as e:
                logger.error(f"Erro de conexão durante recebimento: {str(e)}")
                if bytes_recd == 0:
                    return None
                raise
        return data
    except socket.timeout:
        logger.error(f"Timeout ao receber dados ({timeout}s)")
        return None
    except ConnectionError as e:
        logger.error(f"Erro de conexão: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Erro ao receber dados: {str(e)}")
        return None
    finally:
        try:
            socket.settimeout(original_timeout)
        except:
            pass

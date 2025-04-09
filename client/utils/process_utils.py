# client/utils/process_utils.py
import psutil
import logging
import time
import os
import signal
logger = logging.getLogger("client.process_utils")
def get_process_by_pid(pid):
    try:
        return psutil.Process(pid)
    except psutil.NoSuchProcess:
        logger.warning(f"Processo {pid} não encontrado")
        return None
    except Exception as e:
        logger.error(f"Erro ao obter processo {pid}: {str(e)}")
        return None
def kill_process(pid, timeout=5):
    try:
        process = get_process_by_pid(pid)
        if not process:
            logger.error(f"Processo {pid} não existe")
            return False
        process_name = process.name()
        try:
            logger.info(f"Tentando terminar processo {pid} ({process_name})")
            process.terminate()
            try:
                process.wait(timeout=timeout)
                logger.info(f"Processo {pid} ({process_name}) terminado")
                return True
            except psutil.TimeoutExpired:
                logger.warning(f"Timeout ao encerrar processo {pid}, forçando")
                process.kill()
                process.wait(timeout=1)
                logger.info(f"Processo {pid} ({process_name}) terminado forçadamente")
                return True
        except (psutil.AccessDenied, psutil.NoSuchProcess) as e:
            logger.error(f"Erro ao encerrar processo {pid}: {str(e)}")
            try:
                logger.info(f"Tentando matar processo {pid} com sinais do sistema")
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.5)
                if psutil.pid_exists(pid):
                    os.kill(pid, signal.SIGKILL)
                    time.sleep(0.5)
                success = not psutil.pid_exists(pid)
                logger.info(f"Resultado após tentativa alternativa: {success}")
                return success
            except Exception as e2:
                logger.error(f"Erro final ao encerrar processo {pid}: {str(e2)}")
                return False
    except Exception as e:
        logger.error(f"Erro geral ao encerrar processo {pid}: {str(e)}")
        return False
def format_process_uptime(seconds):
    if seconds < 0:
        return "N/A"
    if seconds < 60:
        return f"{seconds} segundos"
    elif seconds < 3600:
        return f"{seconds // 60} minutos"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h"
def get_process_children(pid):
    try:
        process = get_process_by_pid(pid)
        if not process:
            return []
        return process.children(recursive=True)
    except Exception as e:
        logger.error(f"Erro ao obter processos filhos de {pid}: {str(e)}")
        return []

# server/main.py
import os
import sys
import tkinter as tk
import logging
from gui.main_window import ServerMainWindow
from core.socket_server import SocketServer
from managers.log_manager import LogManager
from managers.process_manager import ProcessManager
from config import LOG_LEVEL, LOG_FORMAT
def main():
    log_manager = LogManager(LOG_LEVEL, LOG_FORMAT)
    logger = log_manager.setup_logging()
    logger.info("Iniciando servidor de monitoramento")
    try:
        root = tk.Tk()
        root.title("Servidor de Monitoramento")
        server = SocketServer()
        process_manager = ProcessManager()
        server.process_handler.set_process_manager(process_manager)
        app = ServerMainWindow(root, server)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        logger.info("Interface gráfica iniciada")
        root.mainloop()
    except Exception as e:
        logger.error(f"Erro ao iniciar servidor: {str(e)}", exc_info=True)
        sys.exit(1)
    logger.info("Servidor finalizado normalmente")
if __name__ == "__main__":
    main()

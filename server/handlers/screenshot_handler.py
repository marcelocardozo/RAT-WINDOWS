# server/handlers/screenshot_handler.py
import logging
import threading
import base64
from io import BytesIO
from PIL import Image
logger = logging.getLogger("server.screenshot_handler")
class ScreenshotHandler:
    def __init__(self, server):
        self.server = server
    def process_screenshot(self, client_address, screenshot_data):
        client_key = f"{client_address[0]}:{client_address[1]}"
        try:
            if not self._validate_image_format(screenshot_data):
                logger.error(f"Formato de imagem inválido de {client_key}")
                return False
            screenshot_b64 = base64.b64encode(screenshot_data).decode('utf-8')
            if self.server.screenshot_callback:
                self.server.screenshot_callback(client_address, screenshot_b64)
                logger.info(f"Screenshot processado para {client_key}")
                return True
            else:
                logger.warning(f"Sem callback para screenshot de {client_key}")
                return False
        except Exception as e:
            logger.error(f"Erro ao processar screenshot de {client_key}: {str(e)}")
            try:
                screenshot_b64 = base64.b64encode(screenshot_data).decode('utf-8')
                if self.server.screenshot_callback:
                    self.server.screenshot_callback(client_address, screenshot_b64)
                    logger.info(f"Screenshot enviado após falha de verificação para {client_key}")
                    return True
            except Exception as e2:
                logger.error(f"Erro final ao processar screenshot: {str(e2)}")
            return False
    def _validate_image_format(self, image_data):
        is_jpeg = len(image_data) >= 2 and image_data[0] == 0xFF and image_data[1] == 0xD8
        is_png = (len(image_data) >= 4 and 
                 image_data[0] == 0x89 and 
                 image_data[1] == 0x50 and 
                 image_data[2] == 0x4E and 
                 image_data[3] == 0x47)
        if is_jpeg:
            logger.debug("Formato de imagem: JPEG")
        elif is_png:
            logger.debug("Formato de imagem: PNG")
        else:
            logger.warning("Formato de imagem não reconhecido")
        return True
    def request_screenshot(self, client_address):
        if client_address not in self.server.connection_manager.client_handlers:
            logger.error(f"Cliente não encontrado: {client_address}")
            return False
        return self.server.connection_manager.client_handlers[client_address].send_command({"action": "screenshot"})

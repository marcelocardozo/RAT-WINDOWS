# client/collectors/screenshot_collector.py
import io
import logging
import threading
from PIL import ImageGrab, Image
from utils.image_utils import resize_image, convert_to_format, optimize_image
from config import SCREENSHOT_MAX_SIZE, SCREENSHOT_QUALITY, SCREENSHOT_FORMAT
logger = logging.getLogger("client.screenshot_collector")
class ScreenshotCollector:
    def __init__(self):
        self.lock = threading.Lock()
    def capture(self, max_size=SCREENSHOT_MAX_SIZE, quality=SCREENSHOT_QUALITY, format=SCREENSHOT_FORMAT):
        try:
            screenshot = ImageGrab.grab()
            if not screenshot or screenshot.width <= 0 or screenshot.height <= 0:
                logger.error(f"Screenshot capturado inválido: {screenshot}")
                return None
            logger.info(f"Imagem capturada: {screenshot.width}x{screenshot.height}, modo: {screenshot.mode}")
            if screenshot.width > max_size or screenshot.height > max_size:
                screenshot = resize_image(screenshot, max_size)
            if format.upper() == "JPEG" and screenshot.mode not in ('RGB', 'L'):
                screenshot = convert_to_format(screenshot, format)
            image_bytes = optimize_image(screenshot, format, quality)
            if not image_bytes:
                logger.error("Falha ao otimizar imagem")
                return None
            return image_bytes
        except Exception as e:
            logger.error(f"Erro ao capturar tela: {str(e)}")
            return None

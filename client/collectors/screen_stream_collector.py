# client/collectors/screen_stream_collector.py
import logging
import threading
import time
from PIL import ImageGrab, Image
from utils.image_utils import resize_image, convert_to_format, optimize_image
from config import SCREEN_STREAM_MAX_SIZE, SCREEN_STREAM_QUALITY, SCREEN_STREAM_FORMAT
logger = logging.getLogger("client.screen_stream_collector")
class ScreenStreamCollector:
    def __init__(self):
        self.lock = threading.Lock()
        self.running = False
        self.streaming_thread = None
        self.callback = None
        self.interval = 0.1
        self.quality = 50
        self.max_size = SCREEN_STREAM_MAX_SIZE if 'SCREEN_STREAM_MAX_SIZE' in globals() else 1024
        self.format = SCREEN_STREAM_FORMAT if 'SCREEN_STREAM_FORMAT' in globals() else "JPEG"
        self.error_count = 0
        self.max_errors = 10
    def start_streaming(self, callback, interval=0.1, quality=None, max_size=None):
        if self.running:
            return False
        with self.lock:
            self.running = True
            self.callback = callback
            self.interval = max(0.033, interval)
            self.quality = quality if quality is not None else SCREEN_STREAM_QUALITY if 'SCREEN_STREAM_QUALITY' in globals() else 50
            self.max_size = max_size if max_size is not None else self.max_size
            self.error_count = 0
            self.streaming_thread = threading.Thread(
                target=self._streaming_loop,
                daemon=True
            )
            self.streaming_thread.start()
            logger.info(f"Screen streaming started with interval={self.interval}s, quality={self.quality}")
            return True
    def stop_streaming(self):
        if not self.running:
            return
        logger.info("Stopping screen streaming...")
        with self.lock:
            self.running = False
        if self.streaming_thread:
            try:
                self.streaming_thread.join(timeout=2.0)
            except:
                pass
            self.streaming_thread = None
        logger.info("Screen streaming stopped")
    def _streaming_loop(self):
        last_capture_time = 0
        while self.running:
            current_time = time.time()
            if current_time - last_capture_time >= self.interval:
                try:
                    with self.lock:
                        if not self.running:
                            break
                        screenshot = ImageGrab.grab()
                        if not screenshot or screenshot.width <= 0 or screenshot.height <= 0:
                            logger.error("Invalid screenshot captured")
                            self.error_count += 1
                            if self.error_count > self.max_errors:
                                logger.error(f"Too many streaming errors ({self.error_count}), stopping stream")
                                self.running = False
                                break
                            continue
                        logger.debug(f"Image captured: {screenshot.width}x{screenshot.height}, mode: {screenshot.mode}")
                        if screenshot.width > self.max_size or screenshot.height > self.max_size:
                            screenshot = resize_image(screenshot, self.max_size)
                        if self.format.upper() == "JPEG" and screenshot.mode not in ('RGB', 'L'):
                            screenshot = convert_to_format(screenshot, self.format)
                        image_bytes = optimize_image(screenshot, self.format, self.quality)
                        if not image_bytes:
                            logger.error("Failed to optimize image")
                            self.error_count += 1
                            if self.error_count > self.max_errors:
                                logger.error(f"Too many streaming errors ({self.error_count}), stopping stream")
                                self.running = False
                                break
                            continue
                        last_capture_time = time.time()
                        self.error_count = 0
                        if self.callback:
                            self.callback(image_bytes)
                except Exception as e:
                    logger.error(f"Error in screen streaming loop: {str(e)}")
                    self.error_count += 1
                    if self.error_count > self.max_errors:
                        logger.error(f"Too many streaming errors, stopping")
                        self.running = False
                        break
            time.sleep(0.005)

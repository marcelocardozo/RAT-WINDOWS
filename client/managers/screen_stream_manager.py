# client/managers/screen_stream_manager.py
import logging
import threading
import time
from collectors.screen_stream_collector import ScreenStreamCollector
logger = logging.getLogger("client.screen_stream_manager")
class ScreenStreamManager:
    def __init__(self):
        self.collector = None
        self.running = False
        self.streaming = False
        self.streaming_interval = 0.1
        self.streaming_quality = None
        self.streaming_max_size = None
        self.capture_lock = threading.Lock()
        self.stream_callback = None
        self.last_stream_error = 0
        self.stream_error_count = 0
        self.max_stream_errors = 10
        self.initialized = False
    def start(self):
        self.running = True
        logger.info("ScreenStreamManager started (collector will be initialized when needed)")
    def _ensure_initialized(self):
        if not self.initialized:
            logger.info("Initializing screen stream collector on first use")
            self.collector = ScreenStreamCollector()
            self.initialized = True
            return True
        return False
    def stop(self):
        self.stop_streaming()
        self.running = False
        logger.info("Screen stream manager stopped")
        self.initialized = False
    def start_streaming(self, interval=0.1, callback=None, quality=None, max_size=None):
        self._ensure_initialized()
        if self.streaming:
            self.stop_streaming()
            time.sleep(0.2)
        self.streaming = True
        self.streaming_interval = max(0.033, interval)
        self.streaming_quality = quality
        self.streaming_max_size = max_size
        self.stream_callback = callback
        self.stream_error_count = 0
        self.last_stream_error = 0
        success = self.collector.start_streaming(
            callback=callback,
            interval=self.streaming_interval,
            quality=self.streaming_quality,
            max_size=self.streaming_max_size
        )
        logger.info(f"Started screen streaming at {self.streaming_interval}s intervals")
        return success
    def stop_streaming(self):
        if not self.streaming:
            return
        logger.info("Stopping screen streaming...")
        self.streaming = False
        if self.initialized and self.collector:
            try:
                self.collector.stop_streaming()
            except:
                pass
        logger.info("Screen streaming stopped")

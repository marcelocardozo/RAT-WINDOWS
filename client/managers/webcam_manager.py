# client/managers/webcam_manager.py
import logging
import threading
import time
from collectors.webcam_collector import WebcamCollector
logger = logging.getLogger("client.webcam_manager")
class WebcamManager:
    def __init__(self):
        self.collector = None  # Não criar o coletor na inicialização
        self.running = False
        self.streaming = False
        self.streaming_camera_id = 0
        self.streaming_interval = 0.1  # Default interval in seconds (reduzido para maior fluidez)
        self.streaming_quality = None  # Qualidade de streaming, None usa o padrão
        self.capture_lock = threading.Lock()
        self.stream_thread = None
        self.stream_callback = None
        self.last_stream_error = 0
        self.stream_error_count = 0
        self.max_stream_errors = 10  # Número máximo de erros antes de parar o streaming
        self.initialized = False
    def start(self):
        self.running = True
        logger.info("WebcamManager started (webcam will be initialized when needed)")
    def _ensure_initialized(self):
        if not self.initialized:
            logger.info("Initializing webcam collector on first use")
            self.collector = WebcamCollector()
            self.initialized = True
            return True
        return False
    def stop(self):
        self.stop_streaming()
        self.running = False
        if self.initialized and self.collector:
            try:
                self.collector.release_all_cameras()
            except:
                pass
        logger.info("Webcam manager stopped")
        self.initialized = False
    def get_available_cameras(self):
        self._ensure_initialized()
        return self.collector.get_available_cameras()
    def capture(self, camera_id=0, quality=None):
        if not self.running:
            logger.warning("Capture ignored: webcam manager is not running")
            return None
        self._ensure_initialized()
        lock_acquired = False
        try:
            lock_acquired = self.capture_lock.acquire(blocking=False)
            if not lock_acquired:
                logger.info("A capture is already in progress, ignoring request")
                return None
            image_bytes = self.collector.capture(camera_id, quality=quality)
            if image_bytes:
                logger.info(f"Webcam capture completed: {len(image_bytes) / 1024:.2f} KB")
            else:
                logger.error("Failed to capture from webcam")
            return image_bytes
        except Exception as e:
            logger.error(f"Error capturing from webcam: {str(e)}")
            return None
        finally:
            if lock_acquired:
                self.capture_lock.release()
    def start_streaming(self, camera_id=0, interval=0.1, callback=None, quality=None):
        self._ensure_initialized()
        if self.streaming:
            self.stop_streaming()
            time.sleep(0.2)
        self.streaming = True
        self.streaming_camera_id = camera_id
        self.streaming_interval = max(0.033, interval)  # Limitar a aproximadamente 30 FPS
        self.streaming_quality = quality
        self.stream_callback = callback
        self.stream_error_count = 0
        self.last_stream_error = 0
        self.stream_thread = threading.Thread(
            target=self._streaming_loop, 
            daemon=True
        )
        self.stream_thread.start()
        logger.info(f"Started streaming from camera {camera_id} at {self.streaming_interval}s intervals")
        return True
    def stop_streaming(self):
        if not self.streaming:
            return
        logger.info("Stopping webcam streaming...")
        self.streaming = False
        if self.stream_thread:
            try:
                self.stream_thread.join(timeout=2.0)
            except:
                pass
            self.stream_thread = None
        if self.initialized and self.collector:
            try:
                self.collector.release_camera(self.streaming_camera_id)
            except:
                pass
        logger.info("Webcam streaming stopped")
    def _streaming_loop(self):
        if not self.initialized or not self.collector:
            logger.error("Streaming loop attempted to run without initialized collector")
            self.streaming = False
            return
        last_capture_time = 0
        while self.streaming and self.running:
            current_time = time.time()
            if current_time - last_capture_time >= self.streaming_interval:
                try:
                    if self.capture_lock.acquire(timeout=0.1):
                        try:
                            image_bytes = self.collector.capture(
                                self.streaming_camera_id,
                                quality=self.streaming_quality
                            )
                            last_capture_time = time.time()
                            if image_bytes and self.stream_callback:
                                self.stream_callback(image_bytes)
                                self.stream_error_count = 0
                            elif not image_bytes:
                                self.stream_error_count += 1
                                current_time = time.time()
                                if self.stream_error_count > self.max_stream_errors:
                                    logger.error(f"Too many streaming errors ({self.stream_error_count}), stopping stream")
                                    self.streaming = False
                                    break
                                if current_time - self.last_stream_error > 2.0:
                                    logger.error(f"Failed to capture streaming frame (error {self.stream_error_count})")
                                    self.last_stream_error = current_time
                        except Exception as e:
                            logger.error(f"Error in streaming loop: {str(e)}")
                            self.stream_error_count += 1
                        finally:
                            self.capture_lock.release()
                    else:
                        logger.debug("Couldn't acquire lock for streaming frame, skipping")
                except Exception as e:
                    logger.error(f"Streaming loop error: {str(e)}")
                    self.stream_error_count += 1
                    if self.stream_error_count > self.max_stream_errors:
                        logger.error(f"Too many streaming errors, stopping")
                        self.streaming = False
                        break
            time.sleep(0.005)  # 5ms de pausa
        if self.initialized and self.collector:
            try:
                self.collector.release_camera(self.streaming_camera_id)
            except:
                pass

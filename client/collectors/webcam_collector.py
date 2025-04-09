# client/collectors/webcam_collector.py
import cv2
import logging
import threading
import base64
import io
import numpy as np
import time
from PIL import Image
from utils.image_utils import resize_image, convert_to_format, optimize_image
from config import WEBCAM_MAX_SIZE, WEBCAM_QUALITY, WEBCAM_FORMAT
logger = logging.getLogger("client.webcam_collector")
class WebcamCollector:
    def __init__(self):
        self.lock = threading.Lock()
        self.active_cameras = {}  # Mantém referências para câmeras abertas
        self.available_cameras = []
    def _scan_cameras(self):
        with self.lock:
            self.available_cameras = []
            max_cameras = 10  # Max number of cameras to check
            for i in range(max_cameras):
                try:
                    cap = cv2.VideoCapture(i)
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret:
                            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                            name = f"Camera {i}"
                            try:
                                backend_name = cap.getBackendName() if hasattr(cap, 'getBackendName') else "Unknown"
                                if backend_name and backend_name != "Unknown":
                                    name = f"{backend_name} ({i})"
                            except:
                                pass
                            self.available_cameras.append({
                                'id': i,
                                'name': name,
                                'resolution': f"{width}x{height}"
                            })
                        cap.release()
                except Exception as e:
                    logger.debug(f"Error checking camera {i}: {str(e)}")
                    continue
            logger.info(f"Found {len(self.available_cameras)} available cameras")
            return self.available_cameras
    def get_available_cameras(self):
        if not self.available_cameras:
            return self._scan_cameras()
        return self.available_cameras
    def _get_camera(self, camera_id):
        if camera_id in self.active_cameras:
            cap = self.active_cameras[camera_id]['cap']
            if not cap.isOpened():
                logger.warning(f"Camera {camera_id} estava aberta mas não está mais funcionando, reabrindo...")
                cap = cv2.VideoCapture(camera_id)
                if not cap.isOpened():
                    return None
                self.active_cameras[camera_id]['cap'] = cap
            return cap
        else:
            cap = cv2.VideoCapture(camera_id)
            if not cap.isOpened():
                return None
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduzir buffer para menor latência
            self.active_cameras[camera_id] = {
                'cap': cap,
                'last_used': time.time(),
                'frame_count': 0
            }
            logger.info(f"Camera {camera_id} aberta e adicionada ao pool de câmeras ativas")
            return cap
    def release_camera(self, camera_id):
        with self.lock:
            if camera_id in self.active_cameras:
                try:
                    self.active_cameras[camera_id]['cap'].release()
                    logger.info(f"Camera {camera_id} liberada")
                except Exception as e:
                    logger.error(f"Erro ao liberar camera {camera_id}: {str(e)}")
                del self.active_cameras[camera_id]
    def release_all_cameras(self):
        with self.lock:
            for camera_id in list(self.active_cameras.keys()):
                try:
                    self.active_cameras[camera_id]['cap'].release()
                except Exception as e:
                    logger.error(f"Erro ao liberar camera {camera_id}: {str(e)}")
            self.active_cameras.clear()
            logger.info("Todas as câmeras foram liberadas")
    def capture(self, camera_id=0, max_size=WEBCAM_MAX_SIZE, quality=None, format=WEBCAM_FORMAT):
        with self.lock:
            try:
                if isinstance(camera_id, str) and camera_id.isdigit():
                    camera_id = int(camera_id)
                if quality is None:
                    quality = WEBCAM_QUALITY
                else:
                    quality = max(10, min(95, quality))
                cap = self._get_camera(camera_id)
                if not cap:
                    logger.error(f"Failed to open camera {camera_id}")
                    return None
                self.active_cameras[camera_id]['last_used'] = time.time()
                self.active_cameras[camera_id]['frame_count'] += 1
                for _ in range(2):  # Descartar frames antigos do buffer
                    cap.grab()
                ret, frame = cap.read()
                if not ret or frame is None:
                    logger.error(f"Failed to capture image from camera {camera_id}")
                    self.release_camera(camera_id)  # Liberar câmera problemática
                    return None
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame_rgb)
                logger.debug(f"Image captured from camera {camera_id}: {image.width}x{image.height}")
                if image.width > max_size or image.height > max_size:
                    image = resize_image(image, max_size)
                if format.upper() == "JPEG" and image.mode != 'RGB':
                    image = convert_to_format(image, format)
                image_bytes = optimize_image(image, format, quality)
                if not image_bytes:
                    logger.error("Failed to optimize webcam image")
                    return None
                return image_bytes
            except Exception as e:
                logger.error(f"Error capturing from webcam {camera_id}: {str(e)}")
                try:
                    self.release_camera(camera_id)
                except:
                    pass
                return None
    def __del__(self):
        self.release_all_cameras()

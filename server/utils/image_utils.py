# server/utils/image_utils.py
import base64
import io
from PIL import Image, ImageTk
import logging
logger = logging.getLogger("server.image_utils")
def decode_base64_image(base64_str):
    try:
        image_data = base64.b64decode(base64_str)
        image = Image.open(io.BytesIO(image_data))
        return image
    except Exception as e:
        logger.error(f"Erro ao decodificar imagem base64: {str(e)}")
        return None
def image_to_base64(image, format="JPEG", quality=75):
    try:
        buffered = io.BytesIO()
        image.save(buffered, format=format, quality=quality)
        img_str = base64.b64encode(buffered.getvalue())
        return img_str.decode('utf-8')
    except Exception as e:
        logger.error(f"Erro ao converter imagem para base64: {str(e)}")
        return None
def resize_image(image, max_width=None, max_height=None, keep_aspect_ratio=True):
    try:
        if not max_width and not max_height:
            return image
        width, height = image.size
        if keep_aspect_ratio:
            if max_width and max_height:
                if width / height > max_width / max_height:
                    new_width = max_width
                    new_height = int(height * (max_width / width))
                else:
                    new_height = max_height
                    new_width = int(width * (max_height / height))
            elif max_width:
                new_width = max_width
                new_height = int(height * (max_width / width))
            else:
                new_height = max_height
                new_width = int(width * (max_height / height))
        else:
            new_width = max_width if max_width else width
            new_height = max_height if max_height else height
        return image.resize((new_width, new_height), Image.LANCZOS)
    except Exception as e:
        logger.error(f"Erro ao redimensionar imagem: {str(e)}")
        try:
            return image.resize((new_width, new_height), Image.BILINEAR)
        except:
            return image
def create_photo_image(image):
    try:
        return ImageTk.PhotoImage(image)
    except Exception as e:
        logger.error(f"Erro ao criar PhotoImage: {str(e)}")
        return None
def validate_image_format(image_data):
    try:
        if not image_data or len(image_data) < 4:
            return False
        is_jpeg = image_data[0] == 0xFF and image_data[1] == 0xD8
        is_png = (image_data[0] == 0x89 and 
                  image_data[1] == 0x50 and 
                  image_data[2] == 0x4E and 
                  image_data[3] == 0x47)
        return is_jpeg or is_png
    except Exception as e:
        logger.error(f"Erro ao validar formato da imagem: {str(e)}")
        return False
def optimize_image(image, format="JPEG", quality=75, max_size=1024):
    try:
        width, height = image.size
        if width > max_size or height > max_size:
            image = resize_image(image, max_size, max_size)
        if format.upper() == "JPEG" and image.mode == "RGBA":
            image = image.convert("RGB")
        buffered = io.BytesIO()
        image.save(buffered, format=format, quality=quality, optimize=True)
        final_size = len(buffered.getvalue())
        logger.debug(f"Tamanho da imagem otimizada: {final_size/1024:.2f}KB")
        return Image.open(buffered)
    except Exception as e:
        logger.error(f"Erro ao otimizar imagem: {str(e)}")
        return image

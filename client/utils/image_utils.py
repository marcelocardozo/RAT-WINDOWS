# client/utils/image_utils.py
import io
from PIL import Image
import logging
logger = logging.getLogger("client.image_utils")
def resize_image(image, max_size, keep_aspect_ratio=True):
    try:
        width, height = image.size
        if not max_size or (width <= max_size and height <= max_size):
            return image
        if keep_aspect_ratio:
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))
        else:
            new_width = min(width, max_size)
            new_height = min(height, max_size)
        try:
            return image.resize((new_width, new_height), Image.LANCZOS)
        except:
            return image.resize((new_width, new_height), Image.BILINEAR)
    except Exception as e:
        logger.error(f"Erro ao redimensionar imagem: {str(e)}")
        return image
def convert_to_format(image, format="JPEG"):
    try:
        if format.upper() == "JPEG" and image.mode in ('RGBA', 'LA'):
            return image.convert('RGB')
        return image
    except Exception as e:
        logger.error(f"Erro ao converter formato da imagem: {str(e)}")
        return image
def optimize_image(image, format="JPEG", quality=75):
    try:
        buffer = io.BytesIO()
        image.save(buffer, format=format, quality=quality, optimize=True)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        logger.error(f"Erro ao otimizar imagem: {str(e)}")
        try:
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)
            return buffer.getvalue()
        except:
            return None
def validate_image_data(image_data):
    if not image_data or len(image_data) < 4:
        return False
    is_jpeg = image_data[0] == 0xFF and image_data[1] == 0xD8
    is_png = (image_data[0] == 0x89 and 
              image_data[1] == 0x50 and 
              image_data[2] == 0x4E and 
              image_data[3] == 0x47)
    return is_jpeg or is_png

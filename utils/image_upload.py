import io
import logging

from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

logging.basicConfig(level=logging.INFO)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
MAX_DIMENSION = 1920


class ImageValidationError(Exception):
    pass


def process_image(file_bytes: bytes, content_type: str) -> tuple[bytes, str]:
    """Validate, resize, and strip EXIF from an uploaded image.

    Returns processed bytes and the output content type (always image/jpeg or image/png or image/webp).
    """
    if content_type not in ALLOWED_TYPES:
        raise ImageValidationError(
            f"Unsupported image type: {content_type}. "
            f"Allowed: JPEG, PNG, WebP, HEIC"
        )

    img = Image.open(io.BytesIO(file_bytes))

    # Resize if too large
    width, height = img.size
    if max(width, height) > MAX_DIMENSION:
        ratio = MAX_DIMENSION / max(width, height)
        new_size = (int(width * ratio), int(height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
        logging.info(
            f"Resized image from {width}x{height} to {new_size[0]}x{new_size[1]}"
        )

    # Strip EXIF by copying pixel data to a new image
    clean_img = Image.new(img.mode, img.size)
    clean_img.putdata(list(img.getdata()))

    # Convert HEIC/HEIF to JPEG; otherwise keep original format
    if content_type in {"image/heic", "image/heif"}:
        output_format = "JPEG"
        output_content_type = "image/jpeg"
    elif content_type == "image/png":
        output_format = "PNG"
        output_content_type = "image/png"
    elif content_type == "image/webp":
        output_format = "WEBP"
        output_content_type = "image/webp"
    else:
        output_format = "JPEG"
        output_content_type = "image/jpeg"

    buf = io.BytesIO()
    clean_img.save(buf, format=output_format, quality=85)
    return buf.getvalue(), output_content_type

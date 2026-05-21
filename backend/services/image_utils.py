import base64
import io
from typing import Tuple

from PIL import Image


def decode_sketch(data_url: str) -> Image.Image:
    """Decode a data URL or raw base64 PNG/JPEG into RGB PIL Image."""
    if "," in data_url:
        _, payload = data_url.split(",", 1)
    else:
        payload = data_url
    raw = base64.b64decode(payload)
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    return image


def prepare_control_sketch(image: Image.Image) -> Image.Image:
    """
    ControlNet Scribble expects clear line art (white strokes on black).
    User draws black on white — invert + boost contrast for layout fidelity.
    """
    from PIL import ImageOps

    gray = ImageOps.autocontrast(image.convert("L"), cutoff=2)
    inverted = ImageOps.invert(gray)
    return inverted.convert("RGB")


def resize_cover(image: Image.Image, width: int, height: int) -> Image.Image:
    """Resize with center crop to exact dimensions (stable for ControlNet)."""
    target_ratio = width / height
    src_w, src_h = image.size
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        new_h = height
        new_w = int(src_w * (height / src_h))
    else:
        new_w = width
        new_h = int(src_h * (width / src_w))

    resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - width) // 2
    top = (new_h - height) // 2
    return resized.crop((left, top, left + width, top + height))


def image_to_jpeg_bytes(image: Image.Image, quality: int = 85) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def image_to_data_url(image: Image.Image, quality: int = 85) -> str:
    payload = base64.b64encode(image_to_jpeg_bytes(image, quality)).decode("ascii")
    return f"data:image/jpeg;base64,{payload}"

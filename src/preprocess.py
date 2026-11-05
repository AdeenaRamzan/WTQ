"""Light image preprocessing: EXIF-rotation fix, sensible resize, mild contrast.

We deliberately keep this gentle - aggressive processing can destroy faint
printed digits. The goal is only to help the model read fine print on tilted
or low-resolution photos.
"""
from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageOps

from . import config

log = config.get_logger("preprocess")


def load_bill_image(path: str | Path) -> tuple[bytes, str]:
    """Return (jpeg_bytes, mime_type) ready to send to the model."""
    path = Path(path)
    img = Image.open(path)

    # Respect EXIF orientation (phones store rotation in metadata).
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")

    long_edge = max(img.size)
    if long_edge < config.MIN_LONG_EDGE_PX:
        scale = config.MIN_LONG_EDGE_PX / long_edge
        new_size = (round(img.width * scale), round(img.height * scale))
        img = img.resize(new_size, Image.LANCZOS)
        log.info("%s upscaled %s -> %s", path.name, long_edge, max(new_size))
    elif long_edge > config.MAX_LONG_EDGE_PX:
        scale = config.MAX_LONG_EDGE_PX / long_edge
        new_size = (round(img.width * scale), round(img.height * scale))
        img = img.resize(new_size, Image.LANCZOS)
        log.info("%s downscaled %s -> %s", path.name, long_edge, max(new_size))

    # Mild contrast stretch; cutoff keeps it from clipping real ink.
    img = ImageOps.autocontrast(img, cutoff=1)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue(), "image/jpeg"

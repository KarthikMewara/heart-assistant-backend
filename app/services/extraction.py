import io
from pathlib import Path

import pymupdf as fitz
import pytesseract
from PIL import Image

from app.config import settings

if settings.tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


def extract_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        with fitz.open(path) as pdf:
            text = "\n".join(page.get_text() for page in pdf)
            if len(text.strip()) > 50:          # a typed PDF has real text
                return text
            pages = [Image.open(io.BytesIO(p.get_pixmap(dpi=300).tobytes("png"))) for p in pdf]
            return "\n".join(_ocr(img) for img in pages)   # a scanned PDF needs OCR
    return _ocr(Image.open(path))


def _ocr(image: Image.Image) -> str:
    return pytesseract.image_to_string(image.convert("L"))   # greyscale improves accuracy
"""Re-encode every upload: strips EXIF/GPS metadata (privacy), fixes rotation, caps size, saves as WebP."""
import io
import uuid
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

MAX_SIDE = 2000

def clean_image(uploaded):
    uploaded.seek(0)
    img = Image.open(uploaded)
    img = ImageOps.exif_transpose(img)       # apply the phone's rotation before dropping metadata
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, "WEBP", quality=85, method=4)   # nothing but pixels is written (no exif=...)
    return ContentFile(buf.getvalue(), name=uuid.uuid4().hex + ".webp")

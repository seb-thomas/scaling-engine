"""
Small WebP thumbnails of book covers.

Covers are stored at full size (often 100-200KB) but shown 64-192 CSS px
wide, so pages serve these instead via srcset. Thumbnails live beside the
media tree and are derived from the cover's path, so no model field is
needed:

    covers/front-row/author-title.jpg  ->  thumbs/front-row/author-title-160.webp
                                           thumbs/front-row/author-title-400.webp
"""

import io
import logging
import os
from typing import Dict, List

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# Rendered widths are 64px (lists), 128px (featured) and 192px (book page).
# 160w serves lists up to 2.5x DPR, 240w lists at 3x and featured at ~2x,
# 400w the book page at 2x
THUMB_WIDTHS = (160, 240, 400)
WEBP_QUALITY = 80


def thumbnail_names(cover_name: str) -> Dict[int, str]:
    """Storage names of a cover's thumbnails, keyed by width."""
    rel = cover_name[len("covers/"):] if cover_name.startswith("covers/") else cover_name
    stem = os.path.splitext(rel)[0]
    return {w: f"thumbs/{stem}-{w}.webp" for w in THUMB_WIDTHS}


def _is_fresh(cover_name: str, thumb_name: str) -> bool:
    if not default_storage.exists(thumb_name):
        return False
    try:
        return os.path.getmtime(default_storage.path(thumb_name)) >= os.path.getmtime(
            default_storage.path(cover_name)
        )
    except (NotImplementedError, OSError):
        return True


def generate_thumbnails(book, force: bool = False) -> int:
    """
    Write any missing or stale thumbnails for book's cover.

    Returns how many were written. Never raises: a bad image is logged and
    the site falls back to the original cover.
    """
    cover_name = book.cover_image.name if book.cover_image else ""
    if not cover_name or not default_storage.exists(cover_name):
        return 0

    todo = {
        w: name for w, name in thumbnail_names(cover_name).items()
        if force or not _is_fresh(cover_name, name)
    }
    if not todo:
        return 0

    try:
        with default_storage.open(cover_name, "rb") as f:
            img = ImageOps.exif_transpose(Image.open(f))
            img.load()
        img = img.convert("RGBA" if img.mode in ("RGBA", "LA", "P") else "RGB")

        for width, name in todo.items():
            thumb = img.copy()
            if thumb.width > width:
                thumb = thumb.resize(
                    (width, round(thumb.height * width / thumb.width)), Image.LANCZOS
                )
            buf = io.BytesIO()
            thumb.save(buf, "WEBP", quality=WEBP_QUALITY, method=6)
            if default_storage.exists(name):
                default_storage.delete(name)
            default_storage.save(name, ContentFile(buf.getvalue()))
        return len(todo)
    except Exception:
        logger.exception("Could not make thumbnails for %s", cover_name)
        return 0


def thumbnail_urls(book) -> List[Dict]:
    """[{width, url}] for thumbnails that exist, smallest first.

    URLs carry the file's mtime so a replaced cover isn't hidden behind
    nginx's 30-day immutable cache on /media/.
    """
    cover_name = book.cover_image.name if book.cover_image else ""
    if not cover_name:
        return []
    out = []
    for width, name in sorted(thumbnail_names(cover_name).items()):
        try:
            version = int(os.path.getmtime(default_storage.path(name)))
        except (NotImplementedError, OSError):
            continue
        out.append({"width": width, "url": f"{default_storage.url(name)}?v={version}"})
    return out

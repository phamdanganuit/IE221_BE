"""
Centralized storage utilities.
Works with Cloudinary (production) or local FileSystemStorage (dev).
"""
import uuid
import logging
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)


def get_storage():
    """Return the active Django storage backend (Cloudinary or local)."""
    return default_storage


def upload_file(file_obj, folder="media", prefix="file"):
    """
    Upload a single file and return its public URL.

    Args:
        file_obj: Django UploadedFile / InMemoryUploadedFile
        folder:   sub-folder inside the storage (e.g. "avatars", "products", "reviews")
        prefix:   prefix for the generated filename

    Returns:
        str – public URL of the uploaded file, or None on failure
    """
    try:
        ext = file_obj.name.rsplit(".", 1)[-1] if "." in file_obj.name else "jpg"
        filename = f"{folder}/{prefix}_{uuid.uuid4().hex[:8]}.{ext}"

        storage = get_storage()
        saved_path = storage.save(filename, file_obj)
        if not saved_path:
            return None

        url = storage.url(saved_path)
        # Ensure absolute URL or relative /media/ path
        if url and (url.startswith("http") or url.startswith("/")):
            return url
        return f"/media/{url.lstrip('/')}" if url else None
    except Exception as exc:
        logger.error("upload_file failed: %s", exc, exc_info=True)
        return None


def delete_file(file_url_or_path):
    """
    Best-effort delete of a previously uploaded file.
    Accepts either a full URL or a storage-relative path.
    """
    if not file_url_or_path:
        return
    try:
        storage = get_storage()
        path = file_url_or_path
        # Strip leading /media/
        if path.startswith("/media/"):
            path = path[len("/media/"):]
        # For full Cloudinary / other URLs, default_storage.delete usually handles it
        if storage.exists(path):
            storage.delete(path)
    except Exception as exc:
        logger.debug("delete_file skipped: %s", exc)

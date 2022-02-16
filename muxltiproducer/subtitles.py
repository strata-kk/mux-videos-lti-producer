import logging
import typing as t
import uuid
from datetime import timedelta

from django.core.files.storage import DefaultStorage
from django.utils.timezone import now

MEDIA_FOLDER = "mux/subtitles"

logger = logging.getLogger(__file__)


def save(file: t.TextIO) -> None:
    """
    Save the file in the right media folder with a random name.

    Return: url of the saved file (str)
    """
    storage = DefaultStorage()
    filename = f"{MEDIA_FOLDER}/{uuid.uuid4()}"
    storage.save(filename, file)
    return storage.url(filename)


def delete_expired():
    """
    Delete uploaded subtitle files older than one hour.
    """
    storage = DefaultStorage()
    _folders, files = storage.listdir(MEDIA_FOLDER)
    for filename in files:
        path = f"{MEDIA_FOLDER}/{filename}"
        created_at = storage.get_created_time(path)
        if created_at < now() - timedelta(hours=1):
            storage.delete(path)
            logger.info("Deleted subtitle file: %s", path)

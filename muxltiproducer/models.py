import enum
import typing as t
from datetime import datetime, timedelta

from django.core.cache import caches
from django.db import models
from django.utils.timezone import now

from . import mux, openedx


class LtiContext(models.Model):
    """
    Information about the LTI context in which assets and upload urls are generated.
    """

    context_id = models.CharField(
        verbose_name="LTI context ID (aka: course ID)", max_length=512, unique=True
    )


# pylint: disable=too-few-public-methods
class AssetManager(models.Manager):
    def filter_visible(self, course_id: str):
        regex = openedx.course_access_limit_regex(course_id)
        return self.filter(lti_context__context_id__regex=regex) if regex else self


class Asset(models.Model):
    mux_id = models.CharField(verbose_name="Mux asset ID", max_length=255, unique=True)
    lti_context = models.ForeignKey(LtiContext, models.CASCADE)
    objects = AssetManager()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self._mux_properties = self.UNDEFINED

    @property
    def mux_properties(self) -> t.Optional["MuxAssetProperties"]:
        """
        Return the properties object built from Mux API.

        Return None if the asset does not exist on Mux.
        """
        if not hasattr(self, "_mux_properties"):
            # pylint: disable=attribute-defined-outside-init
            self._mux_properties = MuxAssetProperties.load(self.mux_id)
        return self._mux_properties


class MuxAssetProperties:
    @classmethod
    def load(cls, mux_id: str) -> t.Optional["MuxAssetProperties"]:
        """
        Load the corresponding asset from the Mux API.

        Return None if the object could not be found.

        Results are stored in the lti_apps cache with keys prefixed by
        "mux:assets:". Pass `no_cache=True` to bypass the cache.

        See docs: https://docs.mux.com/api-reference/video#operation/get-asset
        """
        data = cls.load_data(mux_id)
        return cls(data) if data else None

    @staticmethod
    def load_data(mux_id, no_cache=False) -> t.Optional[t.Dict[str, t.Any]]:
        absent = object()
        cache_key = f"mux:assets:{mux_id}"
        cache = caches["lti_apps"]
        data = cache.get(cache_key, absent)
        if data is absent or no_cache:
            data = mux.get_asset(mux_id)
            cache.set(cache_key, data)
        return data

    def __init__(self, data: t.Dict[str, t.Any]) -> None:
        self._data = data

    def update(self) -> "MuxAssetProperties":
        """
        Update from upstream Mux data.
        """
        data = self.load_data(self._data["id"], no_cache=True)
        if data:
            self._data = data
        return self

    @property
    def created_at(self) -> datetime:
        return datetime.fromtimestamp(self.created_at_timestamp)

    @property
    def created_at_timestamp(self) -> int:
        return int(self._data["created_at"])

    @property
    def playback_id(self) -> t.Optional[str]:
        return self.playback["id"] if self.playback else None

    @property
    def is_public(self) -> bool:
        return self.playback["policy"] == "public" if self.playback else False

    @property
    def playback(self) -> t.Optional[t.Dict[str, str]]:
        """
        Return the first playback property.

        The playback may be either public or private. If there is no playback
        then return None.
        """
        playback_ids = self._data.get("playback_ids")
        return playback_ids[0] if playback_ids else None

    @property
    def video_url(self) -> t.Optional[str]:
        if not self.playback_id:
            return None
        public_url = f"https://stream.mux.com/{self.playback_id}.m3u8"
        if self.is_public:
            return f"{public_url}?redundant_streams=true"
        return mux.sign_video_playback_url(public_url, self.playback_id)

    @property
    def poster_url(self) -> t.Optional[str]:
        if not self.playback_id:
            return None
        public_url = f"https://image.mux.com/{self.playback_id}/thumbnail.jpg"
        if self.is_public:
            return public_url
        return mux.sign_poster_playback_url(public_url, self.playback_id)

    @property
    def subtitle_tracks(self):
        return [track for track in self._data["tracks"] if track["type"] == "text"]

    @property
    def error_messages(self) -> t.List[str]:
        # Beware that for valid videos "errors" is actually "None"
        errors = self._data.get("errors") or {}
        return errors.get("messages", [])


# pylint: disable=too-few-public-methods
class UploadUrlManager(models.Manager):
    def filter_expired(self):
        """
        Limit selection to expired urls, based on the creation date and the upload url validity, plus some margin.
        """
        cutoff = now() - timedelta(seconds=mux.DIRECT_UPLOAD_VALIDITY_SECONDS + 10)
        return self.filter(created_at__lt=cutoff)


class UploadUrl(models.Model):
    @enum.unique
    class Statuses(enum.Enum):
        # https://docs.mux.com/api-reference/video#tag/direct-uploads
        WAITING = "waiting"
        CREATED = "asset_created"
        ERRORED = "errored"
        CANCELLED = "cancelled"
        TIMED_OUT = "timed_out"

    mux_id = models.CharField(
        verbose_name="Mux direct upload URL ID", max_length=255, unique=True
    )
    lti_context = models.ForeignKey(LtiContext, models.CASCADE)
    status = models.CharField(
        default=Statuses.WAITING.value,
        max_length=32,
        choices=[(s.value, s.name) for s in Statuses],
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    objects = UploadUrlManager()

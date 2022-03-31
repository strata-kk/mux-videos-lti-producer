import base64
import hashlib
import hmac
import re
import typing as t
from time import time

import jwt
import mux_python as mux
from mux_python.exceptions import NotFoundException
from django.conf import settings

DIRECT_UPLOAD_VALIDITY_SECONDS = getattr(
    settings,
    "MUX_UPLOAD_URL_VALIDITY_SECONDS",
    2 * 24 * 60 * 60,
)


def create_direct_upload(origin: str = "*") -> t.Dict[str, t.Any]:
    """
    Create a signed url for uploading assets.

    The url will be valid for a limited duration and usable only from a specific origin host.

    See API docs: https://docs.mux.com/guides/video/upload-files-directly#1-create-an-authenticated-mux-url

    Return:

        {
            "id": "...",
            "url": "https://...",
            ...
        }
    """
    signed_playback_enabled = getattr(settings, "MUX_ENABLE_SIGNED_PLAYBACK", True)
    playback_policy = (
        mux.PlaybackPolicy.SIGNED
        if signed_playback_enabled
        else mux.PlaybackPolicy.PUBLIC
    )
    create_asset_request = mux.CreateAssetRequest(playback_policy=[playback_policy])
    create_upload_request = mux.CreateUploadRequest(
        timeout=DIRECT_UPLOAD_VALIDITY_SECONDS,
        new_asset_settings=create_asset_request,
        cors_origin=origin,
    )
    response = get_uploads_client().create_direct_upload(create_upload_request)
    return response.to_dict()["data"]


def get_asset(mux_asset_id) -> t.Optional[t.Dict[str, t.Any]]:
    """
    Fetch an asset from the Mux API.

    Return None if the asset was not found.

    See docs: https://docs.mux.com/api-reference/video#operation/get-asset
    """
    try:
        asset = get_assets_client().get_asset(mux_asset_id)
    except NotFoundException:
        return None
    return asset.data.to_dict()


def get_assets_client() -> mux.AssetsApi:
    return mux.AssetsApi(_get_client())


def get_uploads_client() -> mux.DirectUploadsApi:
    return mux.DirectUploadsApi(_get_client())


def get_url_signing_key_client() -> mux.URLSigningKeysApi:
    return mux.URLSigningKeysApi(_get_client())


def _get_client() -> mux.ApiClient:
    configuration = mux.Configuration(
        username=settings.MUX_TOKEN_ID, password=settings.MUX_TOKEN_SECRET
    )
    return mux.ApiClient(configuration)


def sign_video_playback_url(public_url: str, playback_id: str) -> str:
    return sign_url(
        public_url,
        {
            "sub": playback_id,
            "aud": "v",
            "redundant_streams": True,
        },
    )


def sign_poster_playback_url(public_url: str, playback_id: str) -> str:
    return sign_url(
        public_url,
        {
            "sub": playback_id,
            "aud": "t",
        },
    )


def sign_url(public_url: str, params: t.Dict[str, t.Any]) -> str:
    """
    Return the signed url, with the right expiry parameters.

    The jwt token is appended to the url, just so: `&token=...`.

    Note that signed urls should not include any extra querystring parameters.

    https://docs.mux.com/guides/video/secure-video-playback
    """
    validity_seconds = getattr(
        settings,
        "MUX_SIGNED_URL_EXPIRY_SECONDS",
        7 * 24 * 60 * 60,
    )
    params.setdefault("exp", int(time()) + validity_seconds)

    signing_key_id = settings.MUX_SIGNING_KEY_ID
    private_key_base64 = settings.MUX_SIGNING_PRIVATE_KEY
    private_key = base64.b64decode(private_key_base64).decode()
    headers = {"kid": signing_key_id}
    token = jwt.encode(params, private_key, algorithm="RS256", headers=headers)
    return f"{public_url}?token={token}"


def verify_webhook_signature(sig: str, body: bytes):
    """
    Verify a webhook callback signature.

    https://docs.mux.com/guides/video/verify-webhook-signatures

    Example: 't=1646396487,v1=f609be479abf8951a541e48351662507e720824253220b8c3178c10828af6a1f'
    """
    match = re.match(r"t=(?P<timestamp>[0-9]+),v1=(?P<signature>[a-z0-9]+)$", sig)
    if not match:
        return False
    timestamp, signature = match.groups()
    reference = hmac.new(
        settings.MUX_WEBHOOK_SIGNING_SECRET.encode(),
        timestamp.encode() + b"." + body,
        hashlib.sha256,
    ).hexdigest()
    return reference == signature

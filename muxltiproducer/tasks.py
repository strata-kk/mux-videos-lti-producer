import logging

from huey import crontab
from huey.contrib.djhuey import db_periodic_task, task

from . import models, mux, subtitles

logger = logging.getLogger(__file__)


@db_periodic_task(crontab(minute=0, hour="*"))
def synchronize() -> None:
    """
    Synchronize data with Mux.

    This hourly asynchronous task updates the upload urls stored locally with
    Mux: - Waiting urls for which an asset has been created are updated -
    Expired urls are deleted - Upload urls which have been used are deleted

    In production, updating upload urls should be performed thanks to webhooks.
    In development this is more difficult. Thus, the 'mux_sync' management
    command should be run manually to update upload urls.
    """
    update_waiting_direct_uploads()
    delete_expired_direct_uploads()
    subtitles.delete_expired()


def update_waiting_direct_uploads() -> None:
    """
    Update direct upload status. When ready, create corresponding asset.

    This function performs all tasks in a synchronous manner.

    Note that this function should only be called from time to time. The "right"
    way to update upload urls is to receive web hook callbacks from Mux.
    """
    upload_url_waiting = models.UploadUrl.objects.filter(
        status=models.UploadUrl.Statuses.WAITING.value
    )
    upload_url_count = upload_url_waiting.count()

    for upload_url in upload_url_waiting:
        update_waiting_direct_upload.call_local(upload_url.mux_id)

    logger.info(
        "Updated %d upload urls in the '%s' state",
        upload_url_count,
        models.UploadUrl.Statuses.WAITING.value,
    )


@task()
def update_waiting_direct_upload(mux_id: int) -> None:
    """
    Update a single direct upload url.
    """
    try:
        direct_upload = models.UploadUrl.objects.get(
            mux_id=mux_id, status=models.UploadUrl.Statuses.WAITING.value
        )
    except models.UploadUrl.DoesNotExist:
        return

    mux_client = mux.get_uploads_client()
    updated = mux_client.get_direct_upload(mux_id).data

    if updated.status != models.UploadUrl.Statuses.CREATED.value:
        return

    # Create an asset, if necessary
    models.Asset.objects.get_or_create(
        mux_id=updated.asset_id, lti_context=direct_upload.lti_context
    )
    direct_upload.status = models.UploadUrl.Statuses.CREATED.value
    direct_upload.save()
    logger.info(
        "Upload url updated: mux_id=%s status=%s asset_id=%s",
        direct_upload.mux_id,
        direct_upload.status,
        updated.asset_id,
    )


def delete_expired_direct_uploads():
    """
    Delete upload urls which have passed their expiry date.
    """
    expired = models.UploadUrl.objects.filter_expired()
    logger.info(
        "Deleting expired upload urls: %d",
        expired.count(),
    )
    expired.delete()


@task()
def delete_mux_asset(mux_id: str) -> None:
    """
    Delete asset from Mux.
    """
    client = mux.get_assets_client()
    client.delete_asset(mux_id)

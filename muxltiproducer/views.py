import json

from django.conf import settings
from django.conf.global_settings import LANGUAGES
from django.http import Http404, HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from ltiproducer import ltiviews

from . import models, mux
from . import subtitles as mux_subtitles
from . import tasks

CAN_INSTRUCTORS_DELETE_ASSETS = getattr(
    settings,
    "MUX_CAN_INSTRUCTORS_DELETE_ASSETS",
    True,
)


@ltiviews.view
def launch(request: ltiviews.HttpLtiRequest) -> HttpResponse:
    mux_asset_id = request.lti_params.get("custom_video_id", "")
    mux_asset = None
    if mux_asset_id:
        try:
            mux_asset = models.Asset.objects.filter_visible(
                request.lti_params.context_id
            ).get(
                mux_id=mux_asset_id,
            )
        except models.Asset.DoesNotExist:
            pass
    return render(
        request,
        "muxltiproducer/watch.html",
        context={"asset": mux_asset},
    )


@ltiviews.view
@ltiviews.instructor_required
def edit_video(request: ltiviews.HttpLtiRequest) -> HttpResponse:
    assets = models.Asset.objects.filter_visible(
        request.lti_params.context_id
    ).order_by("-pk")

    return render(
        request,
        "muxltiproducer/edit.html",
        context={
            "assets": assets,
            "can_delete_assets": CAN_INSTRUCTORS_DELETE_ASSETS,
            "languages": LANGUAGES,
        },
    )


@ltiviews.view
@ltiviews.instructor_required
@require_POST
def delete_video(request: ltiviews.HttpLtiRequest, mux_id: str) -> HttpResponse:
    if not CAN_INSTRUCTORS_DELETE_ASSETS:
        return HttpResponseForbidden("Asset deletion is not allowed")
    mux_assets = models.Asset.objects.filter_visible(
        request.lti_params.context_id
    ).filter(mux_id=mux_id)
    for mux_asset in mux_assets:
        tasks.delete_mux_asset(mux_asset.mux_id)
    mux_assets.delete()
    return redirect("mux:edit", lti_session_id=request.lti_session_id)


@ltiviews.view
@ltiviews.instructor_required
@require_POST
def subtitles(request: ltiviews.HttpLtiRequest, mux_id: str) -> HttpResponse:
    """
    Upload subtitle file to Mux.

    https://docs.mux.com/api-reference/video#operation/create-asset-track
    """
    try:
        asset = models.Asset.objects.filter_visible(request.lti_params.context_id).get(
            mux_id=mux_id
        )
    except models.Asset.DoesNotExist as e:
        raise Http404 from e
    if not asset.mux_properties:
        raise Http404
    subtitles_file = request.FILES.get("file")
    if not subtitles_file:
        return HttpResponse("Missing file", status=400)

    # Save the subtitles file
    subtitles_file_url = mux_subtitles.save(subtitles_file)

    # Delete subtitles with the same language code
    # Note: do we really want to do that? Should we send a warning to the
    # end-user? Should we instead create a new track with a different name?
    language_code = request.POST.get("language", settings.LANGUAGE_CODE)
    mux_assets_client = mux.get_assets_client()
    # Update asset cache to fetch latest changes
    asset.mux_properties.update()
    for subtitle_track in asset.mux_properties.subtitle_tracks:
        if subtitle_track["language_code"] == language_code:
            mux_assets_client.delete_asset_track(mux_id, subtitle_track["id"])

    # Create new asset track
    mux_assets_client.create_asset_track(
        mux_id,
        {
            "url": request.build_absolute_uri(subtitles_file_url),
            "type": "text",
            "text_type": "subtitles",
            "language_code": language_code,
        },
    )

    # Update asset cache one more time to reflect changes in the frontend
    asset.mux_properties.update()

    return redirect("mux:edit", lti_session_id=request.lti_session_id)


@ltiviews.view
@ltiviews.instructor_required
@require_POST
def delete_subtitles(
    request: ltiviews.HttpLtiRequest, mux_id: str, track_id: str
) -> HttpResponse:
    try:
        asset = models.Asset.objects.filter_visible(request.lti_params.context_id).get(
            mux_id=mux_id
        )
    except models.Asset.DoesNotExist as e:
        raise Http404 from e
    mux_assets_client = mux.get_assets_client()
    try:
        mux_assets_client.delete_asset_track(mux_id, track_id)
    except mux.NotFoundException:
        pass
    asset.mux_properties.update()
    return redirect("mux:edit", lti_session_id=request.lti_session_id)


@require_http_methods(["GET", "POST"])
@ltiviews.view
@ltiviews.instructor_required
def uploads(request: ltiviews.HttpLtiRequest) -> HttpResponse:
    """
    Generate a URL for direct upload of assets.
    """
    if request.method == "GET":
        mux_id = request.GET.get("id")
        lti_context = get_object_or_404(
            models.LtiContext.objects, context_id=request.lti_params.context_id
        )
        direct_upload = get_object_or_404(
            models.UploadUrl,
            mux_id=mux_id,
            lti_context=lti_context,
        )
        return JsonResponse(
            {"id": direct_upload.mux_id, "status": direct_upload.status}
        )

    # Create url on POST
    scheme = "https" if request.is_secure() else "http"
    direct_upload_data = mux.create_direct_upload(
        origin=f"{scheme}://{request.META['HTTP_HOST']}"
    )
    lti_context, _created = models.LtiContext.objects.get_or_create(
        context_id=request.lti_params.context_id
    )
    models.UploadUrl.objects.create(
        mux_id=direct_upload_data["id"], lti_context=lti_context
    )
    return JsonResponse(
        {"url": direct_upload_data["url"], "id": direct_upload_data["id"]}
    )


@csrf_exempt
@require_POST
def callback(request: ltiviews.HttpLtiRequest):
    """
    Callback webhook used by Mux to tell us about asset changes.

    https://docs.mux.com/guides/video/listen-for-webhooks
    """
    signature = request.headers.get("Mux-Signature", "")
    if not mux.verify_webhook_signature(signature, request.body):
        return HttpResponseForbidden("Invalid Signature")

    data = json.loads(request.body)
    if data["type"] == "video.asset.ready":
        tasks.update_waiting_direct_upload(data["data"]["upload_id"])

    return HttpResponse("")

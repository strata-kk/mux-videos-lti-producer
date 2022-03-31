from django.urls import path

from . import views

app_name = "mux"
urlpatterns = [
    path(
        "launch/<str:lti_session_id>",
        views.launch,
        name="launch",
    ),
    path(
        "edit/<str:lti_session_id>",
        views.edit_video,
        name="edit",
    ),
    path(
        "delete/<str:lti_session_id>/<str:mux_id>",
        views.delete_video,
        name="delete",
    ),
    path(
        "subtitles/<str:lti_session_id>/<str:mux_id>",
        views.subtitles,
        name="subtitles",
    ),
    path(
        "subtitles/<str:lti_session_id>/<str:mux_id>/<str:track_id>",
        views.delete_subtitles,
        name="delete_subtitles",
    ),
    path(
        "uploads/<str:lti_session_id>",
        views.uploads,
        name="uploads",
    ),
    path(
        "callback",
        views.callback,
        name="callback",
    ),
]

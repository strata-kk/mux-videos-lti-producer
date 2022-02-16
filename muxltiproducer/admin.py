from django.contrib import admin

from . import models


@admin.register(models.LtiContext)
class LtiContextAdmin(admin.ModelAdmin):
    list_display = ("id", "context_id")


@admin.register(models.Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("id", "mux_id")


@admin.register(models.UploadUrl)
class UploadUrlAdmin(admin.ModelAdmin):
    list_display = ("id", "mux_id", "created_at", "status")

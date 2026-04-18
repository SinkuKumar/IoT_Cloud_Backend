from django.contrib import admin

from .models import Device


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "id", "device_id", "name", "project",
        "status", "last_seen", "created_at",
    )
    list_filter = ("status",)
    search_fields = ("device_id", "name", "project__name", "project__owner__email")
    raw_id_fields = ("project",)
    readonly_fields = ("created_at", "updated_at", "last_seen")
    ordering = ("-created_at",)

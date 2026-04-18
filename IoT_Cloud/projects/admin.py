from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "owner__email", "owner__username")
    raw_id_fields = ("owner",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

from django.contrib import admin

from .models import ActionLog, DoctorProfile


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "phone",
        "specialization",
        "role",
        "status",
        "is_active",
        "created_at",
    )
    list_display_links = (
        "id",
        "full_name",
    )
    search_fields = (
        "full_name",
        "phone",
        "specialization",
        "user__username",
        "user__first_name",
        "user__last_name",
    )
    list_filter = (
        "role",
        "status",
        "is_active",
        "created_at",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "action_type",
        "service_request",
        "danger_report",
        "doctor",
        "old_status",
        "new_status",
        "created_at",
    )
    list_display_links = (
        "id",
        "action_type",
    )
    search_fields = (
        "description",
        "user__username",
        "doctor__full_name",
        "service_request__client__full_name",
        "danger_report__client__full_name",
    )
    list_filter = (
        "action_type",
        "created_at",
    )
    readonly_fields = (
        "created_at",
    )
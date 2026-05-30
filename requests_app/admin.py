from django.contrib import admin
from .models import ServiceRequest, DangerReport


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "client",
        "animal",
        "service_type",
        "status",
        "created_at",
    )

    list_display_links = (
        "id",
        "client",
    )

    search_fields = (
        "client__full_name",
        "client__phone",
        "animal__name",
        "problem_description",
        "address",
    )

    list_filter = (
        "service_type",
        "status",
        "created_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Mijoz va hayvon", {
            "fields": (
                "client",
                "animal",
            )
        }),
        ("Xizmat ma’lumotlari", {
            "fields": (
                "service_type",
                "problem_description",
                "status",
            )
        }),
        ("Manzil va lokatsiya", {
            "fields": (
                "address",
                "latitude",
                "longitude",
            )
        }),
        ("Administrator", {
            "fields": (
                "admin_comment",
            )
        }),
        ("Vaqt ma’lumotlari", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )


@admin.register(DangerReport)
class DangerReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "danger_type",
        "client",
        "phone",
        "status",
        "created_at",
    )

    list_display_links = (
        "id",
        "danger_type",
    )

    search_fields = (
        "client__full_name",
        "client__phone",
        "phone",
        "description",
        "address",
    )

    list_filter = (
        "danger_type",
        "status",
        "created_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Xabar yuboruvchi", {
            "fields": (
                "client",
                "phone",
            )
        }),
        ("Xavfli holat", {
            "fields": (
                "danger_type",
                "description",
                "status",
            )
        }),
        ("Manzil va lokatsiya", {
            "fields": (
                "address",
                "latitude",
                "longitude",
            )
        }),
        ("Administrator", {
            "fields": (
                "admin_comment",
            )
        }),
        ("Vaqt ma’lumotlari", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )
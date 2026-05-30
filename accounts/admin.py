from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "phone",
        "telegram_id",
        "telegram_username",
        "created_at",
    )

    list_display_links = (
        "id",
        "full_name",
    )

    search_fields = (
        "full_name",
        "phone",
        "telegram_id",
        "telegram_username",
    )

    list_filter = (
        "created_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Asosiy ma’lumotlar", {
            "fields": (
                "full_name",
                "phone",
                "address",
            )
        }),
        ("Telegram ma’lumotlari", {
            "fields": (
                "telegram_id",
                "telegram_username",
            )
        }),
        ("Vaqt ma’lumotlari", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )
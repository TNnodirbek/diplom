from django.contrib import admin
from .models import Animal


@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "animal_type",
        "breed",
        "age",
        "gender",
        "client",
        "created_at",
    )

    list_display_links = (
        "id",
        "name",
    )

    search_fields = (
        "name",
        "breed",
        "client__full_name",
        "client__phone",
    )

    list_filter = (
        "animal_type",
        "gender",
        "created_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Mijoz", {
            "fields": (
                "client",
            )
        }),
        ("Hayvon ma’lumotlari", {
            "fields": (
                "name",
                "animal_type",
                "breed",
                "age",
                "gender",
            )
        }),
        ("Kasallik belgilari", {
            "fields": (
                "symptoms",
            )
        }),
        ("Vaqt ma’lumotlari", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )
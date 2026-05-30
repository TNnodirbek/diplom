import uuid
from django.db import models


def generate_client_code():
    return f"CL-{uuid.uuid4().hex[:8].upper()}"


class Client(models.Model):
    """
    Telegram bot yoki administrator orqali murojaat qilgan mijoz.
    client_code - bot ichida va dashboardda qidirish uchun shaxsiy ID.
    """

    client_code = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        editable=False,
        verbose_name="Mijoz ID"
    )

    full_name = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        verbose_name="F.I.Sh"
    )

    phone = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        verbose_name="Telefon raqam"
    )

    telegram_id = models.BigIntegerField(
        unique=True,
        null=True,
        blank=True,
        verbose_name="Telegram ID"
    )

    telegram_username = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Telegram username"
    )

    address = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Manzil"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaratilgan vaqt"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Yangilangan vaqt"
    )

    class Meta:
        verbose_name = "Mijoz"
        verbose_name_plural = "Mijozlar"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.client_code:
            code = generate_client_code()
            while Client.objects.filter(client_code=code).exists():
                code = generate_client_code()
            self.client_code = code

        super().save(*args, **kwargs)

    def __str__(self):
        name = self.full_name if self.full_name else "Noma’lum mijoz"
        code = self.client_code if self.client_code else "ID yo‘q"
        return f"{code} - {name}"
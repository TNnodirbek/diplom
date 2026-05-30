import uuid
from django.db import models


def generate_animal_code():
    return f"AN-{uuid.uuid4().hex[:8].upper()}"


class Animal(models.Model):
    """
    Mijozga tegishli hayvon.
    Bitta mijozda bir nechta hayvon bo‘lishi mumkin.
    """

    ANIMAL_TYPE_CHOICES = [
        ("dog", "It"),
        ("cat", "Mushuk"),
        ("cow", "Mol"),
        ("horse", "Ot"),
        ("sheep", "Qo‘y"),
        ("goat", "Echki"),
        ("bird", "Qush / Parranda"),
        ("other", "Boshqa"),
    ]

    GENDER_CHOICES = [
        ("male", "Erkak"),
        ("female", "Urg‘ochi"),
        ("unknown", "Noma’lum"),
    ]

    animal_code = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        editable=False,
        verbose_name="Hayvon ID"
    )

    client = models.ForeignKey(
        "accounts.Client",
        on_delete=models.CASCADE,
        related_name="animals",
        verbose_name="Mijoz"
    )

    name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Hayvon nomi"
    )

    animal_type = models.CharField(
        max_length=30,
        choices=ANIMAL_TYPE_CHOICES,
        default="other",
        verbose_name="Hayvon turi"
    )

    breed = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Zoti"
    )

    age = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Yoshi"
    )

    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        default="unknown",
        verbose_name="Jinsi"
    )

    symptoms = models.TextField(
        null=True,
        blank=True,
        verbose_name="Kasallik belgilari"
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
        verbose_name = "Hayvon"
        verbose_name_plural = "Hayvonlar"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.animal_code:
            code = generate_animal_code()
            while Animal.objects.filter(animal_code=code).exists():
                code = generate_animal_code()
            self.animal_code = code

        super().save(*args, **kwargs)

    def __str__(self):
        animal_name = self.name if self.name else self.get_animal_type_display()
        code = self.animal_code if self.animal_code else "ID yo‘q"
        return f"{code} - {animal_name}"
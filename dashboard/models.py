from django.conf import settings
from django.db import models


class DoctorProfile(models.Model):
    """
    Administrator tomonidan arizalar biriktiriladigan veterinar yoki mas’ul xodim profili.
    """

    ROLE_CHIEF_VET = "chief_vet"
    ROLE_VET = "vet"
    ROLE_RESPONSIBLE = "responsible"
    ROLE_ASSISTANT = "assistant"

    ROLE_CHOICES = [
        (ROLE_CHIEF_VET, "Bosh veterinar"),
        (ROLE_VET, "Veterinar"),
        (ROLE_RESPONSIBLE, "Mas’ul xodim"),
        (ROLE_ASSISTANT, "Yordamchi xodim"),
    ]

    STATUS_FREE = "free"
    STATUS_BUSY = "busy"
    STATUS_ON_SERVICE = "on_service"
    STATUS_IN_CLINIC = "in_clinic"
    STATUS_INACTIVE = "inactive"

    STATUS_CHOICES = [
        (STATUS_FREE, "Bo‘sh"),
        (STATUS_BUSY, "Band"),
        (STATUS_ON_SERVICE, "Chaqiruvda"),
        (STATUS_IN_CLINIC, "Klinikada"),
        (STATUS_INACTIVE, "Faol emas"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_profile",
        verbose_name="Foydalanuvchi",
    )
    full_name = models.CharField(
        max_length=150,
        verbose_name="F.I.Sh",
    )
    phone = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name="Telefon raqam",
    )
    specialization = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Mutaxassislik",
    )
    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default=ROLE_VET,
        verbose_name="Lavozim",
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_FREE,
        verbose_name="Holati",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Faol",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaratilgan vaqt",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Yangilangan vaqt",
    )

    class Meta:
        verbose_name = "Veterinar profili"
        verbose_name_plural = "Veterinar profillari"
        ordering = ["full_name"]

    def refresh_status(self):
        """
        Veterinar statusini unga biriktirilgan faol arizalarga qarab avtomatik yangilaydi.
        """

        if not self.is_active:
            new_status = self.STATUS_INACTIVE
        else:
            active_danger_report_exists = self.assigned_danger_reports.exclude(
                status__in=["completed", "rejected"]
            ).exists()

            active_vet_call_exists = self.assigned_service_requests.filter(
                service_type="vet_call"
            ).exclude(
                status__in=["completed", "cancelled"]
            ).exists()

            active_clinic_request_exists = self.assigned_service_requests.filter(
                service_type="clinic"
            ).exclude(
                status__in=["completed", "cancelled"]
            ).exists()

            if active_danger_report_exists:
                new_status = self.STATUS_BUSY
            elif active_vet_call_exists:
                new_status = self.STATUS_ON_SERVICE
            elif active_clinic_request_exists:
                new_status = self.STATUS_IN_CLINIC
            else:
                new_status = self.STATUS_FREE

        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=["status", "updated_at"])

    def __str__(self):
        return f"{self.full_name} — {self.get_status_display()}"


class ActionLog(models.Model):
    """
    Ariza statusi o‘zgarishi, veterinar biriktirish, izoh va yakunlash harakatlari tarixi.
    """

    ACTION_CREATED = "created"
    ACTION_STATUS_CHANGED = "status_changed"
    ACTION_ASSIGNED = "assigned"
    ACTION_COMMENT_ADDED = "comment_added"
    ACTION_COMPLETED = "completed"
    ACTION_CANCELLED = "cancelled"

    ACTION_TYPE_CHOICES = [
        (ACTION_CREATED, "Yaratildi"),
        (ACTION_STATUS_CHANGED, "Status o‘zgartirildi"),
        (ACTION_ASSIGNED, "Mas’ul biriktirildi"),
        (ACTION_COMMENT_ADDED, "Izoh qo‘shildi"),
        (ACTION_COMPLETED, "Yakunlandi"),
        (ACTION_CANCELLED, "Bekor qilindi"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="dashboard_action_logs",
        verbose_name="Harakatni bajargan foydalanuvchi",
    )
    service_request = models.ForeignKey(
        "requests_app.ServiceRequest",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="action_logs",
        verbose_name="Xizmat arizasi",
    )
    danger_report = models.ForeignKey(
        "requests_app.DangerReport",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="action_logs",
        verbose_name="Xavfli holat xabari",
    )
    doctor = models.ForeignKey(
        "dashboard.DoctorProfile",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="action_logs",
        verbose_name="Biriktirilgan xodim",
    )
    action_type = models.CharField(
        max_length=30,
        choices=ACTION_TYPE_CHOICES,
        verbose_name="Harakat turi",
    )
    old_status = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Oldingi status",
    )
    new_status = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Yangi status",
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Izoh",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaratilgan vaqt",
    )

    class Meta:
        verbose_name = "Harakat tarixi"
        verbose_name_plural = "Harakatlar tarixi"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_action_type_display()} — {self.created_at.strftime('%d.%m.%Y %H:%M')}"
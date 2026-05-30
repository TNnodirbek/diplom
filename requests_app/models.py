from django.db import models
from django.utils import timezone


class ServiceRequest(models.Model):
    """
    Klinikada davolash yoki veterinar chaqirish bo‘yicha ariza.
    """

    SERVICE_TYPE_CLINIC = "clinic"
    SERVICE_TYPE_VET_CALL = "vet_call"

    SERVICE_TYPE_CHOICES = [
        (SERVICE_TYPE_CLINIC, "Klinikada davolash"),
        (SERVICE_TYPE_VET_CALL, "Veterinar chaqirish"),
    ]

    STATUS_NEW = "new"
    STATUS_ACCEPTED = "accepted"
    STATUS_ASSIGNED = "assigned"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_NEW, "Yangi"),
        (STATUS_ACCEPTED, "Qabul qilindi"),
        (STATUS_ASSIGNED, "Veterinarga biriktirildi"),
        (STATUS_IN_PROGRESS, "Jarayonda"),
        (STATUS_COMPLETED, "Yakunlandi"),
        (STATUS_CANCELLED, "Bekor qilindi"),
    ]

    client = models.ForeignKey(
        "accounts.Client",
        on_delete=models.CASCADE,
        related_name="service_requests",
        verbose_name="Mijoz",
    )
    animal = models.ForeignKey(
        "animals.Animal",
        on_delete=models.CASCADE,
        related_name="service_requests",
        verbose_name="Hayvon",
    )
    service_type = models.CharField(
        max_length=30,
        choices=SERVICE_TYPE_CHOICES,
        verbose_name="Xizmat turi",
    )
    problem_description = models.TextField(
        verbose_name="Muammo tavsifi",
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Manzil",
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Kenglik",
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Uzunlik",
    )
    assigned_doctor = models.ForeignKey(
        "dashboard.DoctorProfile",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="assigned_service_requests",
        verbose_name="Biriktirilgan veterinar",
    )
    assigned_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Biriktirilgan vaqt",
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        verbose_name="Holati",
    )
    admin_comment = models.TextField(
        blank=True,
        null=True,
        verbose_name="Administrator izohi",
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
        verbose_name = "Xizmat arizasi"
        verbose_name_plural = "Xizmat arizalari"
        ordering = ["-created_at"]

    def assign_doctor(self, doctor, user=None, description=None):
        old_status = self.status

        self.assigned_doctor = doctor
        self.assigned_at = timezone.now()
        self.status = self.STATUS_ASSIGNED
        self.save(
            update_fields=[
                "assigned_doctor",
                "assigned_at",
                "status",
                "updated_at",
            ]
        )

        if doctor:
            doctor.refresh_status()

        from dashboard.models import ActionLog

        ActionLog.objects.create(
            user=user,
            service_request=self,
            doctor=doctor,
            action_type=ActionLog.ACTION_ASSIGNED,
            old_status=old_status,
            new_status=self.status,
            description=description or "Ariza veterinarga biriktirildi.",
        )

    def complete_request(self, user=None, description=None):
        old_status = self.status
        doctor = self.assigned_doctor

        self.status = self.STATUS_COMPLETED
        self.save(update_fields=["status", "updated_at"])

        if doctor:
            doctor.refresh_status()

        from dashboard.models import ActionLog

        ActionLog.objects.create(
            user=user,
            service_request=self,
            doctor=doctor,
            action_type=ActionLog.ACTION_COMPLETED,
            old_status=old_status,
            new_status=self.status,
            description=description or "Ariza yakunlandi.",
        )

    def __str__(self):
        return f"{self.client.full_name} — {self.get_service_type_display()}"


class DangerReport(models.Model):
    """
    Xavfli holatlar bo‘yicha xabar.
    """

    DANGER_TYPE_DEAD_ANIMAL = "dead_animal"
    DANGER_TYPE_AGGRESSIVE_ANIMAL = "aggressive_animal"
    DANGER_TYPE_INFECTIOUS_DISEASE = "infectious_disease"
    DANGER_TYPE_OTHER = "other"

    DANGER_TYPE_CHOICES = [
        (DANGER_TYPE_DEAD_ANIMAL, "O‘lik hayvon"),
        (DANGER_TYPE_AGGRESSIVE_ANIMAL, "Quturgan yoki tajovuzkor hayvon gumoni"),
        (DANGER_TYPE_INFECTIOUS_DISEASE, "Yuqumli kasallik gumoni"),
        (DANGER_TYPE_OTHER, "Boshqa xavfli holat"),
    ]

    STATUS_NEW = "new"
    STATUS_REVIEWED = "reviewed"
    STATUS_ASSIGNED = "assigned"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_NEW, "Yangi xavfli holat"),
        (STATUS_REVIEWED, "Ko‘rib chiqildi"),
        (STATUS_ASSIGNED, "Mas’ul biriktirildi"),
        (STATUS_IN_PROGRESS, "Chora ko‘rilmoqda"),
        (STATUS_COMPLETED, "Yakunlandi"),
        (STATUS_REJECTED, "Rad etildi"),
    ]

    client = models.ForeignKey(
        "accounts.Client",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="danger_reports",
        verbose_name="Xabar yuborgan mijoz",
    )
    danger_type = models.CharField(
        max_length=50,
        choices=DANGER_TYPE_CHOICES,
        verbose_name="Xavf turi",
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Qo‘shimcha ma’lumot",
    )
    phone = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name="Telefon raqam",
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Manzil",
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Kenglik",
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Uzunlik",
    )
    assigned_doctor = models.ForeignKey(
        "dashboard.DoctorProfile",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="assigned_danger_reports",
        verbose_name="Biriktirilgan mas’ul",
    )
    assigned_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Biriktirilgan vaqt",
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        verbose_name="Holati",
    )
    admin_comment = models.TextField(
        blank=True,
        null=True,
        verbose_name="Administrator izohi",
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
        verbose_name = "Xavfli holat xabari"
        verbose_name_plural = "Xavfli holatlar xabarlari"
        ordering = ["-created_at"]

    def assign_doctor(self, doctor, user=None, description=None):
        old_status = self.status

        self.assigned_doctor = doctor
        self.assigned_at = timezone.now()
        self.status = self.STATUS_ASSIGNED
        self.save(
            update_fields=[
                "assigned_doctor",
                "assigned_at",
                "status",
                "updated_at",
            ]
        )

        if doctor:
            doctor.refresh_status()

        from dashboard.models import ActionLog

        ActionLog.objects.create(
            user=user,
            danger_report=self,
            doctor=doctor,
            action_type=ActionLog.ACTION_ASSIGNED,
            old_status=old_status,
            new_status=self.status,
            description=description or "Xavfli holat uchun mas’ul biriktirildi.",
        )

    def complete_report(self, user=None, description=None):
        old_status = self.status
        doctor = self.assigned_doctor

        self.status = self.STATUS_COMPLETED
        self.save(update_fields=["status", "updated_at"])

        if doctor:
            doctor.refresh_status()

        from dashboard.models import ActionLog

        ActionLog.objects.create(
            user=user,
            danger_report=self,
            doctor=doctor,
            action_type=ActionLog.ACTION_COMPLETED,
            old_status=old_status,
            new_status=self.status,
            description=description or "Xavfli holat yakunlandi.",
        )

    def __str__(self):
        return f"{self.get_danger_type_display()} — {self.get_status_display()}"
from datetime import datetime

from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import Client
from animals.models import Animal
from dashboard.models import ActionLog, DoctorProfile
from requests_app.models import DangerReport, ServiceRequest


# =========================
# ROLE / ACCESS CONTROL
# =========================

def is_administrator(user):
    """
    Dashboardga faqat:
    1) Superuser
    2) Administrator guruhidagi user kira oladi.
    """
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name="Administrator").exists()
    )


dashboard_required = user_passes_test(
    is_administrator,
    login_url="/admin/login/",
)


# =========================
# LABELS
# =========================

SERVICE_STATUS_LABELS = {
    "new": "Yangi",
    "accepted": "Qabul qilindi",
    "assigned": "Veterinarga biriktirildi",
    "in_progress": "Jarayonda",
    "completed": "Yakunlandi",
    "cancelled": "Bekor qilindi",
}

DANGER_STATUS_LABELS = {
    "new": "Yangi xavfli holat",
    "reviewed": "Ko‘rib chiqildi",
    "assigned": "Mas’ul biriktirildi",
    "in_progress": "Chora ko‘rilmoqda",
    "completed": "Yakunlandi",
    "rejected": "Rad etildi",
}

ANIMAL_TYPE_LABELS = {
    "dog": "It",
    "cat": "Mushuk",
    "cow": "Mol",
    "horse": "Ot",
    "sheep": "Qo‘y",
    "goat": "Echki",
    "bird": "Qush / Parranda",
    "other": "Boshqa",
}


# =========================
# HELPERS
# =========================

def get_today_range():
    today = timezone.localdate()
    start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    return start, end


def get_query(request):
    return request.GET.get("q", "").strip()


def get_active_doctors():
    return DoctorProfile.objects.filter(is_active=True).order_by("full_name")


def filter_service_queryset(queryset, query):
    if not query:
        return queryset

    return queryset.filter(
        Q(client__full_name__icontains=query)
        | Q(client__phone__icontains=query)
        | Q(client__telegram_username__icontains=query)
        | Q(animal__name__icontains=query)
        | Q(address__icontains=query)
        | Q(problem_description__icontains=query)
        | Q(assigned_doctor__full_name__icontains=query)
    )


def filter_danger_queryset(queryset, query):
    if not query:
        return queryset

    return queryset.filter(
        Q(client__full_name__icontains=query)
        | Q(client__phone__icontains=query)
        | Q(client__telegram_username__icontains=query)
        | Q(phone__icontains=query)
        | Q(address__icontains=query)
        | Q(description__icontains=query)
        | Q(assigned_doctor__full_name__icontains=query)
    )


def get_service_status_count(status):
    return ServiceRequest.objects.filter(status=status).count()


def get_danger_status_count(status):
    return DangerReport.objects.filter(status=status).count()


def write_status_log(
    user,
    service_request=None,
    danger_report=None,
    doctor=None,
    old_status=None,
    new_status=None,
    description=None,
):
    ActionLog.objects.create(
        user=user,
        service_request=service_request,
        danger_report=danger_report,
        doctor=doctor,
        action_type=ActionLog.ACTION_STATUS_CHANGED,
        old_status=old_status,
        new_status=new_status,
        description=description,
    )


def redirect_service_page(service_request):
    if service_request.service_type == ServiceRequest.SERVICE_TYPE_CLINIC:
        return redirect("dashboard:clinic_requests")

    return redirect("dashboard:vet_call_requests")


# =========================
# DASHBOARD HOME
# =========================

@dashboard_required
def dashboard_home(request):
    query = get_query(request)
    today_start, today_end = get_today_range()

    service_requests = ServiceRequest.objects.select_related(
        "client",
        "animal",
        "assigned_doctor",
    )

    danger_reports = DangerReport.objects.select_related(
        "client",
        "assigned_doctor",
    )

    if query:
        service_requests = filter_service_queryset(service_requests, query)
        danger_reports = filter_danger_queryset(danger_reports, query)

    today_service_requests = service_requests.filter(
        created_at__range=(today_start, today_end)
    )

    today_danger_reports = danger_reports.filter(
        created_at__range=(today_start, today_end)
    )

    context = {
        "active_page": "home",
        "query": query,

        "total_clinic": ServiceRequest.objects.filter(service_type="clinic").count(),
        "total_vet_call": ServiceRequest.objects.filter(service_type="vet_call").count(),
        "total_danger": DangerReport.objects.count(),
        "total_new": (
            ServiceRequest.objects.filter(status="new").count()
            + DangerReport.objects.filter(status="new").count()
        ),

        "today_clinic": today_service_requests.filter(service_type="clinic").count(),
        "today_vet_call": today_service_requests.filter(service_type="vet_call").count(),
        "today_danger": today_danger_reports.count(),

        "service_new": get_service_status_count("new"),
        "service_accepted": get_service_status_count("accepted"),
        "service_assigned": get_service_status_count("assigned"),
        "service_in_progress": get_service_status_count("in_progress"),
        "service_completed": get_service_status_count("completed"),
        "service_cancelled": get_service_status_count("cancelled"),

        "danger_new": get_danger_status_count("new"),
        "danger_reviewed": get_danger_status_count("reviewed"),
        "danger_assigned": get_danger_status_count("assigned"),
        "danger_in_progress": get_danger_status_count("in_progress"),
        "danger_completed": get_danger_status_count("completed"),
        "danger_rejected": get_danger_status_count("rejected"),

        "recent_service_requests": service_requests.order_by("-created_at")[:8],
        "recent_danger_reports": danger_reports.order_by("-created_at")[:5],
        "service_status_labels": SERVICE_STATUS_LABELS,
        "danger_status_labels": DANGER_STATUS_LABELS,
    }

    return render(request, "dashboard/index.html", context)


# =========================
# QUICK REQUEST
# =========================

@dashboard_required
def quick_request(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        service_type = request.POST.get("service_type", "clinic").strip()
        animal_type = request.POST.get("animal_type", "other").strip()
        animal_name = request.POST.get("animal_name", "").strip()
        problem_description = request.POST.get("problem_description", "").strip()
        address = request.POST.get("address", "").strip()

        if service_type not in ["clinic", "vet_call"]:
            service_type = "clinic"

        if not full_name:
            full_name = "Telefon orqali murojaat"

        if not problem_description:
            if service_type == "clinic":
                problem_description = "Telefon orqali klinikada davolash arizasi"
            else:
                problem_description = "Telefon orqali veterinar chaqirish arizasi"

        client = None

        if phone:
            client = Client.objects.filter(phone=phone).first()

        if not client:
            client = Client.objects.create(
                full_name=full_name,
                phone=phone,
                address=address,
            )
        else:
            client.full_name = full_name
            if phone:
                client.phone = phone
            if address:
                client.address = address
            client.save()

        animal = Animal.objects.create(
            client=client,
            animal_type=animal_type,
            name=animal_name if animal_name else None,
            symptoms=problem_description,
        )

        ServiceRequest.objects.create(
            client=client,
            animal=animal,
            service_type=service_type,
            problem_description=problem_description,
            address="Klinika ichida" if service_type == "clinic" else address,
            status="new",
            admin_comment="Administrator tomonidan telefon orqali kiritildi.",
        )

        if service_type == "clinic":
            return redirect("dashboard:clinic_requests")

        return redirect("dashboard:vet_call_requests")

    context = {
        "active_page": "quick_request",
        "animal_type_labels": ANIMAL_TYPE_LABELS,
    }

    return render(request, "dashboard/quick_request.html", context)


# =========================
# CLINIC REQUESTS
# =========================

@dashboard_required
def clinic_requests(request):
    query = get_query(request)

    requests_qs = (
        ServiceRequest.objects
        .select_related("client", "animal", "assigned_doctor")
        .filter(service_type="clinic")
        .order_by("-created_at")
    )

    requests_qs = filter_service_queryset(requests_qs, query)

    context = {
        "active_page": "clinic",
        "query": query,
        "title": "Klinikada davolash arizalari",
        "requests": requests_qs,
        "status_labels": SERVICE_STATUS_LABELS,
        "doctors": get_active_doctors(),
    }

    return render(request, "dashboard/service_requests.html", context)


# =========================
# VET CALL REQUESTS
# =========================

@dashboard_required
def vet_call_requests(request):
    query = get_query(request)

    requests_qs = (
        ServiceRequest.objects
        .select_related("client", "animal", "assigned_doctor")
        .filter(service_type="vet_call")
        .order_by("-created_at")
    )

    requests_qs = filter_service_queryset(requests_qs, query)

    context = {
        "active_page": "vet_call",
        "query": query,
        "title": "Veterinar chaqirish arizalari",
        "requests": requests_qs,
        "status_labels": SERVICE_STATUS_LABELS,
        "doctors": get_active_doctors(),
    }

    return render(request, "dashboard/service_requests.html", context)


# =========================
# DANGER REPORTS
# =========================

@dashboard_required
def danger_reports(request):
    query = get_query(request)

    reports = (
        DangerReport.objects
        .select_related("client", "assigned_doctor")
        .order_by("-created_at")
    )

    reports = filter_danger_queryset(reports, query)

    context = {
        "active_page": "danger",
        "query": query,
        "reports": reports,
        "status_labels": DANGER_STATUS_LABELS,
        "doctors": get_active_doctors(),
    }

    return render(request, "dashboard/danger_reports.html", context)


# =========================
# UPDATE SERVICE STATUS / ASSIGN DOCTOR
# =========================

@dashboard_required
def update_service_status(request, request_id):
    service_request = get_object_or_404(
        ServiceRequest.objects.select_related("assigned_doctor"),
        id=request_id,
    )

    if request.method != "POST":
        return redirect_service_page(service_request)

    action = request.POST.get("action", "").strip()
    status = request.POST.get("status", "").strip()
    doctor_id = request.POST.get("doctor_id", "").strip()
    admin_comment = request.POST.get("admin_comment", "").strip()

    old_status = service_request.status
    old_doctor = service_request.assigned_doctor

    if admin_comment:
        service_request.admin_comment = admin_comment
        service_request.save(update_fields=["admin_comment", "updated_at"])

    if action == "assign":
        if not doctor_id:
            return redirect_service_page(service_request)

        doctor = get_object_or_404(
            DoctorProfile,
            id=doctor_id,
            is_active=True,
        )

        service_request.assign_doctor(
            doctor=doctor,
            user=request.user,
            description=admin_comment or "Ariza veterinarga biriktirildi.",
        )

        if old_doctor and old_doctor.id != doctor.id:
            old_doctor.refresh_status()

    elif action == "complete":
        if not service_request.assigned_doctor:
            write_status_log(
                user=request.user,
                service_request=service_request,
                doctor=None,
                old_status=old_status,
                new_status=service_request.status,
                description="Ariza yakunlanmadi: avval veterinar biriktirilishi kerak.",
            )
            return redirect_service_page(service_request)

        service_request.complete_request(
            user=request.user,
            description=admin_comment or "Ariza yakunlandi.",
        )

    else:
        allowed_statuses = [choice[0] for choice in ServiceRequest.STATUS_CHOICES]

        if status in allowed_statuses:
            if status == ServiceRequest.STATUS_COMPLETED and not service_request.assigned_doctor:
                write_status_log(
                    user=request.user,
                    service_request=service_request,
                    doctor=None,
                    old_status=old_status,
                    new_status=service_request.status,
                    description="Status yakunlandiga o‘zgartirilmadi: avval veterinar biriktirilishi kerak.",
                )
                return redirect_service_page(service_request)

            service_request.status = status
            service_request.save(update_fields=["status", "updated_at"])

            if service_request.assigned_doctor:
                service_request.assigned_doctor.refresh_status()

            write_status_log(
                user=request.user,
                service_request=service_request,
                doctor=service_request.assigned_doctor,
                old_status=old_status,
                new_status=service_request.status,
                description=admin_comment or "Ariza statusi o‘zgartirildi.",
            )

    return redirect_service_page(service_request)


# =========================
# UPDATE DANGER STATUS / ASSIGN RESPONSIBLE
# =========================

@dashboard_required
def update_danger_status(request, report_id):
    report = get_object_or_404(
        DangerReport.objects.select_related("assigned_doctor"),
        id=report_id,
    )

    if request.method != "POST":
        return redirect("dashboard:danger_reports")

    action = request.POST.get("action", "").strip()
    status = request.POST.get("status", "").strip()
    doctor_id = request.POST.get("doctor_id", "").strip()
    admin_comment = request.POST.get("admin_comment", "").strip()

    old_status = report.status
    old_doctor = report.assigned_doctor

    if admin_comment:
        report.admin_comment = admin_comment
        report.save(update_fields=["admin_comment", "updated_at"])

    if action == "assign":
        if not doctor_id:
            return redirect("dashboard:danger_reports")

        doctor = get_object_or_404(
            DoctorProfile,
            id=doctor_id,
            is_active=True,
        )

        report.assign_doctor(
            doctor=doctor,
            user=request.user,
            description=admin_comment or "Xavfli holat uchun mas’ul biriktirildi.",
        )

        if old_doctor and old_doctor.id != doctor.id:
            old_doctor.refresh_status()

    elif action == "complete":
        if not report.assigned_doctor:
            write_status_log(
                user=request.user,
                danger_report=report,
                doctor=None,
                old_status=old_status,
                new_status=report.status,
                description="Xavfli holat yakunlanmadi: avval mas’ul biriktirilishi kerak.",
            )
            return redirect("dashboard:danger_reports")

        report.complete_report(
            user=request.user,
            description=admin_comment or "Xavfli holat yakunlandi.",
        )

    else:
        allowed_statuses = [choice[0] for choice in DangerReport.STATUS_CHOICES]

        if status in allowed_statuses:
            if status == DangerReport.STATUS_COMPLETED and not report.assigned_doctor:
                write_status_log(
                    user=request.user,
                    danger_report=report,
                    doctor=None,
                    old_status=old_status,
                    new_status=report.status,
                    description="Status yakunlandiga o‘zgartirilmadi: avval mas’ul biriktirilishi kerak.",
                )
                return redirect("dashboard:danger_reports")

            report.status = status
            report.save(update_fields=["status", "updated_at"])

            if report.assigned_doctor:
                report.assigned_doctor.refresh_status()

            write_status_log(
                user=request.user,
                danger_report=report,
                doctor=report.assigned_doctor,
                old_status=old_status,
                new_status=report.status,
                description=admin_comment or "Xavfli holat statusi o‘zgartirildi.",
            )

    return redirect("dashboard:danger_reports")


# =========================
# HISTORY
# =========================

@dashboard_required
def history(request):
    query = get_query(request)
    selected_date = request.GET.get("date", "").strip()
    selected_month = request.GET.get("month", "").strip()
    selected_year = request.GET.get("year", "").strip()
    show_all = request.GET.get("all", "").strip()

    service_requests = (
        ServiceRequest.objects
        .select_related("client", "animal", "assigned_doctor")
        .order_by("-created_at")
    )

    danger_reports_qs = (
        DangerReport.objects
        .select_related("client", "assigned_doctor")
        .order_by("-created_at")
    )

    if query:
        service_requests = filter_service_queryset(service_requests, query)
        danger_reports_qs = filter_danger_queryset(danger_reports_qs, query)

    if not show_all:
        if selected_date:
            service_requests = service_requests.filter(created_at__date=selected_date)
            danger_reports_qs = danger_reports_qs.filter(created_at__date=selected_date)

        elif selected_month:
            year, month = selected_month.split("-")
            service_requests = service_requests.filter(
                created_at__year=year,
                created_at__month=month,
            )
            danger_reports_qs = danger_reports_qs.filter(
                created_at__year=year,
                created_at__month=month,
            )

        elif selected_year:
            service_requests = service_requests.filter(created_at__year=selected_year)
            danger_reports_qs = danger_reports_qs.filter(created_at__year=selected_year)

        else:
            today = timezone.localdate()
            service_requests = service_requests.filter(created_at__date=today)
            danger_reports_qs = danger_reports_qs.filter(created_at__date=today)

    history_items = []

    for item in service_requests:
        history_items.append({
            "type": item.get_service_type_display(),
            "is_danger": False,
            "client": item.client,
            "animal": item.animal,
            "doctor": item.assigned_doctor,
            "status": item.status,
            "status_label": SERVICE_STATUS_LABELS.get(item.status, item.status),
            "address": item.address,
            "latitude": item.latitude,
            "longitude": item.longitude,
            "created_at": item.created_at,
        })

    for item in danger_reports_qs:
        history_items.append({
            "type": item.get_danger_type_display(),
            "is_danger": True,
            "client": item.client,
            "animal": None,
            "doctor": item.assigned_doctor,
            "status": item.status,
            "status_label": DANGER_STATUS_LABELS.get(item.status, item.status),
            "address": item.address,
            "latitude": item.latitude,
            "longitude": item.longitude,
            "created_at": item.created_at,
        })

    history_items = sorted(
        history_items,
        key=lambda x: x["created_at"],
        reverse=True,
    )

    action_logs = (
        ActionLog.objects
        .select_related("user", "doctor", "service_request", "danger_report")
        .order_by("-created_at")[:100]
    )

    context = {
        "active_page": "history",
        "query": query,
        "history_items": history_items,
        "action_logs": action_logs,
        "selected_date": selected_date,
        "selected_month": selected_month,
        "selected_year": selected_year,
        "show_all": show_all,
    }

    return render(request, "dashboard/history.html", context)


# =========================
# SETTINGS
# =========================

@dashboard_required
def settings_page(request):
    doctors = DoctorProfile.objects.all().order_by("full_name")

    context = {
        "active_page": "settings",
        "doctors": doctors,
    }

    return render(request, "dashboard/settings.html", context)
from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("login/", views.unified_login, name="login"),
    path("logout/", views.unified_logout, name="logout"),

    # Administrator dashboard
    path("", views.dashboard_home, name="home"),
    path("quick-request/", views.quick_request, name="quick_request"),
    path("clinic/", views.clinic_requests, name="clinic_requests"),
    path("vet-call/", views.vet_call_requests, name="vet_call_requests"),
    path("danger/", views.danger_reports, name="danger_reports"),
    path("history/", views.history, name="history"),
    path("settings/", views.settings_page, name="settings"),

    # Veterinar dashboard
    path("doctor/", views.doctor_dashboard, name="doctor_home"),
    path(
        "doctor/request/<int:request_id>/status/",
        views.doctor_update_service_status,
        name="doctor_update_service_status",
    ),
    path(
        "doctor/danger/<int:report_id>/status/",
        views.doctor_update_danger_status,
        name="doctor_update_danger_status",
    ),

    # Administrator actions
    path(
        "service/<int:request_id>/status/",
        views.update_service_status,
        name="update_service_status",
    ),
    path(
        "danger/<int:report_id>/status/",
        views.update_danger_status,
        name="update_danger_status",
    ),
]
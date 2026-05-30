from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard_home, name="home"),
    path("quick-request/", views.quick_request, name="quick_request"),

    path("clinic/", views.clinic_requests, name="clinic_requests"),
    path("vet-call/", views.vet_call_requests, name="vet_call_requests"),
    path("danger/", views.danger_reports, name="danger_reports"),

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

    path("history/", views.history, name="history"),
    path("settings/", views.settings_page, name="settings"),
]
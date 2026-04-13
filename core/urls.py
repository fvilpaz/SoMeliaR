from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("asistente/", views.asistente, name="asistente"),
    path("asistente/api/", views.asistente_api, name="asistente_api"),
]

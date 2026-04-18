from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("anotaciones/", views.anotaciones, name="anotaciones"),
    path("anotaciones/<int:pk>/resolver/", views.anotacion_resolver, name="anotacion_resolver"),
    path("anotaciones/<int:pk>/eliminar/", views.anotacion_eliminar, name="anotacion_eliminar"),
]

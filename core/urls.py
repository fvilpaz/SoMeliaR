from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("registro/", views.registro, name="registro"),
    path("perfil/", views.perfil, name="perfil"),
    path("herramientas/", views.herramientas, name="herramientas"),
    path("anotaciones/", views.anotaciones, name="anotaciones"),
    path("ayuda/", views.ayuda, name="ayuda"),
    path("anotaciones/<int:pk>/resolver/", views.anotacion_resolver, name="anotacion_resolver"),
    path("anotaciones/<int:pk>/eliminar/", views.anotacion_eliminar, name="anotacion_eliminar"),
]

from django.urls import path
from . import views

app_name = "bodega"

urlpatterns = [
    path("", views.vino_list, name="vino_list"),
    path("<int:pk>/", views.vino_detail, name="vino_detail"),
    path("<int:pk>/movimiento/", views.movimiento_create, name="movimiento_create"),
]
from django.urls import path
from . import views

app_name = "proveedores"

urlpatterns = [
    path("", views.proveedor_list, name="proveedor_list"),
    path("<int:pk>/", views.proveedor_detail, name="proveedor_detail"),
    path("nuevo/", views.proveedor_create, name="proveedor_create"),
    path("<int:pk>/editar/", views.proveedor_edit, name="proveedor_edit"),
]
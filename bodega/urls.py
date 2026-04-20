from django.urls import path
from . import views

app_name = "bodega"

urlpatterns = [
    path("", views.vino_list, name="vino_list"),
    path("nuevo/", views.vino_create, name="vino_create"),
    path("exportar/", views.vino_export_csv, name="vino_export"),
    path("movimiento-rapido/", views.movimiento_rapido, name="movimiento_rapido"),
    path("<int:pk>/", views.vino_detail, name="vino_detail"),
    path("<int:pk>/editar/", views.vino_edit, name="vino_edit"),
    path("<int:pk>/eliminar/", views.vino_delete, name="vino_delete"),
    path("<int:pk>/movimiento/", views.movimiento_create, name="movimiento_create"),
    path("<int:pk>/descripcion/", views.vino_descripcion, name="vino_descripcion"),
    path("etiqueta/crear/", views.etiqueta_crear, name="etiqueta_crear"),
    path("<int:pk>/imagen/", views.vino_imagen_upload, name="vino_imagen_upload"),
]

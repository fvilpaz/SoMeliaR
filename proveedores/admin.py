from django.contrib import admin
from .models import Proveedor, VinoProveedor


class VinoProveedorInline(admin.TabularInline):
    model = VinoProveedor
    extra = 1


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ["nombre", "email", "contacto", "activo"]
    list_filter = ["activo"]
    search_fields = ["nombre", "contacto"]
    inlines = [VinoProveedorInline]


@admin.register(VinoProveedor)
class VinoProveedorAdmin(admin.ModelAdmin):
    list_display = ["vino", "proveedor", "precio", "es_principal"]
    list_filter = ["es_principal", "proveedor"]
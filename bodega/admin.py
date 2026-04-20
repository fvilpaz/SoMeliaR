from django.contrib import admin
from .models import Etiqueta, Vino, Movimiento, StockConfig


class StockConfigInline(admin.StackedInline):
    model = StockConfig
    extra = 0


@admin.register(Vino)
class VinoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "bodega_nombre", "familia", "stock_actual", "es_copa", "via_coupa", "activo"]
    list_filter = ["familia", "activo", "es_copa", "via_coupa", "en_canitas", "en_ene", "en_pool"]
    search_fields = ["nombre", "bodega_nombre", "denominacion_origen", "variedades"]
    inlines = [StockConfigInline]


@admin.register(Etiqueta)
class EtiquetaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "color"]


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ["vino", "tipo", "cantidad", "fecha"]
    list_filter = ["tipo", "fecha"]
    search_fields = ["vino__nombre"]
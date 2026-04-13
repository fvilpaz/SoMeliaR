from django.contrib import admin
from .models import Pedido, LineaPedido


class LineaPedidoInline(admin.TabularInline):
    model = LineaPedido
    extra = 1


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ["__str__", "estado", "generado_por_ia", "fecha_creacion"]
    list_filter = ["estado", "generado_por_ia"]
    inlines = [LineaPedidoInline]

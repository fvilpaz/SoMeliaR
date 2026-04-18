from decimal import Decimal

from django.shortcuts import render, redirect
from django.db.models import Sum, DecimalField, Value
from django.db.models.functions import Coalesce

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from bodega.models import Vino, StockConfig
from pedidos.models import Pedido
from .models import Anotacion


def dashboard(request):
    # Una sola query: stock calculado + config de mínimos
    vinos = list(
        Vino.objects
        .filter(activo=True)
        .select_related("stock_config")
        .annotate(
            stock_anotado=Coalesce(
                Sum("movimientos__cantidad"),
                Value(Decimal("0")),
                output_field=DecimalField(),
            )
        )
    )

    # Resumen por familia (en Python, sin más queries)
    familias = []
    for codigo, nombre in Vino.Familia.choices:
        vinos_familia = [v for v in vinos if v.familia == codigo]
        if not vinos_familia:
            continue
        stock_total = sum(v.stock_anotado for v in vinos_familia)
        bajo_minimo_count = sum(
            1 for v in vinos_familia
            if hasattr(v, "stock_config") and v.stock_anotado < v.stock_config.stock_minimo
        )
        familias.append({
            "codigo": codigo,
            "nombre": nombre,
            "count": len(vinos_familia),
            "stock_total": stock_total,
            "bajo_minimo": bajo_minimo_count,
        })

    # Alertas: vinos bajo mínimo (sin queries adicionales)
    alertas = []
    for v in vinos:
        try:
            if v.stock_anotado < v.stock_config.stock_minimo:
                alertas.append({
                    "vino": v,
                    "stock_actual": v.stock_anotado,
                    "stock_minimo": v.stock_config.stock_minimo,
                })
        except StockConfig.DoesNotExist:
            pass

    pedidos_pendientes = Pedido.objects.filter(
        estado__in=[Pedido.Estado.BORRADOR, Pedido.Estado.PENDIENTE]
    ).count()

    valor_inventario = sum(v.stock_anotado * v.precio_coste for v in vinos)

    chart_labels = [f["nombre"] for f in familias]
    chart_data = [float(f["stock_total"]) for f in familias]

    context = {
        "familias": familias,
        "alertas": alertas,
        "pedidos_pendientes": pedidos_pendientes,
        "chart_labels": chart_labels,
        "chart_data": chart_data,
        "total_vinos": len(vinos),
        "valor_inventario": valor_inventario,
    }
    return render(request, "dashboard.html", context)


def anotaciones(request):
    if request.method == "POST":
        texto = request.POST.get("texto", "").strip()
        prioridad = request.POST.get("prioridad", Anotacion.Prioridad.NORMAL)
        if texto:
            Anotacion.objects.create(texto=texto, prioridad=prioridad)
        return redirect("core:anotaciones")

    lista = Anotacion.objects.filter(resuelta=False)
    resueltas = Anotacion.objects.filter(resuelta=True)[:10]
    return render(request, "anotaciones.html", {"lista": lista, "resueltas": resueltas})


@require_POST
def anotacion_resolver(request, pk):
    Anotacion.objects.filter(pk=pk).update(resuelta=True)
    return JsonResponse({"ok": True})


@require_POST
def anotacion_eliminar(request, pk):
    Anotacion.objects.filter(pk=pk).delete()
    return JsonResponse({"ok": True})



import json

from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Sum, Count
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from bodega.models import Vino, StockConfig
from pedidos.models import Pedido
from .services import interpretar_comando, ejecutar_comando


def dashboard(request):
    vinos = Vino.objects.filter(activo=True)

    # Resumen por familia
    familias = []
    for codigo, nombre in Vino.Familia.choices:
        vinos_familia = vinos.filter(familia=codigo)
        count = vinos_familia.count()
        if count == 0:
            continue
        # Calcular stock total de la familia
        stock_total = 0
        bajo_minimo_count = 0
        for v in vinos_familia:
            stock_total += v.stock_actual
            if v.bajo_minimo:
                bajo_minimo_count += 1
        familias.append({
            "codigo": codigo,
            "nombre": nombre,
            "count": count,
            "stock_total": stock_total,
            "bajo_minimo": bajo_minimo_count,
        })

    # Alertas: vinos bajo mínimo
    alertas = []
    for v in vinos:
        if v.bajo_minimo:
            alertas.append({
                "vino": v,
                "stock_actual": v.stock_actual,
                "stock_minimo": v.stock_config.stock_minimo,
            })

    # Pedidos pendientes
    pedidos_pendientes = Pedido.objects.filter(
        estado__in=[Pedido.Estado.BORRADOR, Pedido.Estado.PENDIENTE]
    ).count()

    # Datos para Chart.js
    chart_labels = [f["nombre"] for f in familias]
    chart_data = [f["stock_total"] for f in familias]

    context = {
        "familias": familias,
        "alertas": alertas,
        "pedidos_pendientes": pedidos_pendientes,
        "chart_labels": chart_labels,
        "chart_data": chart_data,
        "total_vinos": vinos.count(),
    }
    return render(request, "dashboard.html", context)


def asistente(request):
    """Página del asistente de voz."""
    return render(request, "asistente.html")


@csrf_exempt
@require_POST
def asistente_api(request):
    """API que recibe texto transcrito y ejecuta la acción."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "mensaje": "JSON inválido"}, status=400)

    texto = data.get("texto", "").strip()
    if not texto:
        return JsonResponse({"ok": False, "mensaje": "No hay texto"}, status=400)

    # 1. Interpretar con Gemini
    comando = interpretar_comando(texto)

    # 2. Ejecutar la acción
    resultado = ejecutar_comando(comando)

    return JsonResponse(resultado)

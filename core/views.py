from decimal import Decimal

import io
import tempfile
import os

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.management import call_command
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.db.models import Sum, DecimalField, Value
from django.db.models.functions import Coalesce

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from bodega.models import Vino, StockConfig, Movimiento
from pedidos.models import Pedido, LineaPedido
from proveedores.models import Proveedor, VinoProveedor
from .forms import RegistroForm, PerfilForm
from .models import Anotacion


@login_required
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


@login_required
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


@login_required
@require_POST
def anotacion_resolver(request, pk):
    Anotacion.objects.filter(pk=pk).update(resuelta=True)
    return JsonResponse({"ok": True})


@login_required
@require_POST
def anotacion_eliminar(request, pk):
    Anotacion.objects.filter(pk=pk).delete()
    return JsonResponse({"ok": True})


@login_required
def herramientas(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Solo superusuarios.")

    stats = {
        "vinos": Vino.objects.count(),
        "movimientos": Movimiento.objects.count(),
        "proveedores": Proveedor.objects.count(),
        "pedidos": Pedido.objects.count(),
        "anotaciones": Anotacion.objects.count(),
    }

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "limpiar":
            LineaPedido.objects.all().delete()
            Pedido.objects.all().delete()
            VinoProveedor.objects.all().delete()
            Movimiento.objects.all().delete()
            StockConfig.objects.all().delete()
            Vino.objects.all().delete()
            Proveedor.objects.all().delete()
            Anotacion.objects.all().delete()
            messages.success(request, "Base de datos limpiada. Puedes importar un Excel nuevo.")
            return redirect("core:herramientas")

        elif accion == "importar":
            archivo = request.FILES.get("excel")
            if not archivo:
                messages.error(request, "Selecciona un archivo Excel (.xls).")
                return redirect("core:herramientas")
            if not archivo.name.endswith(".xls"):
                messages.error(request, "El archivo debe ser .xls (formato Excel 97-2003).")
                return redirect("core:herramientas")

            # Guardar en archivo temporal y lanzar el comando de importación
            with tempfile.NamedTemporaryFile(suffix=".xls", delete=False) as tmp:
                for chunk in archivo.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name

            try:
                out = io.StringIO()
                call_command("importar_excel", tmp_path, stdout=out, stderr=out)
                output = out.getvalue()
                vinos_nuevos = Vino.objects.count()
                messages.success(
                    request,
                    f"Importación completada: {vinos_nuevos} vinos, "
                    f"{Proveedor.objects.count()} proveedores, "
                    f"{Movimiento.objects.count()} movimientos."
                )
            except Exception as e:
                messages.error(request, f"Error al importar: {e}")
            finally:
                os.unlink(tmp_path)

            return redirect("core:herramientas")

    return render(request, "herramientas.html", {"stats": stats})


def registro(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"¡Bienvenido, {user.first_name or user.username}! Cuenta creada correctamente.")
            return redirect("core:dashboard")
    else:
        form = RegistroForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def perfil(request):
    if request.method == "POST":
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect("core:perfil")
    else:
        form = PerfilForm(instance=request.user)
    return render(request, "registration/profile.html", {"form": form})



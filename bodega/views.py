from decimal import Decimal

from django.contrib import messages
from django.db.models import Sum, DecimalField, Value
from django.db.models.functions import Coalesce
from django.shortcuts import render, get_object_or_404, redirect

from .models import Vino, Movimiento
from .forms import MovimientoForm


def vino_list(request):
    familia = request.GET.get("familia", "")
    vinos = (
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
    if familia:
        vinos = vinos.filter(familia=familia)

    familias = Vino.Familia.choices
    context = {
        "vinos": vinos,
        "familias": familias,
        "familia_actual": familia,
    }
    return render(request, "bodega/vino_list.html", context)


def vino_detail(request, pk):
    vino = get_object_or_404(Vino, pk=pk)
    movimientos = vino.movimientos.all()[:20]
    context = {
        "vino": vino,
        "movimientos": movimientos,
    }
    return render(request, "bodega/vino_detail.html", context)


def movimiento_rapido(request):
    vinos = Vino.objects.filter(activo=True).order_by("nombre")

    if request.method == "POST":
        vino_id = request.POST.get("vino_id")
        tipo = request.POST.get("tipo")
        try:
            cantidad = Decimal(request.POST.get("cantidad", "1"))
        except Exception:
            cantidad = Decimal("1")

        vino = get_object_or_404(Vino, pk=vino_id, activo=True)

        if tipo == Movimiento.Tipo.SALIDA:
            cantidad_mov = -abs(cantidad)
        elif tipo == Movimiento.Tipo.ENTRADA:
            cantidad_mov = abs(cantidad)
        else:
            cantidad_mov = cantidad

        Movimiento.objects.create(vino=vino, tipo=tipo, cantidad=cantidad_mov)

        stock_nuevo = vino.stock_actual
        accion = {"entrada": "Entrada", "salida": "Salida", "ajuste": "Ajuste"}.get(tipo, tipo)
        messages.success(
            request,
            f"{accion} registrada: {abs(cantidad):.0f} × {vino}. Stock actual: {stock_nuevo:.1f} uds."
        )
        return redirect("bodega:movimiento_rapido")

    context = {"vinos": vinos}
    return render(request, "bodega/movimiento_rapido.html", context)


def movimiento_create(request, pk):
    vino = get_object_or_404(Vino, pk=pk)
    if request.method == "POST":
        form = MovimientoForm(request.POST)
        if form.is_valid():
            movimiento = form.save(commit=False)
            movimiento.vino = vino
            movimiento.save()
            return redirect("bodega:vino_detail", pk=vino.pk)
    else:
        form = MovimientoForm()
    context = {
        "vino": vino,
        "form": form,
    }
    return render(request, "bodega/movimiento_form.html", context)
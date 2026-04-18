from decimal import Decimal

from django.db.models import Sum, DecimalField, Value
from django.db.models.functions import Coalesce
from django.shortcuts import render, get_object_or_404, redirect

from .models import Vino
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
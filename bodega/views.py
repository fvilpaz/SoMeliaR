import csv
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, DecimalField, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from django.db.models import Q
from .models import Etiqueta, Vino, Movimiento, StockConfig
from .forms import MovimientoForm, VinoForm


@login_required
def vino_list(request):
    familia = request.GET.get("familia", "")
    busqueda = request.GET.get("q", "").strip()
    orden = request.GET.get("orden", "nombre")
    vista = request.GET.get("vista", "grid")

    orden_map = {
        "nombre": "nombre",
        "nombre_desc": "-nombre",
        "familia": "familia",
        "stock": "stock_anotado",
    }
    order_by = orden_map.get(orden, "nombre")

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
    if busqueda:
        vinos = vinos.filter(
            Q(nombre__icontains=busqueda) |
            Q(bodega_nombre__icontains=busqueda) |
            Q(denominacion_origen__icontains=busqueda)
        )

    vinos = vinos.order_by(order_by)

    familias = Vino.Familia.choices
    context = {
        "vinos": vinos,
        "familias": familias,
        "familia_actual": familia,
        "busqueda": busqueda,
        "orden": orden,
        "vista": vista,
    }
    return render(request, "bodega/vino_list.html", context)


@login_required
def vino_detail(request, pk):
    vino = get_object_or_404(Vino, pk=pk)
    movimientos = vino.movimientos.all()[:20]
    context = {
        "vino": vino,
        "movimientos": movimientos,
    }
    return render(request, "bodega/vino_detail.html", context)


@login_required
def vino_create(request):
    etiquetas_all = Etiqueta.objects.all()
    if request.method == "POST":
        form = VinoForm(request.POST, request.FILES)
        selected_ids = set(int(x) for x in request.POST.getlist("etiquetas") if x.isdigit())
        if form.is_valid():
            vino = form.save()
            stock_inicial = form.cleaned_data.get("stock_inicial") or Decimal("0")
            if stock_inicial > 0:
                Movimiento.objects.create(
                    vino=vino,
                    tipo=Movimiento.Tipo.ENTRADA,
                    cantidad=stock_inicial,
                    notas="Stock inicial al crear el vino",
                )
            messages.success(request, f"Vino «{vino}» creado correctamente.")
            return redirect("bodega:vino_detail", pk=vino.pk)
    else:
        form = VinoForm()
        selected_ids = set()
    return render(request, "bodega/vino_form.html", {
        "form": form, "titulo": "Nuevo vino",
        "etiquetas_all": etiquetas_all, "selected_ids": selected_ids,
    })


@login_required
def vino_edit(request, pk):
    vino = get_object_or_404(Vino, pk=pk)
    etiquetas_all = Etiqueta.objects.all()
    if request.method == "POST":
        form = VinoForm(request.POST, request.FILES, instance=vino)
        selected_ids = set(int(x) for x in request.POST.getlist("etiquetas") if x.isdigit())
        if form.is_valid():
            form.save()
            messages.success(request, f"Vino «{vino}» actualizado correctamente.")
            return redirect("bodega:vino_detail", pk=vino.pk)
    else:
        form = VinoForm(instance=vino)
        selected_ids = set(vino.etiquetas.values_list("pk", flat=True))
    return render(request, "bodega/vino_form.html", {
        "form": form, "titulo": f"Editar: {vino}", "vino": vino,
        "etiquetas_all": etiquetas_all, "selected_ids": selected_ids,
    })


@login_required
@require_POST
def vino_imagen_upload(request, pk):
    vino = get_object_or_404(Vino, pk=pk)
    if request.FILES.get("imagen"):
        vino.imagen = request.FILES["imagen"]
        vino.save()
    if request.POST.get("borrar") and vino.imagen:
        vino.imagen.delete(save=True)
    preview = (
        f'<img src="{vino.imagen.url}" alt="{vino.nombre}" '
        f'id="imagen-preview" class="img-fluid rounded mb-2" style="max-height:180px;object-fit:contain;">'
        f'<button type="button" class="btn btn-outline-danger btn-sm d-block" '
        f'hx-post="{request.path}" hx-vals=\'{{"borrar":"1"}}\' '
        f'hx-target="#imagen-wrap" hx-swap="innerHTML" '
        f'hx-headers=\'{{"X-CSRFToken":"{request.POST.get("csrfmiddlewaretoken","")}"}}\'>'
        f'<i class="bi bi-trash3 me-1"></i>Eliminar foto</button>'
        if vino.imagen else '<p class="text-muted small mb-0">Sin imagen.</p>'
    )
    return HttpResponse(preview)


@login_required
@require_POST
def etiqueta_crear(request):
    nombre = request.POST.get("nombre", "").strip()
    color = request.POST.get("color", "secondary")
    if not nombre:
        return HttpResponse("")
    etiqueta, _ = Etiqueta.objects.get_or_create(
        nombre__iexact=nombre,
        defaults={"nombre": nombre, "color": color},
    )
    return HttpResponse(
        f'<div class="form-check">'
        f'<input class="form-check-input" type="checkbox" name="etiquetas" '
        f'value="{etiqueta.pk}" id="etiq_{etiqueta.pk}" checked>'
        f'<label class="form-check-label" for="etiq_{etiqueta.pk}">'
        f'<span class="badge bg-{etiqueta.color}">{etiqueta.nombre}</span>'
        f'</label>'
        f'</div>'
    )


@login_required
def vino_delete(request, pk):
    vino = get_object_or_404(Vino, pk=pk)
    if request.method == "POST":
        nombre = str(vino)
        vino.activo = False
        vino.save()
        messages.success(request, f"Vino «{nombre}» eliminado de la carta.")
        return redirect("bodega:vino_list")
    return render(request, "bodega/vino_confirm_delete.html", {"vino": vino})


@login_required
def vino_export_csv(request):
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
        .order_by("familia", "nombre")
    )

    fecha = timezone.now().strftime("%Y%m%d")
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="bodega_{fecha}.csv"'
    response.write("\ufeff")  # BOM para que Excel abra bien con tildes

    writer = csv.writer(response)
    writer.writerow([
        "Nombre", "Bodega", "Añada", "Familia", "Tipo/Azúcar",
        "D.O.", "Variedades", "Precio coste", "Precio carta",
        "Stock actual", "Stock mínimo", "Stock óptimo",
        "Copa", "Precio copa", "Coupa", "Cañitas", "EÑE", "Pool", "Notas",
    ])
    for v in vinos:
        try:
            sc = v.stock_config
            s_min = sc.stock_minimo
            s_opt = sc.stock_optimo
        except StockConfig.DoesNotExist:
            s_min = s_opt = ""
        writer.writerow([
            v.nombre, v.bodega_nombre, v.anada or "",
            v.get_familia_display(), v.azucar,
            v.denominacion_origen, v.variedades,
            v.precio_coste, v.precio_carta,
            v.stock_anotado, s_min, s_opt,
            "Sí" if v.es_copa else "No", v.precio_copa if v.es_copa else "",
            "Sí" if v.via_coupa else "No",
            "Sí" if v.en_canitas else "No",
            "Sí" if v.en_ene else "No",
            "Sí" if v.en_pool else "No",
            v.notas,
        ])
    return response


@login_required
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


@login_required
@require_POST
def vino_descripcion(request, pk):
    vino = get_object_or_404(Vino, pk=pk)
    from pedidos.services import generar_descripcion_vino
    texto = generar_descripcion_vino(vino)
    return HttpResponse(texto)


@login_required
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

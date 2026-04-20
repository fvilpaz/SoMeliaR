from collections import defaultdict
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import send_mail
from django.contrib import messages

from .models import Pedido, LineaPedido
from .services import obtener_vinos_bajo_minimo, agrupar_por_proveedor, generar_texto_pedido


@login_required
def pedido_list(request):
    pedidos = Pedido.objects.select_related("proveedor").all()
    return render(request, "pedidos/pedido_list.html", {"pedidos": pedidos})


@login_required
def analizar_stock(request):
    """Analiza el stock, genera pedidos borrador agrupados por proveedor."""
    if request.method == "POST":
        bajo_minimo = obtener_vinos_bajo_minimo()
        if not bajo_minimo:
            messages.info(request, "¡Todo en orden! No hay vinos bajo mínimo.")
            return redirect("core:dashboard")

        grupos, sin_proveedor = agrupar_por_proveedor(bajo_minimo)

        pedidos_creados = 0
        for grupo in grupos:
            proveedor = grupo["proveedor"]
            lineas_data = grupo["lineas"]

            texto = generar_texto_pedido(proveedor, lineas_data)

            pedido = Pedido.objects.create(
                proveedor=proveedor,
                estado=Pedido.Estado.BORRADOR,
                generado_por_ia=True,
                texto_ia=texto,
            )
            for item in lineas_data:
                LineaPedido.objects.create(
                    pedido=pedido,
                    vino=item["vino"],
                    cantidad_sugerida=item["cantidad_sugerida"],
                    precio_unitario=item["precio"],
                )
            pedidos_creados += 1

        messages.success(
            request,
            f"Análisis completado. Se han generado {pedidos_creados} pedido(s) borrador."
        )
        if sin_proveedor:
            nombres = ", ".join(str(item["vino"]) for item in sin_proveedor)
            messages.warning(
                request,
                f"Los siguientes vinos no tienen proveedor asignado: {nombres}"
            )
        return redirect("pedidos:pedido_list")

    bajo_minimo = obtener_vinos_bajo_minimo()
    grupos, sin_proveedor = agrupar_por_proveedor(bajo_minimo)
    context = {
        "bajo_minimo": bajo_minimo,
        "grupos": grupos,
        "sin_proveedor": sin_proveedor,
    }
    return render(request, "pedidos/analizar_stock.html", context)


@login_required
def pedido_detail(request, pk):
    pedido = get_object_or_404(Pedido.objects.select_related("proveedor"), pk=pk)
    lineas = pedido.lineas.select_related("vino").all()

    if request.method == "POST":
        for linea in lineas:
            key = f"cantidad_{linea.pk}"
            if key in request.POST:
                try:
                    linea.cantidad_final = int(request.POST[key])
                    linea.save()
                except (ValueError, TypeError):
                    pass

        if pedido.estado == Pedido.Estado.BORRADOR:
            pedido.estado = Pedido.Estado.PENDIENTE
            pedido.save()
            messages.success(request, "Pedido actualizado y marcado como pendiente de envío.")

        return redirect("pedidos:pedido_detail", pk=pedido.pk)

    context = {
        "pedido": pedido,
        "lineas": lineas,
    }
    return render(request, "pedidos/pedido_detail.html", context)


@login_required
def pedido_recibir(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    if request.method == "POST" and pedido.estado == Pedido.Estado.ENVIADO:
        pedido.estado = Pedido.Estado.RECIBIDO
        pedido.save()
        messages.success(request, f"Pedido #{pedido.pk} marcado como recibido.")
    return redirect("pedidos:pedido_detail", pk=pedido.pk)


@login_required
def pedido_historico(request):
    """Histórico de pedidos enviados agrupado por año y mes."""
    pedidos = (
        Pedido.objects
        .filter(estado__in=[Pedido.Estado.ENVIADO, Pedido.Estado.RECIBIDO])
        .select_related("proveedor")
        .prefetch_related("lineas")
        .order_by("-fecha_creacion")
    )

    # Agrupar por año → mes
    por_anio = defaultdict(lambda: defaultdict(list))
    for p in pedidos:
        anio = p.fecha_creacion.year
        mes = p.fecha_creacion.month
        por_anio[anio][mes].append(p)

    # Calcular totales por mes y año
    MESES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    resumen = []
    for anio in sorted(por_anio.keys(), reverse=True):
        meses_data = []
        total_anio = Decimal("0")
        for mes in sorted(por_anio[anio].keys(), reverse=True):
            lista = por_anio[anio][mes]
            total_mes = sum(p.total for p in lista)
            total_anio += total_mes
            meses_data.append({
                "mes": mes,
                "nombre_mes": MESES[mes],
                "pedidos": lista,
                "total": total_mes,
                "count": len(lista),
            })
        resumen.append({
            "anio": anio,
            "meses": meses_data,
            "total_anio": total_anio,
        })

    return render(request, "pedidos/pedido_historico.html", {"resumen": resumen})


@login_required
def pedido_enviar(request, pk):
    """Envía el pedido por email al proveedor."""
    pedido = get_object_or_404(Pedido, pk=pk)

    if request.method == "POST" and pedido.estado in (
        Pedido.Estado.BORRADOR, Pedido.Estado.PENDIENTE
    ):
        lineas = pedido.lineas.select_related("vino").all()
        lineas_data = []
        for linea in lineas:
            lineas_data.append({
                "vino": str(linea.vino),
                "cantidad": linea.cantidad_final or linea.cantidad_sugerida,
                "precio": linea.precio_unitario,
            })

        texto_final = generar_texto_pedido(pedido.proveedor, lineas_data)

        send_mail(
            subject=f"Pedido de Bodega #{pedido.pk} — SoMeliaR",
            message=texto_final,
            from_email=request.user.email,
            recipient_list=[pedido.proveedor.email],
        )

        pedido.estado = Pedido.Estado.ENVIADO
        pedido.texto_ia = texto_final
        pedido.save()

        messages.success(
            request,
            f"Pedido #{pedido.pk} enviado a {pedido.proveedor.email} correctamente."
        )
    return redirect("pedidos:pedido_detail", pk=pedido.pk)

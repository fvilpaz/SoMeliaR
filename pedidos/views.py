from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings

from .models import Pedido, LineaPedido
from .services import obtener_vinos_bajo_minimo, agrupar_por_proveedor, generar_texto_pedido


def pedido_list(request):
    pedidos = Pedido.objects.select_related("proveedor").all()
    return render(request, "pedidos/pedido_list.html", {"pedidos": pedidos})


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

            # Generar texto IA
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

    # GET: mostrar vista previa del análisis
    bajo_minimo = obtener_vinos_bajo_minimo()
    grupos, sin_proveedor = agrupar_por_proveedor(bajo_minimo)
    context = {
        "bajo_minimo": bajo_minimo,
        "grupos": grupos,
        "sin_proveedor": sin_proveedor,
    }
    return render(request, "pedidos/analizar_stock.html", context)


def pedido_detail(request, pk):
    pedido = get_object_or_404(Pedido.objects.select_related("proveedor"), pk=pk)
    lineas = pedido.lineas.select_related("vino").all()

    if request.method == "POST":
        # Actualizar cantidades finales
        for linea in lineas:
            key = f"cantidad_{linea.pk}"
            if key in request.POST:
                try:
                    linea.cantidad_final = int(request.POST[key])
                    linea.save()
                except (ValueError, TypeError):
                    pass

        # Cambiar estado a pendiente si estaba en borrador
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


def pedido_enviar(request, pk):
    """Envía el pedido por email al proveedor."""
    pedido = get_object_or_404(Pedido, pk=pk)

    if request.method == "POST" and pedido.estado in (
        Pedido.Estado.BORRADOR, Pedido.Estado.PENDIENTE
    ):
        # Regenerar texto con cantidades finales
        lineas = pedido.lineas.select_related("vino").all()
        lineas_data = []
        for linea in lineas:
            lineas_data.append({
                "vino": str(linea.vino),
                "cantidad": linea.cantidad_final or linea.cantidad_sugerida,
                "precio": linea.precio_unitario,
            })

        texto_final = generar_texto_pedido(pedido.proveedor, lineas_data)

        # Enviar email (en demo sale por consola)
        send_mail(
            subject=f"Pedido de Bodega #{pedido.pk} — SoMeliaR",
            message=texto_final,
            from_email=settings.DEFAULT_FROM_EMAIL,
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

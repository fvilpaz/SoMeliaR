from decimal import Decimal

import io
import re
import time
import tempfile
import os
import requests as http_requests

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
from .forms import RegistroForm, PerfilForm, AvatarForm
from .models import Anotacion, PerfilUsuario, Configuracion


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
        "vinos_sin_imagen": Vino.objects.filter(activo=True, imagen="").count(),
    }

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "borrar_imagenes":
            vinos_con_imagen = Vino.objects.exclude(imagen="")
            count = 0
            for v in vinos_con_imagen:
                if v.imagen:
                    v.imagen.delete(save=False)
                    v.imagen = ""
                    v.save(update_fields=["imagen"])
                    count += 1
            messages.success(request, f"{count} imágenes eliminadas. Puedes volver a escanear.")
            return redirect("core:herramientas")

        elif accion == "limpiar":
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
                messages.error(request, "Selecciona un archivo.")
                return redirect("core:herramientas")

            nombre = archivo.name.lower()
            if nombre.endswith(".xlsx"):
                sufijo = ".xlsx"
            elif nombre.endswith(".xls"):
                sufijo = ".xls"
            else:
                messages.error(request, "Formato no soportado. Usa .xls o .xlsx (Excel / LibreOffice / OpenOffice).")
                return redirect("core:herramientas")

            with tempfile.NamedTemporaryFile(suffix=sufijo, delete=False) as tmp:
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

        elif accion == "logo":
            config = Configuracion.get()
            if request.FILES.get("logo"):
                config.logo = request.FILES["logo"]
                config.save()
                messages.success(request, "Logo actualizado.")
            return redirect("core:herramientas")

        elif accion == "login_imagen":
            config = Configuracion.get()
            if request.FILES.get("login_imagen"):
                config.login_imagen = request.FILES["login_imagen"]
                config.save()
                messages.success(request, "Imagen de login actualizada.")
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
    perfil_obj, _ = PerfilUsuario.objects.get_or_create(user=request.user)

    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "avatar":
            avatar_form = AvatarForm(request.POST, request.FILES, instance=perfil_obj)
            if avatar_form.is_valid():
                avatar_form.save()
                messages.success(request, "Foto de perfil actualizada.")
            return redirect("core:perfil")
        else:
            form = PerfilForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, "Perfil actualizado correctamente.")
                return redirect("core:perfil")
            avatar_form = AvatarForm(instance=perfil_obj)
            return render(request, "registration/profile.html", {"form": form, "avatar_form": avatar_form})

    form = PerfilForm(instance=request.user)
    avatar_form = AvatarForm(instance=perfil_obj)
    return render(request, "registration/profile.html", {"form": form, "avatar_form": avatar_form})


@login_required
@require_POST
def escanear_imagenes(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Solo superusuarios.")

    try:
        from duckduckgo_search import DDGS
    except ImportError:
        messages.error(request, "Librería duckduckgo-search no instalada.")
        return redirect("core:herramientas")

    limite = int(request.POST.get("limite", 10))
    vinos = list(Vino.objects.filter(activo=True, imagen="").order_by("nombre")[:limite])

    ok, sin_resultado = 0, 0
    log = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9",
    }

    _og_patterns = [
        re.compile(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](https?://[^"\'> ]+)', re.I),
        re.compile(r'<meta[^>]+content=["\'](https?://[^"\'> ]+)["\'][^>]+property=["\']og:image["\']', re.I),
        re.compile(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\'](https?://[^"\'> ]+)', re.I),
    ]
    _STOPWORDS = {'el', 'la', 'los', 'las', 'de', 'del', 'y', 'e', 'vino', 'wine', 'bodegas', 'bodega'}

    def _confianza(nombre_vino, bodega, titulo, url):
        """Puntuación 0-1 de coincidencia entre el resultado y el vino buscado."""
        haystack = (titulo + " " + url).lower()
        # Palabras del nombre (sin año ni stopwords)
        nombre_limpio = re.sub(r'\b(19|20)\d{2}\b', '', nombre_vino).lower()
        palabras = [w for w in nombre_limpio.split() if w not in _STOPWORDS and len(w) > 2]
        if not palabras:
            return 0.0
        hits_nombre = sum(1 for w in palabras if w in haystack)
        score = hits_nombre / len(palabras)
        # Bonus si aparece la bodega
        if bodega:
            bodega_words = [w for w in bodega.lower().split() if w not in _STOPWORDS and len(w) > 2]
            if bodega_words and any(w in haystack for w in bodega_words):
                score += 0.3
        # Bonus si el año del vino también aparece
        anyo = re.search(r'\b(19|20)\d{2}\b', nombre_vino)
        if anyo and anyo.group() in haystack:
            score += 0.2
        return min(score, 1.0)

    def _og_de_pagina(url):
        try:
            r = http_requests.get(url, timeout=5, headers=headers)
            if r.status_code == 200:
                for pat in _og_patterns:
                    m = pat.search(r.text)
                    if m:
                        return m.group(1)
        except Exception:
            pass
        return None

    def _guardar(vino, img_url):
        try:
            r = http_requests.get(img_url, timeout=8, headers=headers)
            if r.status_code == 200 and len(r.content) > 4000:
                ext = img_url.split("?")[0].rsplit(".", 1)[-1].lower()
                if ext not in ("jpg", "jpeg", "png", "webp", "gif"):
                    ext = "jpg"
                from django.core.files.base import ContentFile
                vino.imagen.save(f"{vino.pk}_scan.{ext}", ContentFile(r.content), save=True)
                return True
        except Exception:
            pass
        return False

    for vino in vinos:
        nombre_sin_anyo = re.sub(r'\b(19|20)\d{2}\b', '', vino.nombre).strip()
        partes_query = [p for p in [nombre_sin_anyo, vino.bodega_nombre] if p]
        base_query = " ".join(partes_query)
        descargado = False
        fuente_usada = None

        time.sleep(2)  # evitar rate limit entre vinos

        try:
            with DDGS() as ddgs:
                resultados = list(ddgs.text(
                    f"{base_query} vino comprar",
                    max_results=8,
                    region="es-es",
                ))
        except Exception as exc:
            log.append(f"✗ {nombre_sin_anyo} — error búsqueda: {exc}")
            sin_resultado += 1
            continue

        for r in resultados:
            titulo = r.get("title", "")
            href = r.get("href", "")
            if not href:
                continue

            # Solo guardar si el resultado coincide con suficiente confianza
            score = _confianza(vino.nombre, vino.bodega_nombre or "", titulo, href)
            if score < 0.6:
                continue

            og = _og_de_pagina(href)
            if og and _guardar(vino, og):
                ok += 1
                descargado = True
                dominio = href.split("/")[2] if "/" in href else href
                fuente_usada = f"{dominio} ({score:.0%})"
                break

        if descargado:
            log.append(f"✓ {nombre_sin_anyo} ({fuente_usada})")
        else:
            sin_resultado += 1
            log.append(f"✗ {nombre_sin_anyo}")

    pendientes = Vino.objects.filter(activo=True, imagen="").count()
    resumen = f"Escaneo completado — {ok} descargadas, {sin_resultado} sin resultado, {pendientes} pendientes."
    if log:
        resumen += " | " + " · ".join(log)
    if ok:
        messages.success(request, resumen)
    else:
        messages.warning(request, resumen)
    return redirect("core:herramientas")



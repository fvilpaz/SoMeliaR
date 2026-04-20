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

    scan_state = cache.get(SCAN_KEY)
    return render(request, "herramientas.html", {"stats": stats, "scan_state": scan_state})


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


import threading
from django.core.cache import cache

SCAN_KEY = "wine_scan_state"

_SCAN_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
_OG_PATS = [
    re.compile(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](https?://[^"\'> ]+)', re.I),
    re.compile(r'<meta[^>]+content=["\'](https?://[^"\'> ]+)["\'][^>]+property=["\']og:image["\']', re.I),
    re.compile(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\'](https?://[^"\'> ]+)', re.I),
]
_STOPWORDS = {'el','la','los','las','de','del','y','e','vino','wine','bodegas','bodega'}


def _guardar_imagen_vino(vino, img_url):
    try:
        r = http_requests.get(img_url, timeout=8, headers=_SCAN_HEADERS)
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


def _scan_worker(vino_pks):
    """Corre en hilo secundario. Actualiza cache con el progreso."""
    for i, pk in enumerate(vino_pks):
        state = cache.get(SCAN_KEY) or {}
        if state.get("cancelar"):
            state["status"] = "cancelado"
            cache.set(SCAN_KEY, state, 3600)
            return

        try:
            vino = Vino.objects.get(pk=pk)
        except Vino.DoesNotExist:
            continue

        nombre_limpio = re.sub(r'\b(19|20)\d{2}\b', '', vino.nombre).strip()
        # Query completo: nombre con año + bodega (si es distinta) + DO
        partes = [vino.nombre]
        if vino.bodega_nombre and vino.bodega_nombre.lower() not in vino.nombre.lower():
            partes.append(vino.bodega_nombre)
        if vino.denominacion_origen:
            partes.append(vino.denominacion_origen)
        query = " ".join(partes)

        state["progreso"] = i + 1
        state["procesando"] = vino.nombre
        cache.set(SCAN_KEY, state, 3600)

        descargado = False
        time.sleep(3)  # pausa necesaria para evitar rate limit de DDG

        exc_msg = ""
        try:
            from duckduckgo_search import DDGS
            ddgs = DDGS()
            resultados = list(ddgs.text(
                f"{query} vino",
                max_results=4,
                region="es-es",
            ))
            for res in resultados:
                href = res.get("href", "")
                if not href:
                    continue
                # Extraer og:image de la página del producto (foto oficial)
                try:
                    r = http_requests.get(href, timeout=5, headers=_SCAN_HEADERS)
                    if r.status_code == 200:
                        for pat in _OG_PATS:
                            m = pat.search(r.text)
                            if m:
                                img_url = m.group(1)
                                if _guardar_imagen_vino(vino, img_url):
                                    descargado = True
                                    break
                except Exception:
                    pass
                if descargado:
                    break
        except Exception as exc:
            exc_msg = f" [{str(exc)[:60]}]"

        state = cache.get(SCAN_KEY) or {}
        if descargado:
            state["ok"] = state.get("ok", 0) + 1
            state.setdefault("log", []).insert(0, f"✓ {nombre_limpio}")
        else:
            state["sin_resultado"] = state.get("sin_resultado", 0) + 1
            state.setdefault("log", []).insert(0, f"✗ {nombre_limpio}{exc_msg}")
        cache.set(SCAN_KEY, state, 3600)

    state = cache.get(SCAN_KEY) or {}
    state["status"] = "done"
    state["procesando"] = ""
    cache.set(SCAN_KEY, state, 3600)


@login_required
@require_POST
def escanear_imagenes(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Solo superusuarios.")

    # Cancelar si se pide
    if request.POST.get("cancelar"):
        state = cache.get(SCAN_KEY) or {}
        state["cancelar"] = True
        cache.set(SCAN_KEY, state, 3600)
        return redirect("core:herramientas")

    # No lanzar dos a la vez
    state = cache.get(SCAN_KEY) or {}
    if state.get("status") == "running":
        messages.warning(request, "Ya hay un escaneo en curso.")
        return redirect("core:herramientas")

    vinos = list(Vino.objects.filter(activo=True, imagen="").order_by("nombre"))

    if not vinos:
        messages.info(request, "Todos los vinos ya tienen foto.")
        return redirect("core:herramientas")

    cache.set(SCAN_KEY, {
        "status": "running",
        "total": len(vinos),
        "progreso": 0,
        "ok": 0,
        "sin_resultado": 0,
        "procesando": "",
        "log": [],
        "cancelar": False,
    }, 7200)

    t = threading.Thread(target=_scan_worker, args=([v.pk for v in vinos],), daemon=True)
    t.start()

    return redirect("core:herramientas")


@login_required
def escanear_estado(request):
    state = cache.get(SCAN_KEY) or {"status": "idle"}
    return JsonResponse(state)



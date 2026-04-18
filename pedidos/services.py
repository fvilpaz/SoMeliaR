"""
Servicio de análisis de stock e integración con IA (Google Gemini).

Si GEMINI_API_KEY está configurada, usa Gemini para redactar pedidos.
Si no, usa un generador local como fallback.
"""
import logging
from decimal import Decimal
from datetime import datetime

from django.conf import settings
from django.db.models import Sum, DecimalField, Value
from django.db.models.functions import Coalesce

from bodega.models import Vino, StockConfig
from proveedores.models import VinoProveedor

logger = logging.getLogger(__name__)


def obtener_vinos_bajo_minimo():
    """Devuelve lista de dicts con vinos cuyo stock está bajo el mínimo."""
    # Una query: configs + vinos + stock calculado
    configs = list(
        StockConfig.objects
        .filter(vino__activo=True)
        .select_related("vino")
        .annotate(
            stock_calculado=Coalesce(
                Sum("vino__movimientos__cantidad"),
                Value(Decimal("0")),
                output_field=DecimalField(),
            )
        )
    )

    bajo_minimo = [c for c in configs if c.stock_calculado < c.stock_minimo]
    if not bajo_minimo:
        return []

    # Una sola query para obtener proveedores de todos los vinos afectados
    vino_ids = [c.vino_id for c in bajo_minimo]
    vp_map = {
        vp.vino_id: vp
        for vp in VinoProveedor.objects.filter(
            vino_id__in=vino_ids, es_principal=True
        ).select_related("proveedor")
    }

    return [
        {
            "vino": c.vino,
            "stock_actual": c.stock_calculado,
            "stock_minimo": c.stock_minimo,
            "stock_optimo": c.stock_optimo,
            "cantidad_sugerida": max(
                0, int((c.stock_optimo - c.stock_calculado).to_integral_value())
            ),
            "proveedor": vp_map[c.vino_id].proveedor if c.vino_id in vp_map else None,
            "precio": vp_map[c.vino_id].precio if c.vino_id in vp_map else c.vino.precio_coste,
        }
        for c in bajo_minimo
    ]


# ---------------------------------------------------------------------------
# Generación de texto del pedido
# ---------------------------------------------------------------------------

def _construir_datos_pedido(proveedor, lineas):
    """Construye el resumen de datos del pedido como texto plano."""
    fecha = datetime.now().strftime("%d/%m/%Y")
    resumen = f"Fecha: {fecha}\n"
    resumen += f"Proveedor: {proveedor.nombre}\n"
    resumen += f"Email proveedor: {proveedor.email}\n"
    resumen += f"Contacto: {proveedor.contacto or 'N/A'}\n\n"
    resumen += "Productos a pedir:\n"

    total = 0
    for linea in lineas:
        cant = linea.get("cantidad", linea.get("cantidad_sugerida", 0))
        precio = linea.get("precio", 0)
        subtotal = cant * float(precio)
        total += subtotal
        resumen += f"- {linea['vino']}: {cant} unidades a {precio}€/ud (subtotal: {subtotal:.2f}€)\n"

    resumen += f"\nTotal estimado: {total:.2f}€"
    return resumen, total


def _generar_con_gemini(proveedor, lineas):
    """Genera el texto del pedido usando Google Gemini."""
    import google.generativeai as genai

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(settings.GEMINI_MODEL)

    datos, total = _construir_datos_pedido(proveedor, lineas)

    prompt = (
        "Eres el asistente de bodega de un Beach Club de lujo. "
        "Redacta un email de pedido formal pero cercano en español para enviar "
        "al proveedor con los siguientes datos. "
        "Incluye un saludo profesional, la lista detallada de productos con "
        "cantidades y precios, el total estimado, y una despedida pidiendo "
        "confirmación de disponibilidad y plazos de entrega. "
        "Firma como 'Equipo de Bodega — SoMeliaR'.\n\n"
        f"DATOS DEL PEDIDO:\n{datos}"
    )

    response = model.generate_content(prompt)
    return response.text


def _generar_mock(proveedor, lineas):
    """Genera texto de pedido localmente sin IA (fallback)."""
    datos, total = _construir_datos_pedido(proveedor, lineas)
    fecha = datetime.now().strftime("%d/%m/%Y")

    texto = f"PEDIDO DE BODEGA — {fecha}\n"
    texto += f"Proveedor: {proveedor.nombre}\n"
    texto += f"Contacto: {proveedor.contacto or proveedor.email}\n"
    texto += "=" * 50 + "\n\n"

    total = 0
    for linea in lineas:
        cant = linea.get("cantidad", linea.get("cantidad_sugerida", 0))
        precio = linea.get("precio", 0)
        subtotal = cant * float(precio)
        total += subtotal
        texto += f"• {linea['vino']} — {cant} uds. x {precio}€ = {subtotal:.2f}€\n"

    texto += f"\n{'=' * 50}\n"
    texto += f"TOTAL ESTIMADO: {total:.2f}€\n\n"
    texto += (
        "Este pedido ha sido generado automáticamente por el sistema de gestión "
        "de bodega SoMeliaR. Por favor, confirme disponibilidad y plazos de entrega.\n\n"
        "Un saludo,\nEl equipo de Bodega"
    )
    return texto


def generar_texto_pedido(proveedor, lineas):
    """
    Genera el texto del pedido.

    Si hay GEMINI_API_KEY configurada, usa Google Gemini.
    Si no, usa el generador local (mock).
    """
    if settings.GEMINI_API_KEY:
        try:
            texto = _generar_con_gemini(proveedor, lineas)
            logger.info("Texto de pedido generado con Gemini")
            return texto
        except Exception as e:
            logger.warning("Error con Gemini, usando fallback: %s", e)
            return _generar_mock(proveedor, lineas)
    else:
        logger.info("Sin GEMINI_API_KEY, usando generador local")
        return _generar_mock(proveedor, lineas)


def agrupar_por_proveedor(vinos_bajo_minimo):
    """Agrupa los vinos bajo mínimo por proveedor."""
    grupos = {}
    sin_proveedor = []
    for item in vinos_bajo_minimo:
        prov = item["proveedor"]
        if prov is None:
            sin_proveedor.append(item)
        else:
            if prov.pk not in grupos:
                grupos[prov.pk] = {"proveedor": prov, "lineas": []}
            grupos[prov.pk]["lineas"].append(item)
    return list(grupos.values()), sin_proveedor

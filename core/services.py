"""
Asistente de voz — interpreta comandos en lenguaje natural y ejecuta acciones.

Usa Gemini para entender frases como:
  - "He vendido 2 botellas de Protos Crianza"
  - "Han entrado 6 Albariño"
  - "¿Cuánto queda de Muga Rosado?"
  - "Pon 3 botellas de salida del Krug"
"""
import json
import logging
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db.models import Q

from bodega.models import Movimiento, Vino

logger = logging.getLogger(__name__)

# Lista de nombres de vinos para el prompt (se cachea)
_vinos_cache = None


def _get_vinos_nombres():
    """Devuelve lista de nombres de vinos activos para el prompt."""
    global _vinos_cache
    if _vinos_cache is None:
        _vinos_cache = list(
            Vino.objects.filter(activo=True)
            .values_list("nombre", flat=True)
        )
    return _vinos_cache


def invalidar_cache_vinos():
    """Invalida el caché de nombres (llamar al añadir/borrar vinos)."""
    global _vinos_cache
    _vinos_cache = None


def _buscar_vino(nombre_buscado):
    """Busca un vino por nombre fuzzy."""
    if not nombre_buscado:
        return None

    nombre = nombre_buscado.strip().lower()

    # Búsqueda exacta (case-insensitive)
    vino = Vino.objects.filter(nombre__iexact=nombre_buscado).first()
    if vino:
        return vino

    # Búsqueda por contenido
    vino = Vino.objects.filter(nombre__icontains=nombre_buscado).first()
    if vino:
        return vino

    # Búsqueda por palabras clave
    palabras = nombre.split()
    if palabras:
        q = Q()
        for palabra in palabras:
            if len(palabra) > 2:
                q &= Q(nombre__icontains=palabra)
        if q:
            vino = Vino.objects.filter(q).first()
            if vino:
                return vino

    return None


def interpretar_comando(texto):
    """
    Interpreta un comando de voz y devuelve la acción a ejecutar.

    Returns dict con:
        - tipo: "venta" | "entrada" | "ajuste" | "consulta" | "error"
        - vino_nombre: nombre del vino mencionado
        - cantidad: número de botellas
        - mensaje: respuesta para el usuario
    """
    if not texto or not texto.strip():
        return {
            "tipo": "error",
            "mensaje": "No he entendido nada. ¿Puedes repetir?",
        }

    # Intentar con Gemini
    if settings.GEMINI_API_KEY:
        try:
            return _interpretar_con_gemini(texto)
        except Exception as e:
            logger.warning("Error con Gemini en asistente: %s", e)
            return _interpretar_local(texto)
    else:
        return _interpretar_local(texto)


def _interpretar_con_gemini(texto, intentos=2):
    """Usa Gemini para interpretar el comando, con reintentos en 429."""
    import time
    import google.generativeai as genai
    from google.api_core.exceptions import ResourceExhausted

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(settings.GEMINI_MODEL)

    vinos = _get_vinos_nombres()

    prompt = f"""Eres el asistente de voz de una bodega de un Beach Club. Interpretas comandos del sumiller.

IMPORTANTE: El texto viene de reconocimiento de voz y puede tener ERRORES de transcripción.
Por ejemplo: "elisia" = "ELYSSIA", "recaredo" = "Recaredo Terrers", "crup" = "Krug", etc.
Debes buscar el vino MAS PARECIDO fonéticamente aunque esté mal escrito.

VINOS EN LA BODEGA:
{chr(10).join(f'- {v}' for v in vinos)}

COMANDO DEL SUMILLER: "{texto}"

Responde SOLO con JSON válido (sin markdown, sin ```):
{{
  "tipo": "venta" | "entrada" | "ajuste" | "consulta" | "desconocido",
  "vino_nombre": "nombre EXACTO de la lista de arriba (copiado tal cual)",
  "cantidad": numero (1 si no se menciona),
  "mensaje": "respuesta breve en español"
}}

Acciones:
- vendido/venta/salida/quita/sacado → "venta"
- entrado/entrada/recibido/llegaron/añade/pon → "entrada"
- cuánto queda/stock/cuántas hay → "consulta"
- ajuste/corrige → "ajuste"
"""

    for intento in range(intentos):
        try:
            response = model.generate_content(prompt)
            raw = response.text.strip()
            break
        except ResourceExhausted as e:
            # Extraer tiempo de espera del error
            wait = 15  # default
            err_str = str(e)
            if "retry_delay" in err_str:
                import re
                m = re.search(r'seconds:\s*(\d+)', err_str)
                if m:
                    wait = int(m.group(1)) + 1
            if intento < intentos - 1:
                logger.info("Gemini 429, reintentando en %ds...", wait)
                time.sleep(wait)
            else:
                raise

    # Limpiar posibles marcadores markdown
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:])
    if raw.endswith("```"):
        raw = raw[:-3]
    if raw.startswith("json"):
        raw = raw[4:]
    raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Gemini devolvió JSON inválido: %s", raw)
        return {
            "tipo": "error",
            "mensaje": "No he podido interpretar la respuesta. ¿Puedes repetir?",
        }

    return {
        "tipo": data.get("tipo", "desconocido"),
        "vino_nombre": data.get("vino_nombre", ""),
        "cantidad": data.get("cantidad", 1),
        "mensaje": data.get("mensaje", ""),
    }


def _interpretar_local(texto):
    """Interpretación local sin IA. Intenta encontrar el vino por coincidencia."""
    import re

    texto_lower = texto.lower()

    # Detectar tipo
    tipo = "desconocido"
    if any(w in texto_lower for w in ["vendido", "venta", "salida", "quita", "sacado"]):
        tipo = "venta"
    elif any(w in texto_lower for w in ["entrada", "entrado", "recibido", "llegaron", "añade", "pon"]):
        tipo = "entrada"
    elif any(w in texto_lower for w in ["cuánto", "cuanto", "stock", "queda", "hay"]):
        tipo = "consulta"

    # Extraer cantidad (buscar números en el texto)
    cantidad = 1
    nums = re.findall(r'(\d+(?:[.,]\d+)?)', texto)
    if nums:
        cantidad = float(nums[0].replace(',', '.'))

    # Intentar encontrar el vino por coincidencia de palabras
    # Quitar palabras comunes para quedarnos con el nombre del vino
    palabras_comunes = {
        "he", "ha", "han", "vendido", "venta", "salida", "quita", "sacado",
        "entrada", "entrado", "recibido", "llegaron", "añade", "pon",
        "cuánto", "cuanto", "stock", "queda", "hay", "botellas", "botella",
        "de", "del", "la", "el", "las", "los", "un", "una", "unos", "unas",
        "por", "para", "con", "y", "que", "se", "me", "le", "a", "en",
        "dos", "tres", "cuatro", "cinco", "seis",
    }
    palabras = [p for p in texto_lower.split() if p not in palabras_comunes and len(p) > 1]

    vino_encontrado = None
    if palabras:
        # Buscar vinos que contengan alguna de las palabras
        mejor_score = 0
        for vino in Vino.objects.filter(activo=True):
            nombre_lower = vino.nombre.lower()
            score = sum(1 for p in palabras if p in nombre_lower)
            if score > mejor_score:
                mejor_score = score
                vino_encontrado = vino

    if vino_encontrado and mejor_score > 0:
        return {
            "tipo": tipo,
            "vino_nombre": vino_encontrado.nombre,
            "cantidad": cantidad,
            "mensaje": f"(Sin IA) Creo que te refieres a {vino_encontrado.nombre}.",
        }

    return {
        "tipo": tipo,
        "vino_nombre": "",
        "cantidad": cantidad,
        "mensaje": "No he podido identificar el vino. La cuota de IA está agotada. Espera un momento e inténtalo de nuevo.",
    }


def _fmt(n):
    """Formatea un número: sin decimales si es entero, máx 2 si no."""
    valor = f"{float(n):.2f}".rstrip("0").rstrip(".")
    return valor


def ejecutar_comando(comando):
    """
    Ejecuta un comando interpretado. Busca el vino y realiza la acción.

    Returns dict con resultado y mensaje final.
    """
    tipo = comando.get("tipo", "desconocido")
    vino_nombre = comando.get("vino_nombre", "")
    cantidad = comando.get("cantidad", 1)

    # Consulta no necesita vino necesariamente
    if tipo == "consulta" and vino_nombre:
        vino = _buscar_vino(vino_nombre)
        if vino:
            stock = vino.stock_actual
            return {
                "ok": True,
                "tipo": "consulta",
                "vino": str(vino),
                "vino_id": vino.pk,
                "stock": float(stock),
                "mensaje": f"De {vino} quedan {_fmt(stock)} botellas en bodega.",
            }
        return {
            "ok": False,
            "tipo": "consulta",
            "mensaje": f"No encuentro el vino '{vino_nombre}' en la bodega.",
        }

    if tipo in ("venta", "entrada", "ajuste"):
        vino = _buscar_vino(vino_nombre)
        if not vino:
            return {
                "ok": False,
                "tipo": tipo,
                "mensaje": f"No encuentro el vino '{vino_nombre}'. ¿Puedes repetir el nombre?",
            }

        try:
            cant = Decimal(str(cantidad))
        except (InvalidOperation, ValueError):
            cant = Decimal("1")

        if tipo == "venta":
            cant_mov = -abs(cant)
            tipo_mov = Movimiento.Tipo.SALIDA
        elif tipo == "entrada":
            cant_mov = abs(cant)
            tipo_mov = Movimiento.Tipo.ENTRADA
        else:
            cant_mov = cant
            tipo_mov = Movimiento.Tipo.AJUSTE

        Movimiento.objects.create(
            vino=vino,
            tipo=tipo_mov,
            cantidad=cant_mov,
            notas=f"Registrado por asistente de voz",
        )

        nuevo_stock = vino.stock_actual
        accion = "Venta" if tipo == "venta" else "Entrada" if tipo == "entrada" else "Ajuste"

        return {
            "ok": True,
            "tipo": tipo,
            "vino": str(vino),
            "vino_id": vino.pk,
            "cantidad": float(abs(cant)),
            "stock_nuevo": float(nuevo_stock),
            "mensaje": f"✓ {accion} registrada: {_fmt(abs(cant))} × {vino}. Stock actual: {_fmt(nuevo_stock)}",
        }

    if tipo == "desconocido":
        return {
            "ok": False,
            "tipo": "desconocido",
            "mensaje": comando.get("mensaje", "No he entendido el comando. Prueba con algo como: 'He vendido 2 Protos Crianza'"),
        }

    return {
        "ok": False,
        "tipo": tipo,
        "mensaje": comando.get("mensaje", "No he podido ejecutar la acción."),
    }

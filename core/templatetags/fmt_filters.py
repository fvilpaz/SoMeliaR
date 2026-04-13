from django import template

register = template.Library()


@register.filter(name="fmt_num")
def fmt_num(value):
    """
    Formatea un número:
    - Si es entero (ej. 36.0) → "36"
    - Si tiene decimales (ej. 35.6) → "35.6"
    - Máximo 2 decimales, sin ceros finales.
    """
    try:
        return f"{float(value):.2f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return value

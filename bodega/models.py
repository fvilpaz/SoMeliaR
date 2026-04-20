from decimal import Decimal

from django.db import models
from django.db.models import Sum


class Etiqueta(models.Model):
    COLORES = [
        ("primary",   "Azul"),
        ("success",   "Verde"),
        ("danger",    "Rojo"),
        ("warning",   "Amarillo"),
        ("info",      "Cian"),
        ("secondary", "Gris"),
        ("dark",      "Negro"),
    ]
    nombre = models.CharField(max_length=50, unique=True)
    color  = models.CharField(max_length=20, choices=COLORES, default="secondary")

    class Meta:
        ordering = ["nombre"]
        verbose_name = "etiqueta"
        verbose_name_plural = "etiquetas"

    def __str__(self):
        return self.nombre


class Vino(models.Model):
    class Familia(models.TextChoices):
        ESPUMOSO_NAC = "espumoso_nac", "Burbujas Nacional"
        CHAMPAGNE = "champagne", "Champagne"
        ESPUMOSO_INT = "espumoso_int", "Burbujas Internacional (Otros)"
        BLANCO_NAC = "blanco_nac", "Blanco Nacional"
        BLANCO_INT = "blanco_int", "Blanco Internacional"
        TINTO_NAC = "tinto_nac", "Tinto Nacional"
        TINTO_INT = "tinto_int", "Tinto Internacional"
        GRANDES_TINTOS = "grandes_tintos", "Grandes Vinos Tintos"
        ROSADO = "rosado", "Rosado"
        DULCE = "dulce", "Dulce"
        GENEROSO = "generoso", "Generoso"
        FUERA_CARTA = "fuera_carta", "Fuera de Carta"
        PROPIEDAD = "propiedad", "Vinos de Propiedad"

    nombre = models.CharField(max_length=200)
    bodega_nombre = models.CharField("bodega", max_length=200, blank=True)
    anada = models.PositiveIntegerField("añada", null=True, blank=True)
    familia = models.CharField(max_length=20, choices=Familia.choices)
    azucar = models.CharField(
        "tipo/azúcar", max_length=100, blank=True,
        help_text="Ej: Brut, Brut Nature, Extra Brut, Rosado..."
    )
    denominacion_origen = models.CharField(
        "denominación de origen", max_length=200, blank=True
    )
    variedades = models.CharField(
        "variedades de uva", max_length=300, blank=True
    )
    precio_coste = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    precio_carta = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    # Venta por copas
    es_copa = models.BooleanField("se vende por copas", default=False)
    precio_copa = models.DecimalField(
        "precio copa en carta", max_digits=8, decimal_places=2, default=0
    )
    # Canal de compra
    via_coupa = models.BooleanField(
        "se pide por Coupa", default=False,
        help_text="Si True, se pide por el sistema corporativo Meliá."
    )
    # Ubicaciones donde se sirve
    en_canitas = models.BooleanField("Cañitas", default=False)
    en_ene = models.BooleanField("EÑE", default=False)
    en_pool = models.BooleanField("Pool", default=False)
    etiquetas = models.ManyToManyField(
        Etiqueta, blank=True, related_name="vinos", verbose_name="etiquetas"
    )
    imagen = models.ImageField(
        upload_to="vinos/", blank=True,
        help_text="Foto de la etiqueta o botella."
    )
    notas = models.TextField(blank=True)
    activo = models.BooleanField(default=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["familia", "nombre"]
        verbose_name = "vino"
        verbose_name_plural = "vinos"

    def __str__(self):
        txt = self.nombre
        if self.anada:
            txt += f" {self.anada}"
        return txt

    @property
    def stock_actual(self):
        if hasattr(self, "stock_anotado"):
            return self.stock_anotado
        total = self.movimientos.aggregate(total=Sum("cantidad"))["total"]
        return total or Decimal("0")

    @property
    def bajo_minimo(self):
        """True si el stock está por debajo del mínimo configurado."""
        try:
            return self.stock_actual < self.stock_config.stock_minimo
        except StockConfig.DoesNotExist:
            return False


class Movimiento(models.Model):
    class Tipo(models.TextChoices):
        ENTRADA = "entrada", "Entrada"
        SALIDA = "salida", "Salida"
        AJUSTE = "ajuste", "Ajuste"

    vino = models.ForeignKey(
        Vino, on_delete=models.CASCADE, related_name="movimientos"
    )
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    cantidad = models.DecimalField(
        max_digits=8, decimal_places=1,
        help_text="Positivo para entradas, negativo para salidas."
    )
    fecha = models.DateTimeField(auto_now_add=True)
    notas = models.TextField(blank=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "movimiento"
        verbose_name_plural = "movimientos"

    def __str__(self):
        signo = "+" if self.cantidad > 0 else ""
        return f"{self.vino} | {self.get_tipo_display()} {signo}{self.cantidad}"


class StockConfig(models.Model):
    vino = models.OneToOneField(
        Vino, on_delete=models.CASCADE, related_name="stock_config"
    )
    stock_minimo = models.PositiveIntegerField(default=6)
    stock_optimo = models.PositiveIntegerField(default=12)

    class Meta:
        verbose_name = "configuración de stock"
        verbose_name_plural = "configuraciones de stock"

    def __str__(self):
        return f"{self.vino} — mín: {self.stock_minimo}, ópt: {self.stock_optimo}"
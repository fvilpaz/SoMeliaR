from django.db import models


class Pedido(models.Model):
    class Estado(models.TextChoices):
        BORRADOR = "borrador", "Borrador"
        PENDIENTE = "pendiente", "Pendiente de revisión"
        ENVIADO = "enviado", "Enviado"
        RECIBIDO = "recibido", "Recibido"

    proveedor = models.ForeignKey(
        "proveedores.Proveedor",
        on_delete=models.CASCADE,
        related_name="pedidos",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.BORRADOR, db_index=True
    )
    generado_por_ia = models.BooleanField(default=False)
    texto_ia = models.TextField("texto generado por IA", blank=True)
    notas = models.TextField(blank=True)

    class Meta:
        ordering = ["-fecha_creacion"]
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"

    def __str__(self):
        return f"Pedido #{self.pk} — {self.proveedor} ({self.get_estado_display()})"

    @property
    def total(self):
        return sum(
            linea.precio_unitario * (linea.cantidad_final or linea.cantidad_sugerida)
            for linea in self.lineas.all()
        )


class LineaPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido, on_delete=models.CASCADE, related_name="lineas"
    )
    vino = models.ForeignKey(
        "bodega.Vino", on_delete=models.CASCADE, related_name="lineas_pedido"
    )
    cantidad_sugerida = models.PositiveIntegerField()
    cantidad_final = models.PositiveIntegerField(null=True, blank=True)
    precio_unitario = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        verbose_name = "línea de pedido"
        verbose_name_plural = "líneas de pedido"

    def __str__(self):
        cant = self.cantidad_final or self.cantidad_sugerida
        return f"{self.vino} x{cant}"

from django.db import models


class Proveedor(models.Model):
    nombre = models.CharField(max_length=200)
    email = models.EmailField()
    telefono = models.CharField(max_length=30, blank=True)
    contacto = models.CharField(
        "persona de contacto", max_length=200, blank=True
    )
    notas = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "proveedor"
        verbose_name_plural = "proveedores"

    def __str__(self):
        return self.nombre


class VinoProveedor(models.Model):
    vino = models.ForeignKey(
        "bodega.Vino", on_delete=models.CASCADE, related_name="vino_proveedores"
    )
    proveedor = models.ForeignKey(
        Proveedor, on_delete=models.CASCADE, related_name="vinos"
    )
    referencia = models.CharField(max_length=100, blank=True)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    es_principal = models.BooleanField(default=False)

    class Meta:
        verbose_name = "vino-proveedor"
        verbose_name_plural = "vinos-proveedores"
        unique_together = ["vino", "proveedor"]

    def __str__(self):
        return f"{self.vino} → {self.proveedor}"
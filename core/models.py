from django.db import models


class Anotacion(models.Model):
    class Prioridad(models.TextChoices):
        URGENTE  = "urgente",  "Urgente"
        MODERADO = "moderado", "Moderado"
        NORMAL   = "normal",   "Normal"

    texto     = models.TextField()
    prioridad = models.CharField(max_length=10, choices=Prioridad.choices, default=Prioridad.NORMAL)
    fecha     = models.DateTimeField(auto_now_add=True)
    resuelta  = models.BooleanField(default=False)

    class Meta:
        ordering = ["resuelta", "-fecha"]

    def __str__(self):
        return self.texto[:60]

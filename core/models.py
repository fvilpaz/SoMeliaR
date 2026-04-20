from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    avatar = models.ImageField(upload_to="avatares/", blank=True)
    foto_en_sidebar = models.BooleanField(default=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"


@receiver(post_save, sender=User)
def crear_perfil(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.get_or_create(user=instance)


class Configuracion(models.Model):
    """Singleton: configuración visual de la app (logo, imagen login)."""
    logo = models.ImageField(upload_to="config/", blank=True,
                             help_text="Logo del sidebar (cuadrado, mín. 200×200px)")
    login_imagen = models.ImageField(upload_to="config/", blank=True,
                                     help_text="Foto de la pantalla de login")

    class Meta:
        verbose_name = "configuración"

    def __str__(self):
        return "Configuración de la app"

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


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

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# En producción (DEBUG=False): migraciones, estáticos y carga inicial de datos
if os.environ.get("DEBUG", "True") == "False":
    import django
    django.setup()
    from django.core.management import call_command
    call_command("migrate", "--no-input")
    call_command("collectstatic", "--no-input")
    # Cargar datos iniciales si la base de datos está vacía
    try:
        from bodega.models import Vino
        if Vino.objects.count() == 0:
            call_command("loaddata", "fixtures/initial_data.json")
    except Exception:
        pass

application = get_wsgi_application()

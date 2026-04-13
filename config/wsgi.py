import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Cargar datos iniciales si la base de datos está vacía (solo en producción)
if os.environ.get("DEBUG", "True") == "False":
    try:
        import django
        django.setup()
        from bodega.models import Vino
        if Vino.objects.count() == 0:
            from django.core.management import call_command
            call_command("loaddata", "fixtures/initial_data.json")
    except Exception:
        pass

application = get_wsgi_application()

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# En producción (DEBUG=False): aplicar migraciones y estáticos al arrancar
if os.environ.get("DEBUG", "True") == "False":
    import django
    django.setup()
    from django.core.management import call_command
    call_command("migrate", "--no-input")
    call_command("collectstatic", "--no-input", "--clear")

application = get_wsgi_application()

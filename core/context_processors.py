from .models import Configuracion, PerfilUsuario


def app_config(request):
    config = Configuracion.get()
    perfil = None
    if request.user.is_authenticated:
        perfil, _ = PerfilUsuario.objects.get_or_create(user=request.user)
    return {"app_config": config, "user_perfil": perfil}

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from core.views import reset_tmp_x9k2

urlpatterns = [
    path("admin/", admin.site.urls),
    path("reset-tmp-x9k2/", reset_tmp_x9k2, name="reset_tmp"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("core.urls")),
    path("bodega/", include("bodega.urls")),
    path("proveedores/", include("proveedores.urls")),
    path("pedidos/", include("pedidos.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
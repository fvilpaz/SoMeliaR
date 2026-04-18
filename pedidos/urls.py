from django.urls import path
from . import views

app_name = "pedidos"

urlpatterns = [
    path("", views.pedido_list, name="pedido_list"),
    path("analizar/", views.analizar_stock, name="analizar_stock"),
    path("<int:pk>/", views.pedido_detail, name="pedido_detail"),
    path("<int:pk>/enviar/", views.pedido_enviar, name="pedido_enviar"),
    path("<int:pk>/recibir/", views.pedido_recibir, name="pedido_recibir"),
]

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Proveedor
from .forms import ProveedorForm


@login_required
def proveedor_list(request):
    proveedores = Proveedor.objects.filter(activo=True)
    return render(request, "proveedores/proveedor_list.html", {"proveedores": proveedores})


@login_required
def proveedor_detail(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    return render(request, "proveedores/proveedor_detail.html", {"proveedor": proveedor})


@login_required
def proveedor_create(request):
    if request.method == "POST":
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("proveedores:proveedor_list")
    else:
        form = ProveedorForm()
    return render(request, "proveedores/proveedor_form.html", {"form": form, "titulo": "Nuevo Proveedor"})


@login_required
def proveedor_edit(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == "POST":
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            return redirect("proveedores:proveedor_detail", pk=proveedor.pk)
    else:
        form = ProveedorForm(instance=proveedor)
    return render(request, "proveedores/proveedor_form.html", {"form": form, "titulo": "Editar Proveedor"})

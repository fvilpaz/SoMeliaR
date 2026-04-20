from django import forms
from .models import Etiqueta, Movimiento, Vino, StockConfig


class MovimientoForm(forms.ModelForm):
    class Meta:
        model = Movimiento
        fields = ["tipo", "cantidad", "notas"]
        widgets = {
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "cantidad": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "notas": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def clean_cantidad(self):
        cantidad = self.cleaned_data["cantidad"]
        if cantidad == 0:
            raise forms.ValidationError("La cantidad no puede ser 0.")
        return cantidad

    def save(self, commit=True):
        movimiento = super().save(commit=False)
        if movimiento.tipo == Movimiento.Tipo.SALIDA and movimiento.cantidad > 0:
            movimiento.cantidad = -movimiento.cantidad
        if commit:
            movimiento.save()
        return movimiento


class VinoForm(forms.ModelForm):
    stock_minimo = forms.IntegerField(
        min_value=0, initial=6, label="Stock mínimo",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    stock_optimo = forms.IntegerField(
        min_value=0, initial=12, label="Stock óptimo",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    stock_inicial = forms.DecimalField(
        min_value=0, initial=0, required=False, label="Stock inicial (uds.)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.5"}),
        help_text="Botellas que hay ahora mismo en bodega.",
    )

    class Meta:
        model = Vino
        fields = [
            "nombre", "bodega_nombre", "anada", "familia",
            "azucar", "denominacion_origen", "variedades",
            "precio_coste", "precio_carta",
            "es_copa", "precio_copa",
            "via_coupa", "en_canitas", "en_ene", "en_pool",
            "etiquetas",
            "imagen",
            "notas", "activo",
        ]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "bodega_nombre": forms.TextInput(attrs={"class": "form-control"}),
            "anada": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Ej: 2019"}),
            "familia": forms.Select(attrs={"class": "form-select"}),
            "azucar": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Brut, Crianza..."}),
            "denominacion_origen": forms.TextInput(attrs={"class": "form-control"}),
            "variedades": forms.TextInput(attrs={"class": "form-control"}),
            "precio_coste": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "precio_carta": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "precio_copa": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "notas": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            try:
                sc = self.instance.stock_config
                self.fields["stock_minimo"].initial = sc.stock_minimo
                self.fields["stock_optimo"].initial = sc.stock_optimo
            except StockConfig.DoesNotExist:
                pass
            # En edición no mostramos stock inicial (ya existe historial)
            self.fields["stock_inicial"].widget = forms.HiddenInput()
            self.fields["stock_inicial"].required = False

    def save(self, commit=True):
        vino = super().save(commit=commit)
        if commit:
            sc, _ = StockConfig.objects.get_or_create(vino=vino)
            sc.stock_minimo = self.cleaned_data["stock_minimo"]
            sc.stock_optimo = self.cleaned_data["stock_optimo"]
            sc.save()
        return vino

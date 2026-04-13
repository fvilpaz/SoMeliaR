from django import forms
from .models import Movimiento


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
        # Salidas se guardan como negativo
        if movimiento.tipo == Movimiento.Tipo.SALIDA and movimiento.cantidad > 0:
            movimiento.cantidad = -movimiento.cantidad
        if commit:
            movimiento.save()
        return movimiento
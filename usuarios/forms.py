from django import forms
from .models import Siembra

class SiembraForm(forms.ModelForm):
    class Meta:
        model = Siembra
        fields = ["producto", "cantidad", "fecha_siembra", "ubicacion"]
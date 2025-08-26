from django import forms
from .models import Sowing, Product, Municipality, Prices

class SowingForm(forms.ModelForm):
    class Meta:
        model = Sowing
        fields = ['product', 'quantity', 'sowing_date', 'municipality']
        labels = {
            'product': 'Producto',
            'quantity': 'Cantidad',
            'sowing_date': 'Fecha de siembra',
            'municipality': 'Municipio'
        }
        widgets = {
            'sowing_date': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.unit = 'hectarea'
        if commit:
            instance.save()
        return instance
            
class PriceForm(forms.ModelForm):
    UNIDADES = [
        ('k', 'kilo'),
        ('t', 'tonelada'),
        ('a', 'arroba')
    ]

    class Meta:
        model = Prices
        fields = ['value', 'date', 'product', 'unit', 'quantity']
        labels = {
            'product': 'Producto',
            'quantity': 'Cantidad',
            'unit': 'Unidad',
            'date': 'Fecha del Precio',
            'value': 'Valor'
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class ViabilityForm(forms.Form):
    municipality = forms.ModelChoiceField(queryset=Municipality.objects.all(), label='Municipio')
    sowing_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Fecha de Siembra')
    temperature_c = forms.FloatField(label="Temperatura (°C)", required=False, widget=forms.HiddenInput())
    rainfall_mm = forms.FloatField(label="Lluvia (mm)", required=False, widget=forms.HiddenInput())
    humidity_pct = forms.FloatField(label="Humedad (%)", required=False, widget=forms.HiddenInput())


    def get_conditions(self):
        return {
            'temperature_c': self.cleaned_data['temperature_c'],
            'rainfall_mm': self.cleaned_data['rainfall_mm'],
            'humidity_pct': self.cleaned_data['humidity_pct'],
        }

class PricePredictForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.all(), label='Producto')
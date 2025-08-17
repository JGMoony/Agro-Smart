from django import forms
from .models import Sowing, Product, Municipality

class SowingForm(forms.ModelForm):
    class Meta:
        model = Sowing
        fields = ['product', 'quantity', 'sowing_date', 'municipality', 'harvest_date', 'status']
        widgets = {
            'sowing_date': forms.DateInput(attrs={'type': 'date'}),
            'harvest_date': forms.DateInput(attrs={'type': 'date'}),
        }

class ViabilityForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.all())
    municipality = forms.ModelChoiceField(queryset=Municipality.objects.all())
    sowing_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

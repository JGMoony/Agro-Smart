from django import forms
from .models import User

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'password']
        
    def save(self, commit=True):
        user = super().save(commit=False)
        pdw = self.cleaned_data['password']
        user.set_password(pdw)
        if commit:
            user.save()
        return user
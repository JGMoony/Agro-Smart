from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from .forms import SignUpForm
from .forms import AdminUserCreationForm


class CustomLoginView(LoginView):
    template_name = "registration/login.html"

class CustomLogoutView(LogoutView):
    next_page = 'login'

class RegisterView(View):
    def get(self, request):
        form = SignUpForm()
        return render(request, 'registration/register.html', {'form': form})

    def post(self, request):
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
        return render(request, 'registration/register.html', {'form': form})
    
def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

@method_decorator([login_required, user_passes_test(is_admin)], name='dispatch')
class AdminUserCreateView(View):
    def get(self, request):
        form = AdminUserCreationForm()
        return render(request, 'users/admin_user_create.html', {'form': form})

    def post(self, request):
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')  # o donde prefieras
        return render(request, 'registration/admin_user_create.html', {'form': form})

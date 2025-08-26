from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Vista Home
@login_required
def home(request):
    return render(request, "home.html")

urlpatterns = [
    path("admin/", admin.site.urls),

    # Login y logout
    path("", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # Home
    # urls.py
    path("home/", home, name="home"),


    # Apps
    path("crops/", include("crops.urls")),
    path("weather/", include("weather.urls")),
    path("users/", include("users.urls")),
]

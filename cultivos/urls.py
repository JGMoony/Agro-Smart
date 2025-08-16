from django.urls import path
from . import views

urlpatterns = [
    path("", views.lista_siembras, name="lista_siembras"),
    path("crear/", views.crear_siembra, name="crear_siembra"),
]

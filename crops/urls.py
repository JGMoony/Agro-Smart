from django.urls import path
from .views import (
    dashboard, sowing_create, sowing_edit, sowing_delete,
    admin_dashboard, viability, price_create, price_delete,
    price_edit, price_predit, price_dashboard
)
from . import views

urlpatterns = [
    # Página de inicio
    path('', views.home, name='home'),

    # Dashboard de siembras
    path('mis-siembras/', dashboard, name='my_sowings'),

    # Gestión de siembras
    path('sowings/new/', sowing_create, name='sowing_create'),
    path('sowings/<int:pk>/edit/', sowing_edit, name='sowing_edit'),
    path('sowings/<int:pk>/delete/', sowing_delete, name='sowing_delete'),

    # Precios
    path('price/dashboard/', price_dashboard, name='price_dashboard'),
    path('prices/predict/', price_predit, name='price_predict'),
    path('prices/new/', price_create, name='price_create'),
    path('prices/<int:pk>/edit/', price_edit, name='price_edit'),
    path('prices/<int:pk>/delete/', price_delete, name='price_delete'),

    # Panel de administrador
    path('admin-panel/', admin_dashboard, name='admin_dashboard'),

    # Viabilidad y reportes
    path('viability/', viability, name='viability'),
    path("seleccionar-cultivo/", views.seleccionar_cultivo, name="seleccionar_cultivo"),
    path('', views.home, name='home'),
    path('mis-siembras/', dashboard, name='my_sowings'),
    path('reports/', views.reports_view, name='reports'),
    path('production', production_view, name='production')
]

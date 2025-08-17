from django.urls import path
from .views import dashboard, sowing_create, sowing_edit, sowing_delete, admin_dashboard, viability

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('sowings/new/', sowing_create, name='sowing_create'),
    path('sowings/<int:pk>/edit/', sowing_edit, name='sowing_edit'),
    path('sowings/<int:pk>/delete/', sowing_delete, name='sowing_delete'),
    path('admin-panel/', admin_dashboard, name='admin_dashboard'),
    path('viability/', viability, name='viability'),
]
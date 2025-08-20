from django.urls import path
from .views import CustomLoginView, CustomLogoutView, RegisterView, AdminUserCreateView
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),  # <- redirige al login después del logout
    path('admin/create-user', AdminUserCreateView.as_view(), name='admin_create_user'),
]

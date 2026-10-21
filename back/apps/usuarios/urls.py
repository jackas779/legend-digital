from django.urls import path

from .views import (
    LoginView,
    MeView,
    PermissionListCreateView,
    RegisterView,
    RoleListCreateView,
    health_view,
)

urlpatterns = [
    path('health/', health_view, name='usuarios-health'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('me/', MeView.as_view(), name='me'),
    path('roles/', RoleListCreateView.as_view(), name='roles'),
    path('permisos/', PermissionListCreateView.as_view(), name='permisos'),
]

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('usuarios/', views.gestionar_usuarios, name='usuarios'),
    path('usuarios/nuevo/', views.crear_usuario, name='usuario_crear'),
    path('usuarios/<int:pk>/editar/', views.editar_usuario, name='usuario_editar'),
]
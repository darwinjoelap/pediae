from django.urls import path
from . import views

app_name = 'configuracion'

urlpatterns = [
    path('', views.editar_config, name='editar'),
    # Catálogo de vacunas del consultorio
    path('vacunas/', views.catalogo_vacunas, name='vacunas'),
    path('vacunas/nueva/', views.vacuna_nueva, name='vacuna_nueva'),
    path('vacunas/<int:pk>/editar/', views.vacuna_editar, name='vacuna_editar'),
    path('vacunas/<int:pk>/toggle/', views.vacuna_toggle, name='vacuna_toggle'),
    path('vacunas/<int:pk>/eliminar/', views.vacuna_eliminar, name='vacuna_eliminar'),
]
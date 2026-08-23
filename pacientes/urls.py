from django.urls import path
from . import views

app_name = 'pacientes'

urlpatterns = [
    path('', views.lista_pacientes, name='lista'),
    path('nuevo/', views.nueva_paciente, name='nuevo'),
    path('<int:pk>/', views.detalle_paciente, name='detalle'),
    path('<int:pk>/editar/', views.editar_paciente, name='editar'),
    # Vacunas
    path('<int:pk>/vacunas/', views.vacunas_paciente, name='vacunas'),
    path('<int:pk>/vacunas/registrar/', views.registrar_vacuna, name='vacuna_registrar'),
    path('<int:pk>/vacunas/<int:va_pk>/eliminar/', views.eliminar_vacuna_aplicada, name='vacuna_eliminar'),
    # Curvas OMS — PDF
    path('<int:pk>/curvas-pdf/', views.curvas_crecimiento_pdf, name='curvas_pdf'),
]

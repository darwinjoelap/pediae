from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('<int:paciente_id>/pdf/', views.generar_pdf_historial, name='pdf_historial'),
    path('historial/<int:paciente_id>/', views.generar_pdf_historial, name='pdf_historial_alt'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
    path('estadisticas/pdf/', views.estadisticas_pdf, name='estadisticas_pdf'),
    path('pagos-pendientes/', views.pagos_pendientes, name='pagos_pendientes'),
]
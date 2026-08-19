from django.urls import path
from . import views

app_name = 'agenda'

urlpatterns = [
    path('', views.agenda_hoy, name='hoy'),
    path('semana/', views.agenda_semana, name='semana'),
    path('citas/nueva/', views.nueva_cita, name='cita_nueva'),
    path('citas/<int:pk>/editar/', views.editar_cita, name='cita_editar'),
    path('citas/<int:pk>/atendida/', views.marcar_atendida, name='cita_atendida'),
    path('citas/<int:pk>/recordatorio/', views.marcar_recordatorio, name='cita_recordatorio'),
    path('lugares/', views.lista_lugares, name='lugares'),
    path('lugares/nuevo/', views.nuevo_lugar, name='lugar_nuevo'),
    path('lugares/<int:pk>/toggle/', views.toggle_lugar, name='lugar_toggle'),
    path('lugares/<int:pk>/eliminar/', views.eliminar_lugar, name='lugar_eliminar'),
    path('<str:fecha>/', views.agenda_dia, name='dia'),
    path('lugares/<int:pk>/editar/', views.editar_lugar, name='lugar_editar'),
    path('citas/<int:pk>/eliminar/', views.eliminar_cita, name='cita_eliminar'),
]

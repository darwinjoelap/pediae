from django.urls import path
from . import views

app_name = 'consultas'

urlpatterns = [
    path('nueva/<int:paciente_id>/', views.nueva_consulta, name='nueva'),
    path('<int:pk>/', views.detalle_consulta, name='detalle'),
    path('<int:pk>/editar/', views.editar_consulta, name='editar'),
    path('<int:pk>/adjuntar/', views.adjuntar_archivo, name='adjuntar'),
    path('<int:pk>/imprimir/', views.imprimir_consulta, name='imprimir'),
    path('<int:pk>/recipe/', views.recipe_consulta, name='recipe'),
    path('<int:pk>/pago/', views.toggle_pago, name='toggle_pago'),
    path('<int:pk>/agregar-servicio/', views.agregar_servicio, name='agregar_servicio'),
    path('procedimiento/<int:paciente_id>/', views.nuevo_procedimiento, name='nuevo_procedimiento'),
    path('procedimiento/<int:pk>/pago/', views.toggle_pago_procedimiento, name='toggle_pago_procedimiento'),
    path('servicio/<int:pk>/eliminar/', views.eliminar_servicio, name='eliminar_servicio'),
]

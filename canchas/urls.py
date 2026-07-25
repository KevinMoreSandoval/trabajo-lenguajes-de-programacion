from django.urls import path

from . import views

app_name = 'canchas'

urlpatterns = [
    path('', views.lista_canchas, name='lista'),
    path('crear/', views.crear_cancha, name='crear'),
    path('reportes/', views.reportes, name='reportes'),
    path('<int:cancha_id>/editar/', views.editar_cancha, name='editar'),
    path('<int:cancha_id>/eliminar/', views.eliminar_cancha, name='eliminar'),
    path('<int:cancha_id>/horarios/', views.gestionar_horarios, name='horarios'),
    path('horarios/<int:horario_id>/eliminar/', views.eliminar_horario, name='eliminar_horario'),
    path('<int:cancha_id>/', views.detalle_cancha, name='detalle'),
]

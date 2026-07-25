from django.urls import path

from . import views

app_name = 'usuarios'

urlpatterns = [
    path('clientes/', views.lista_clientes, name='clientes'),
    path('clientes/crear/', views.crear_cliente, name='crear_cliente'),
    path('', views.lista_usuarios, name='lista'),
    path('crear/', views.crear_usuario, name='crear'),
    path('<int:user_id>/editar/', views.editar_usuario, name='editar'),
    path('<int:user_id>/eliminar/', views.eliminar_usuario, name='eliminar'),
]

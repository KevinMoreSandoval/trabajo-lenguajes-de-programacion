"""
URL configuration for djangocrud project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from authentication import views as auth_views
from canchas import views as canchas_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', auth_views.signin, name='signin'),
    path('signup/', auth_views.signup, name='signup'),
    path('dashboard/', canchas_views.dashboard, name='dashboard'),
    path('api/dashboard/kpis/', canchas_views.api_dashboard_kpis, name='api_dashboard_kpis'),
    path('api/dashboard/ingresos/', canchas_views.api_dashboard_ingresos, name='api_dashboard_ingresos'),
    path('api/dashboard/ocupacion/', canchas_views.api_dashboard_ocupacion, name='api_dashboard_ocupacion'),
    path('api/dashboard/reservas/', canchas_views.api_dashboard_reservas, name='api_dashboard_reservas'),
    path('usuarios/', include('authentication.urls')),
    path('canchas/', include('canchas.urls')),
    path('reservas/', include('reservas.urls')),
    path('pagos/', include('pagos.urls')),
    path('signout/', auth_views.signout, name='signout'),
]

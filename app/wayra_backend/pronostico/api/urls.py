from django.urls import path

from . import views

urlpatterns = [
    path("destinos", views.destinos),
    path("destinos/<slug:codigo>", views.destino),
    path("destinos/<slug:codigo>/pronostico", views.pronostico),
    path("destinos/<slug:codigo>/ventanas", views.ventanas),
    path("mapa", views.mapa),
    path("comparador", views.comparador),
    path("ejecucion", views.ejecucion),
]

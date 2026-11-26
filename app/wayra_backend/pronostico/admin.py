from django.contrib import admin

from .models import Actividad, Criterio, Destino, Ejecucion, PronosticoPunto, PuntoRuta


class PuntoRutaInline(admin.TabularInline):
    model = PuntoRuta
    extra = 0


@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "duracion_tipica_h")


@admin.register(Destino)
class DestinoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "actividad", "activo")
    list_filter = ("actividad", "activo")
    inlines = [PuntoRutaInline]


@admin.register(Criterio)
class CriterioAdmin(admin.ModelAdmin):
    list_display = ("actividad", "zona", "variable", "sentido", "umbral_amarillo", "umbral_rojo", "unidad")
    list_filter = ("actividad", "zona", "variable")


@admin.register(Ejecucion)
class EjecucionAdmin(admin.ModelAdmin):
    list_display = ("gfs_inicio_utc", "estado", "es_respaldo", "modelo_version", "horizonte_h")
    list_filter = ("estado", "es_respaldo")


@admin.register(PronosticoPunto)
class PronosticoPuntoAdmin(admin.ModelAdmin):
    list_display = ("ejecucion", "punto_ruta", "valido_utc", "fuente", "t_k", "rh_pct")
    list_filter = ("fuente",)

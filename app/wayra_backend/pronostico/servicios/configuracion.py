"""Carga de los archivos de datos/config a la base (RF015, RNF003).

Los archivos mandan: la base es una copia para consultar. Cargar dos veces
deja lo mismo, no duplica.
"""
import json
from functools import lru_cache

from django.conf import settings
from django.db import transaction

from ..models import LAT_MAX, LAT_MIN, LON_MAX, LON_MIN, Actividad, Criterio, Destino, PuntoRuta
from ..modelo import estatico


class ConfigError(Exception):
    pass


def _leer(nombre):
    ruta = settings.CONFIG_DIR / nombre
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise ConfigError(f"Falta el archivo {ruta}")
    except json.JSONDecodeError as e:
        raise ConfigError(f"{nombre} tiene un error en la línea {e.lineno}: {e.msg}")


@lru_cache(maxsize=1)
def parametros():
    return _leer("parametros.json")


@transaction.atomic
def cargar_config():
    resumen = {"actividades": 0, "destinos": 0, "puntos": 0, "criterios": 0}

    actividades = {}
    for a in _leer("actividades.json"):
        obj, _ = Actividad.objects.update_or_create(
            codigo=a["codigo"],
            defaults={"nombre": a["nombre"], "duracion_tipica_h": a.get("duracion_tipica_h")},
        )
        actividades[obj.codigo] = obj
        resumen["actividades"] += 1

    codigos_destino = []
    for d in _leer("destinos.json"):
        if d["actividad"] not in actividades:
            raise ConfigError(f"Destino {d['codigo']}: la actividad '{d['actividad']}' no existe")
        destino, _ = Destino.objects.update_or_create(
            codigo=d["codigo"],
            defaults={
                "nombre": d["nombre"],
                "actividad": actividades[d["actividad"]],
                "descripcion": d.get("descripcion", ""),
                "activo": d.get("activo", True),
                "fuente_coordenadas": d["fuente_coordenadas"],
            },
        )
        codigos_destino.append(destino.codigo)
        resumen["destinos"] += 1

        ordenes = []
        for orden, p in enumerate(d["puntos"], start=1):
            if not (LAT_MIN <= p["lat"] <= LAT_MAX and LON_MIN <= p["lon"] <= LON_MAX):
                raise ConfigError(f"{d['codigo']} / {p['nombre']}: el punto está fuera de la grilla WRF")
            fila, col = estatico.celda_wrf(p["lat"], p["lon"])
            PuntoRuta.objects.update_or_create(
                destino=destino,
                orden=orden,
                defaults={
                    "nombre": p["nombre"],
                    "zona": p["zona"],
                    "lat": p["lat"],
                    "lon": p["lon"],
                    "altitud_real_m": p["altitud_real_m"],
                    "fila": fila,
                    "col": col,
                },
            )
            ordenes.append(orden)
            resumen["puntos"] += 1
        destino.puntos.exclude(orden__in=ordenes).delete()

    # Un destino que sale del archivo se apaga; borrarlo se llevaría su historial.
    Destino.objects.exclude(codigo__in=codigos_destino).update(activo=False)

    vistos = []
    for c in _leer("criterios.json")["criterios"]:
        if c["actividad"] not in actividades:
            raise ConfigError(f"Criterio de '{c['actividad']}': esa actividad no existe")
        for zona in c["zonas"]:
            obj, _ = Criterio.objects.update_or_create(
                actividad=actividades[c["actividad"]],
                zona=zona,
                variable=c["variable"],
                defaults={
                    "sentido": c["sentido"],
                    "umbral_amarillo": c["umbral_amarillo"],
                    "umbral_rojo": c["umbral_rojo"],
                    "unidad": c["unidad"],
                    "fuente": c["fuente"],
                },
            )
            vistos.append(obj.pk)
            resumen["criterios"] += 1
    Criterio.objects.exclude(pk__in=vistos).delete()

    parametros.cache_clear()
    return resumen

"""Arma las respuestas de la API a partir de la última ejecución válida.

La página solo lee lo ya guardado; el modelo nunca corre por una visita (RNF001).
"""
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

import numpy as np
from django.conf import settings

from ..modelo import estatico
from ..models import Criterio, Destino, Ejecucion, PronosticoPunto, PuntoRuta
from ..servicios import indicadores as ind
from ..servicios.configuracion import parametros
from ..servicios.ejecucion import leer_gfs, leer_salida
from ..servicios.tiempo import a_iso, a_lima, desde_iso

LLUVIA_FUENTE = "Pronóstico externo Open-Meteo (GFS), no del modelo WAYRA"
RESOLUCION_KM = {"gfs": 28, "wayra": 3}
UNIDADES_MAPA = {"temperatura": "°C", "humedad": "%", "viento": "km/h"}


class SinEjecucion(Exception):
    pass


class NoEncontrado(Exception):
    pass


class DatoInvalido(Exception):
    pass


# --- Ejecución -------------------------------------------------------------

def ultima_ejecucion():
    ejec = Ejecucion.objects.filter(estado="exito").order_by("-gfs_inicio_utc", "es_respaldo", "-pk").first()
    if ejec is None:
        raise SinEjecucion("Todavía no hay un pronóstico disponible")
    return ejec


def datos_ejecucion(ejec):
    antiguedad = (datetime.now(timezone.utc) - ejec.gfs_inicio_utc).total_seconds() / 3600
    return {
        "id": ejec.pk,
        "gfs_inicio_utc": a_iso(ejec.gfs_inicio_utc),
        "gfs_inicio_lima": a_lima(ejec.gfs_inicio_utc),
        "antiguedad_h": int(antiguedad),
        "desactualizada": antiguedad > parametros()["desactualizada_h"],
        "es_respaldo": ejec.es_respaldo,
        "modelo_version": ejec.modelo_version,
        "horizonte_h": ejec.horizonte_h,
    }


# Los .npz no cambian una vez escritos: se leen una vez por ruta completa.
@lru_cache(maxsize=4)
def _leer_salida(ruta):
    return leer_salida(ruta)


@lru_cache(maxsize=4)
def _leer_gfs(ruta):
    return leer_gfs(ruta)


def _salida(nombre):
    return _leer_salida(str(Path(settings.SALIDAS_DIR) / nombre))


def _gfs(nombre):
    return _leer_gfs(str(Path(settings.SALIDAS_DIR) / nombre))


# --- Destinos ---------------------------------------------------------------

def _destino(codigo):
    destino = Destino.objects.select_related("actividad").filter(codigo=codigo, activo=True).first()
    if destino is None:
        raise NoEncontrado(f"No existe el destino '{codigo}'")
    return destino


def _info_punto(p):
    altitud_celda = round(estatico.altitud_celda(p.fila, p.col))
    diferencia = p.altitud_real_m - altitud_celda
    return {
        "id": p.pk,
        "nombre": p.nombre,
        "zona": p.zona,
        "lat": p.lat,
        "lon": p.lon,
        "altitud_real_m": p.altitud_real_m,
        "altitud_celda_m": altitud_celda,
        "diferencia_m": diferencia,
        "es_estimado": abs(diferencia) > parametros()["umbral_estimado_m"],
    }


def lista_destinos():
    resultado = []
    for d in Destino.objects.filter(activo=True).select_related("actividad").order_by("nombre"):
        altitudes = [p.altitud_real_m for p in d.puntos.all()]
        resultado.append({
            "codigo": d.codigo,
            "nombre": d.nombre,
            "actividad": {"codigo": d.actividad.codigo, "nombre": d.actividad.nombre},
            "altitud_min_m": min(altitudes, default=None),
            "altitud_max_m": max(altitudes, default=None),
        })
    return resultado


def detalle_destino(codigo):
    d = _destino(codigo)
    return {
        "codigo": d.codigo,
        "nombre": d.nombre,
        "actividad": {
            "codigo": d.actividad.codigo,
            "nombre": d.actividad.nombre,
            "duracion_tipica_h": d.actividad.duracion_tipica_h,
        },
        "descripcion": d.descripcion,
        "fuente_coordenadas": d.fuente_coordenadas,
        "puntos": [_info_punto(p) for p in d.puntos.all()],
    }


# --- Pronóstico por hora (RF003-RF006, RF014, RF018-RF020) ---------------

def _criterios_por_zona(actividad):
    por_zona = {}
    for c in Criterio.objects.filter(actividad=actividad).values():
        por_zona.setdefault(c["zona"], []).append(c)
    return por_zona


def _horas_punto(ejec, punto, info, criterios):
    par = parametros()
    filas = PronosticoPunto.objects.filter(ejecucion=ejec, punto_ruta=punto).order_by("valido_utc")
    gfs = {f.valido_utc: f for f in filas if f.fuente == "gfs"}
    humedad = next((c for c in criterios if c["variable"] == "humedad"), None)

    horas = []
    for f in (f for f in filas if f.fuente == "wayra"):
        t_c = ind.kelvin_a_c(f.t_k)
        if info["es_estimado"]:
            t_c = ind.ajuste_altitud(t_c, info["altitud_real_m"], info["altitud_celda_m"], par["gradiente_termico_c_por_km"])
        v_kmh = ind.viento_kmh(f.u_ms, f.v_ms)
        grados, rumbo = ind.viento_direccion(f.u_ms, f.v_ms)
        st = ind.sensacion_termica(t_c, v_kmh)
        color, motivo = ind.semaforo(
            {"temperatura": t_c, "sensacion_termica": st, "viento": v_kmh, "humedad": f.rh_pct},
            criterios,
        )
        lluvia = gfs.get(f.valido_utc)
        lluvia_mm = None if lluvia is None or lluvia.precip_mm is None else round(lluvia.precip_mm, 1)
        horas.append({
            "valido_utc": a_iso(f.valido_utc),
            "hora_lima": a_lima(f.valido_utc),
            "fin_lima": a_lima(f.valido_utc + timedelta(hours=1)),
            "temperatura_c": round(t_c, 1),
            "sensacion_termica_c": round(st, 1),
            "punto_rocio_c": round(ind.punto_rocio(t_c, f.rh_pct), 1),
            "bajo_cero": t_c < 0,
            "humedad_pct": round(f.rh_pct),
            "humedad_elevada": humedad is not None and f.rh_pct >= humedad["umbral_amarillo"],
            "viento_kmh": round(v_kmh),
            "viento_dir_grados": grados,
            "viento_dir_texto": rumbo,
            "lluvia_mm": lluvia_mm,
            "lluvia_fuente": LLUVIA_FUENTE if lluvia_mm is not None else None,
            "semaforo": color,
            "semaforo_motivo": motivo,
        })
    return horas


def _isoterma(ejec):
    horas, salida = _salida(ejec.archivo_salida)
    dem = estatico.cargar()["dem"]
    resultado = []
    for h, hora in enumerate(horas):
        altitud = ind.isoterma_cero(salida[h, :, :, 1] - 273.15, dem)
        resultado.append({"valido_utc": a_iso(hora), "hora_lima": a_lima(hora), "altitud_m": altitud})
    return resultado


def pronostico_destino(codigo):
    d = _destino(codigo)
    ejec = ultima_ejecucion()
    criterios = _criterios_por_zona(d.actividad)

    puntos = []
    for p in d.puntos.all():
        info = _info_punto(p)
        horas = _horas_punto(ejec, p, info, criterios.get(p.zona, []))
        i = ind.transicion_termica([h["temperatura_c"] for h in horas])
        puntos.append({
            **info,
            "punto_id": p.pk,
            "transicion_termica": {
                "hora_lima": horas[i]["hora_lima"] if i is not None else None,
                "texto": None if i is not None else "No ocurre en el horizonte",
            },
            "horas": horas,
        })
    return {
        "destino": d.codigo,
        "nombre": d.nombre,
        "actividad": d.actividad.nombre,
        "ejecucion": datos_ejecucion(ejec),
        "isoterma_0c": _isoterma(ejec),
        "puntos": puntos,
    }


def ventanas_destino(codigo, duracion_h=None):
    datos = pronostico_destino(codigo)
    d = _destino(codigo)
    if duracion_h is None:
        duracion_h = d.actividad.duracion_tipica_h or 6
    if not 1 <= duracion_h <= 48:
        raise DatoInvalido("duracion_h debe estar entre 1 y 48")
    if not datos["puntos"]:
        return {"duracion_h": duracion_h, "ventanas": []}

    # Una fila por hora con los colores de todas las zonas del destino.
    horas = []
    for i, base in enumerate(datos["puntos"][0]["horas"]):
        horas.append({
            "valido_utc": base["valido_utc"],
            "hora_lima": base["hora_lima"],
            "fin_lima": base["fin_lima"],
            "colores": [(p["horas"][i]["semaforo"], p["horas"][i]["semaforo_motivo"]) for p in datos["puntos"]],
        })
    return {"duracion_h": duracion_h, "ventanas": ind.ventanas(horas, duracion_h)}


# --- Mapa y comparador (RF008, RF009) -----------------------------------

def _valor_variable(rh, t_k, u, v, variable):
    if variable == "temperatura":
        return t_k - 273.15
    if variable == "humedad":
        return rh
    return np.hypot(u, v) * 3.6


def _indice_hora(horas, valido_utc):
    if not valido_utc:
        return 0
    try:
        buscada = desde_iso(valido_utc)
    except ValueError:
        raise DatoInvalido("valido_utc no tiene un formato de fecha válido")
    if buscada not in horas:
        raise NoEncontrado("No hay pronóstico para esa hora")
    return horas.index(buscada)


def mapa(variable, valido_utc=None, fuente="wayra"):
    if variable not in UNIDADES_MAPA:
        raise DatoInvalido("variable debe ser temperatura, humedad o viento")
    if fuente not in RESOLUCION_KM:
        raise DatoInvalido("fuente debe ser wayra o gfs")
    ejec = ultima_ejecucion()
    est = estatico.cargar()
    horas, salida = _salida(ejec.archivo_salida)
    h = _indice_hora(horas, valido_utc)

    if fuente == "wayra":
        campo = salida[h]
        lats, lons = est["wrf_lats"], est["wrf_lons"]
    else:
        horas_gfs, grilla, _, _ = _gfs(ejec.archivo_gfs)
        campo = grilla[horas_gfs.index(horas[h])][::-1]  # se voltea: fila 0 = sur, igual que WAYRA
        lats, lons = est["gfs_lats"][::-1], est["gfs_lons"]

    valores = _valor_variable(campo[..., 0], campo[..., 1], campo[..., 2], campo[..., 3], variable)
    decimales = 0 if variable == "humedad" else 1
    return {
        "variable": variable,
        "unidad": UNIDADES_MAPA[variable],
        "fuente": fuente,
        "resolucion_km": RESOLUCION_KM[fuente],
        "valido_utc": a_iso(horas[h]),
        "hora_lima": a_lima(horas[h]),
        "filas": int(valores.shape[0]),
        "columnas": int(valores.shape[1]),
        "lat_sur": float(lats[0]),
        "lat_norte": float(lats[-1]),
        "lon_oeste": float(lons[0]),
        "lon_este": float(lons[-1]),
        "min": round(float(valores.min()), decimales),
        "max": round(float(valores.max()), decimales),
        "valores": np.round(valores, decimales).tolist(),
        "horas_disponibles": [{"valido_utc": a_iso(x), "hora_lima": a_lima(x)} for x in horas],
        "destinos": [
            {"codigo": p.destino.codigo, "nombre": p.destino.nombre, "punto_id": p.pk,
             "punto": p.nombre, "lat": p.lat, "lon": p.lon}
            for p in PuntoRuta.objects.filter(destino__activo=True).select_related("destino")
        ],
    }


def comparador(valido_utc, punto_id):
    try:
        punto = PuntoRuta.objects.select_related("destino").get(pk=int(punto_id), destino__activo=True)
    except (TypeError, ValueError):
        raise DatoInvalido("punto_id debe ser un número")
    except PuntoRuta.DoesNotExist:
        raise NoEncontrado("No existe ese punto")

    ejec = ultima_ejecucion()
    horas, salida = _salida(ejec.archivo_salida)
    h = _indice_hora(horas, valido_utc)
    horas_gfs, grilla, _, _ = _gfs(ejec.archivo_gfs)
    gf, gc = estatico.celda_gfs(punto.lat, punto.lon)

    def valores(rh, t_k, u, v, fuente):
        return {
            "temperatura_c": round(float(t_k) - 273.15, 1),
            "humedad_pct": round(float(rh)),
            "viento_kmh": round(float(np.hypot(u, v)) * 3.6),
            "resolucion_km": RESOLUCION_KM[fuente],
        }

    return {
        "valido_utc": a_iso(horas[h]),
        "hora_lima": a_lima(horas[h]),
        "punto": {"id": punto.pk, "nombre": punto.nombre, "destino": punto.destino.nombre},
        "gfs": valores(*grilla[horas_gfs.index(horas[h]), gf, gc], "gfs"),
        "wayra": valores(*salida[h, punto.fila, punto.col], "wayra"),
    }

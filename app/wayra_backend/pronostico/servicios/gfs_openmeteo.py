"""Descarga del GFS desde Open-Meteo para los 17x13 puntos de la grilla de entrenamiento.

Pendiente (Noa): Open-Meteo sirve el GFS a 0,11°, y aquí se toma el valor de la
celda más cercana a cada nodo de 0,25°. Confirmar que se parece a lo que se usó
para entrenar (variables a 2 m y viento a 10 m).
"""
import time
from datetime import datetime, timedelta, timezone

import numpy as np
import requests

from ..modelo import estatico

URL = "https://api.open-meteo.com/v1/gfs"
URL_META = "https://api.open-meteo.com/data/ncep_gfs025/static/meta.json"
VARIABLES = "relative_humidity_2m,temperature_2m,wind_speed_10m,wind_direction_10m,precipitation"


class DescargaError(Exception):
    pass


def _pedir(url, params, intentos=3):
    ultimo = None
    for intento in range(intentos):
        try:
            r = requests.get(url, params=params, timeout=60)
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError) as e:
            ultimo = e
            time.sleep(2 * (intento + 1))
    raise DescargaError(f"Open-Meteo no respondió: {ultimo}")


def inicio_corrida_utc():
    """Hora de inicio de la última corrida GFS. Si falla, la última hora sinóptica con 6 h de margen."""
    try:
        meta = _pedir(URL_META, {}, intentos=1)
        return datetime.fromtimestamp(meta["last_run_initialisation_time"], tz=timezone.utc)
    except (DescargaError, KeyError):
        ahora = datetime.now(timezone.utc) - timedelta(hours=6)
        return ahora.replace(hour=ahora.hour - ahora.hour % 6, minute=0, second=0, microsecond=0)


def descargar(horas_pasadas=2, horizonte_h=48):
    """Devuelve las horas UTC, la grilla (N, 17, 13, 4) RH, T(K), U, V y la lluvia (N, 17, 13)."""
    est = estatico.cargar()
    lats, lons = est["gfs_lats"], est["gfs_lons"]
    malla_lat, malla_lon = np.meshgrid(lats, lons, indexing="ij")  # fila 0 = norte, como static.npz

    respuesta = _pedir(URL, {
        "latitude": ",".join(f"{v:.2f}" for v in malla_lat.ravel()),
        "longitude": ",".join(f"{v:.2f}" for v in malla_lon.ravel()),
        "hourly": VARIABLES,
        "past_hours": horas_pasadas,
        "forecast_hours": horizonte_h,
        "wind_speed_unit": "ms",
        "timezone": "GMT",
        "cell_selection": "nearest",
    })
    if isinstance(respuesta, dict):
        respuesta = [respuesta]
    if len(respuesta) != malla_lat.size:
        raise DescargaError(f"Llegaron {len(respuesta)} puntos, se esperaban {malla_lat.size}")

    horas = [datetime.fromisoformat(t).replace(tzinfo=timezone.utc) for t in respuesta[0]["hourly"]["time"]]
    n = len(horas)
    if n != horas_pasadas + horizonte_h:
        raise DescargaError(f"Llegaron {n} horas, se esperaban {horas_pasadas + horizonte_h}")

    def columna(nombre):
        valores = np.array([p["hourly"][nombre] for p in respuesta], dtype=object)
        if any(v is None for v in valores.ravel()):
            raise DescargaError(f"Faltan valores de {nombre}")
        return valores.astype(np.float32).T.reshape(n, len(lats), len(lons))

    rh = np.clip(columna("relative_humidity_2m"), 0, 100)
    t_k = columna("temperature_2m") + 273.15
    rapidez = columna("wind_speed_10m")
    direccion = np.deg2rad(columna("wind_direction_10m"))
    # La dirección es de dónde viene el viento; U y V apuntan hacia dónde va.
    u = -rapidez * np.sin(direccion)
    v = -rapidez * np.cos(direccion)

    grilla = np.stack([rh, t_k, u, v], axis=-1).astype(np.float32)
    lluvia = columna("precipitation")
    return horas, grilla, lluvia

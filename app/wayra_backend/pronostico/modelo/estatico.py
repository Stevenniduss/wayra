"""Lectura de datos/static.npz: relieve y coordenadas de las dos grillas.

Ojo con el orden de las filas:
- WRF (70x35): fila 0 = sur  (wrf_lats sube).
- GFS (17x13): fila 0 = norte (gfs_lats baja).
"""
from functools import lru_cache

import numpy as np
from django.conf import settings


@lru_cache(maxsize=1)
def cargar():
    with np.load(settings.DATOS_DIR / "static.npz") as datos:
        return {
            "dem": datos["dem"].astype(np.float32),
            "wrf_lats": datos["wrf_lats"].astype(np.float64),
            "wrf_lons": datos["wrf_lons"].astype(np.float64),
            "gfs_lats": datos["gfs_lats"].astype(np.float64),
            "gfs_lons": datos["gfs_lons"].astype(np.float64),
            "vars": [str(v) for v in datos["vars"]],
        }


def celda_wrf(lat, lon):
    """Fila y columna WRF más cercanas a un punto."""
    est = cargar()
    fila = int(np.abs(est["wrf_lats"] - lat).argmin())
    col = int(np.abs(est["wrf_lons"] - lon).argmin())
    return fila, col


def celda_gfs(lat, lon):
    """Fila y columna GFS más cercanas (fila 0 = norte)."""
    est = cargar()
    fila = int(np.abs(est["gfs_lats"] - lat).argmin())
    col = int(np.abs(est["gfs_lons"] - lon).argmin())
    return fila, col


def altitud_celda(fila, col):
    return float(cargar()["dem"][fila, col])

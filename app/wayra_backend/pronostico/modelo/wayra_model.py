"""Punto de entrada del modelo WAYRA.

Interfaz acordada con Noa:
    predict(gfs, horas_utc) -> salida
    gfs:    float32 (H, 3, 17, 13, 4)  horas t-2, t-1, t  |  canales RH, T, U, V
    salida: float32 (H, 70, 35, 4)     canales RH, T, U, V
    Unidades originales: RH en %, T en K, U y V en m/s. La normalización va dentro.

Mientras llegan los pesos de Noa, esta versión solo interpola la hora t del GFS
a la grilla WRF. Sirve para probar el flujo completo, no para la demo final.
"""
import hashlib
from pathlib import Path

import numpy as np
from django.conf import settings

from . import estatico

VERSION_PROVISIONAL = "interp-0.1"


def version():
    return VERSION_PROVISIONAL


def sha256_pesos():
    """Huella de los pesos (RNF009). Sin pesos, la de este archivo."""
    ruta = Path(settings.PESOS_MODELO)
    if not ruta.exists():
        ruta = Path(__file__)
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _interpolar_a_wrf(campo_gfs):
    """(17, 13) del GFS -> (70, 35) del WRF, bilineal."""
    est = estatico.cargar()
    # np.interp necesita la latitud subiendo: se voltea el GFS (norte arriba -> sur arriba).
    lats_gfs = est["gfs_lats"][::-1]
    campo = campo_gfs[::-1, :]

    por_lon = np.stack([np.interp(est["wrf_lons"], est["gfs_lons"], fila) for fila in campo])
    return np.stack([np.interp(est["wrf_lats"], lats_gfs, columna) for columna in por_lon.T], axis=1)


def predict(gfs, horas_utc):
    gfs = np.asarray(gfs, dtype=np.float32)
    if gfs.ndim != 5 or gfs.shape[1:] != (3, 17, 13, 4):
        raise ValueError(f"Entrada GFS con forma {gfs.shape}, se esperaba (H, 3, 17, 13, 4)")
    if len(horas_utc) != gfs.shape[0]:
        raise ValueError("horas_utc no coincide con H")

    horas = gfs.shape[0]
    salida = np.empty((horas, 70, 35, 4), dtype=np.float32)
    for h in range(horas):
        for canal in range(4):
            salida[h, :, :, canal] = _interpolar_a_wrf(gfs[h, -1, :, :, canal])

    salida[..., 0] = np.clip(salida[..., 0], 0, 100)
    return salida

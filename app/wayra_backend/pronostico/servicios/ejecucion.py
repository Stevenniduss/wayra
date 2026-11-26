"""Una ejecución completa (RF013): GFS -> modelo -> archivos .npz -> puntos en la base.

Si algo falla, la ejecución queda en 'error' con su motivo y la anterior sigue
siendo la que ve la página (RNF002).
"""
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from django.conf import settings
from django.db import transaction

from .. import modelo
from ..modelo import estatico
from ..models import Ejecucion, PronosticoPunto, PuntoRuta
from . import gfs_openmeteo
from .configuracion import cargar_config, parametros


def _guardar_gfs(ruta, horas, grilla, lluvia, gfs_inicio):
    np.savez_compressed(
        ruta,
        horas=np.array([int(h.timestamp()) for h in horas], dtype=np.int64),
        grilla=grilla,
        lluvia=lluvia,
        gfs_inicio=np.int64(gfs_inicio.timestamp()),
    )


def leer_gfs(ruta):
    with np.load(ruta) as d:
        horas = [datetime.fromtimestamp(int(t), tz=timezone.utc) for t in d["horas"]]
        gfs_inicio = datetime.fromtimestamp(int(d["gfs_inicio"]), tz=timezone.utc)
        return horas, d["grilla"], d["lluvia"], gfs_inicio


def leer_salida(ruta):
    with np.load(ruta) as d:
        horas = [datetime.fromtimestamp(int(t), tz=timezone.utc) for t in d["horas"]]
        return horas, d["salida"]


def ejecutar(gfs_desde=None, respaldo=False):
    cargar_config()
    par = parametros()
    pasadas, horizonte = par["horas_pasadas"], par["horizonte_h"]
    salidas = Path(settings.SALIDAS_DIR)
    salidas.mkdir(parents=True, exist_ok=True)

    ejec = Ejecucion.objects.create(
        es_respaldo=respaldo,
        modelo_version=modelo.version(),
        sha256_pesos=modelo.sha256_pesos(),
        gfs_inicio_utc=datetime.now(timezone.utc),
        inicio_proceso_utc=datetime.now(timezone.utc),
        horizonte_h=horizonte,
    )
    try:
        if gfs_desde:
            horas, grilla, lluvia, gfs_inicio = leer_gfs(gfs_desde)
        else:
            gfs_inicio = gfs_openmeteo.inicio_corrida_utc()
            horas, grilla, lluvia = gfs_openmeteo.descargar(pasadas, horizonte)

        archivo_gfs = f"ejecucion_{ejec.pk}_gfs.npz"
        _guardar_gfs(salidas / archivo_gfs, horas, grilla, lluvia, gfs_inicio)

        # Cada hora de salida usa las horas t-2, t-1 y t.
        entrada = np.stack([grilla[i - 2:i + 1] for i in range(pasadas, len(horas))])
        horas_salida = horas[pasadas:]
        salida = modelo.predict(entrada, horas_salida)
        if salida.shape != (len(horas_salida), 70, 35, 4) or not np.isfinite(salida).all():
            raise ValueError(f"El modelo devolvió una salida inválida {salida.shape}")

        archivo_salida = f"ejecucion_{ejec.pk}_salida.npz"
        np.savez_compressed(
            salidas / archivo_salida,
            horas=np.array([int(h.timestamp()) for h in horas_salida], dtype=np.int64),
            salida=salida,
        )

        filas = []
        for punto in PuntoRuta.objects.filter(destino__activo=True):
            gf, gc = estatico.celda_gfs(punto.lat, punto.lon)
            for h, hora in enumerate(horas_salida):
                rh, t, u, v = (float(x) for x in salida[h, punto.fila, punto.col])
                filas.append(PronosticoPunto(
                    ejecucion=ejec, punto_ruta=punto, valido_utc=hora, fuente="wayra",
                    t_k=t, rh_pct=rh, u_ms=u, v_ms=v,
                ))
                rh, t, u, v = (float(x) for x in grilla[pasadas + h, gf, gc])
                filas.append(PronosticoPunto(
                    ejecucion=ejec, punto_ruta=punto, valido_utc=hora, fuente="gfs",
                    t_k=t, rh_pct=rh, u_ms=u, v_ms=v,
                    precip_mm=float(lluvia[pasadas + h, gf, gc]),
                ))

        with transaction.atomic():
            PronosticoPunto.objects.bulk_create(filas, batch_size=1000)
            ejec.gfs_inicio_utc = gfs_inicio
            ejec.archivo_gfs = archivo_gfs
            ejec.archivo_salida = archivo_salida
            ejec.estado = "exito"
            ejec.fin_proceso_utc = datetime.now(timezone.utc)
            ejec.save()
    except Exception as e:
        ejec.estado = "error"
        ejec.mensaje_error = f"{type(e).__name__}: {e}"[:1000]
        ejec.fin_proceso_utc = datetime.now(timezone.utc)
        ejec.save()
        raise
    return ejec

"""Flujo completo sin internet: GFS falso -> modelo -> API."""
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from django.test import Client, TestCase, override_settings

from pronostico import modelo
from pronostico.models import Destino, Ejecucion, PronosticoPunto
from pronostico.servicios.configuracion import cargar_config
from pronostico.servicios.ejecucion import _guardar_gfs, ejecutar


class FlujoTest(TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.override = override_settings(SALIDAS_DIR=self.tmp)
        self.override.enable()

        inicio = datetime(2026, 12, 3, 6, tzinfo=timezone.utc)
        horas = [inicio + timedelta(hours=i) for i in range(50)]
        grilla = np.zeros((50, 17, 13, 4), dtype=np.float32)
        grilla[..., 0] = 70           # RH %
        grilla[..., 1] = 275.15       # 2 °C
        grilla[..., 2] = 3            # U
        grilla[..., 3] = 4            # V -> 18 km/h
        lluvia = np.full((50, 17, 13), 0.2, dtype=np.float32)
        self.gfs = self.tmp / "gfs_prueba.npz"
        _guardar_gfs(self.gfs, horas, grilla, lluvia, inicio)

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_cargar_config_dos_veces_no_duplica(self):
        primera = cargar_config()
        segunda = cargar_config()
        self.assertEqual(primera, segunda)
        self.assertEqual(Destino.objects.count(), primera["destinos"])

    def test_predict_forma_y_rango(self):
        entrada = np.zeros((4, 3, 17, 13, 4), dtype=np.float32)
        entrada[..., 0] = 150
        salida = modelo.predict(entrada, list(range(4)))
        self.assertEqual(salida.shape, (4, 70, 35, 4))
        self.assertLessEqual(salida[..., 0].max(), 100)

    def test_ejecucion_y_api(self):
        ejec = ejecutar(gfs_desde=self.gfs)
        self.assertEqual(ejec.estado, "exito")
        self.assertTrue(PronosticoPunto.objects.filter(ejecucion=ejec, fuente="gfs", precip_mm__range=(0.19, 0.21)).exists())

        c = Client()
        r = c.get("/api/destinos/laguna-churup/pronostico")
        self.assertEqual(r.status_code, 200)
        hora = r.json()["puntos"][0]["horas"][0]
        self.assertEqual(hora["hora_lima"], "03/12 03:00")
        self.assertEqual(hora["viento_kmh"], 18)
        self.assertEqual(len(r.json()["puntos"][0]["horas"]), 48)

        self.assertEqual(c.get("/api/mapa?variable=humedad").json()["filas"], 70)
        self.assertEqual(c.get("/api/mapa?variable=humedad&fuente=gfs").json()["filas"], 17)
        self.assertEqual(c.get("/api/destinos/no-existe").status_code, 404)

    def test_error_no_borra_la_anterior(self):
        buena = ejecutar(gfs_desde=self.gfs)
        with self.assertRaises(Exception):
            ejecutar(gfs_desde=self.tmp / "no_existe.npz")
        self.assertEqual(Ejecucion.objects.filter(estado="error").count(), 1)
        self.assertEqual(Client().get("/api/ejecucion").json()["id"], buena.pk)

    def test_sin_ejecuciones_responde_503(self):
        self.assertEqual(Client().get("/api/ejecucion").status_code, 503)

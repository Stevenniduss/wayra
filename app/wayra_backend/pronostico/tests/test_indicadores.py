from django.test import SimpleTestCase

from pronostico.servicios import indicadores as ind

VIENTO = {"variable": "viento", "sentido": "max", "umbral_amarillo": 30, "umbral_rojo": 50}
TEMP = {"variable": "temperatura", "sentido": "min", "umbral_amarillo": 0, "umbral_rojo": -5}


class UnidadesTest(SimpleTestCase):
    def test_kelvin(self):
        self.assertAlmostEqual(ind.kelvin_a_c(273.15), 0)

    def test_viento_del_norte(self):
        # Viento que viene del norte sopla hacia el sur: v negativo.
        self.assertEqual(ind.viento_direccion(0, -5), (0, "N"))
        self.assertEqual(ind.viento_direccion(5, 0), (270, "O"))
        self.assertEqual(ind.viento_direccion(0, 0), (None, None))

    def test_rapidez_en_kmh(self):
        self.assertAlmostEqual(ind.viento_kmh(3, 4), 18)


class DerivadosTest(SimpleTestCase):
    def test_sensacion_termica_valor_de_tabla(self):
        # Tabla de Environment Canada: -10 °C con 20 km/h -> -17,9 °C.
        self.assertAlmostEqual(ind.sensacion_termica(-10, 20), -17.9, delta=0.1)

    def test_sensacion_termica_no_aplica(self):
        self.assertEqual(ind.sensacion_termica(12, 30), 12)
        self.assertEqual(ind.sensacion_termica(0, 3), 0)

    def test_punto_rocio(self):
        self.assertAlmostEqual(ind.punto_rocio(20, 100), 20, delta=0.01)
        self.assertAlmostEqual(ind.punto_rocio(20, 50), 9.3, delta=0.1)

    def test_ajuste_altitud(self):
        # 500 m más arriba que la celda, con 6,5 °C/km: 3,25 °C menos.
        self.assertAlmostEqual(ind.ajuste_altitud(10, 4500, 4000, 6.5), 6.75)

    def test_isoterma(self):
        dem = [3000, 4000, 5000, 6000]
        t = [13, 6.5, 0, -6.5]
        self.assertEqual(ind.isoterma_cero(t, dem), 5000)
        self.assertIsNone(ind.isoterma_cero([5, 6, 7, 8], dem))

    def test_transicion_termica(self):
        self.assertEqual(ind.transicion_termica([-3, -1, 0.5, 2]), 2)
        self.assertIsNone(ind.transicion_termica([1, 2, 3]))


class SemaforoTest(SimpleTestCase):
    def test_verde(self):
        self.assertEqual(ind.semaforo({"viento": 10, "temperatura": 5}, [VIENTO, TEMP])[0], "verde")

    def test_amarillo_con_motivo(self):
        color, motivo = ind.semaforo({"viento": 35, "temperatura": 5}, [VIENTO, TEMP])
        self.assertEqual(color, "amarillo")
        self.assertIn("Viento 35 km/h", motivo)

    def test_gana_el_peor(self):
        color, motivo = ind.semaforo({"viento": 35, "temperatura": -6}, [VIENTO, TEMP])
        self.assertEqual(color, "rojo")
        self.assertIn("Temperatura", motivo)

    def test_sin_dato_es_gris(self):
        self.assertEqual(ind.semaforo({"viento": None, "temperatura": 5}, [VIENTO, TEMP])[0], "gris")

    def test_sin_criterios_es_gris(self):
        self.assertEqual(ind.semaforo({"viento": 5}, [])[0], "gris")


class VentanasTest(SimpleTestCase):
    def _horas(self, colores):
        return [
            {"valido_utc": f"h{i}", "hora_lima": f"03/12 {i:02d}:00", "fin_lima": f"03/12 {i + 1:02d}:00",
             "colores": [(c, "Viento alto")]}
            for i, c in enumerate(colores)
        ]

    def test_roja_si_alguna_hora_es_roja(self):
        v = ind.ventanas(self._horas(["verde", "rojo", "verde", "verde"]), 2)
        self.assertEqual([x["semaforo"] for x in v if x["inicio_lima"] == "03/12 00:00"], ["rojo"])

    def test_orden_mejor_a_peor_y_repetible(self):
        horas = self._horas(["amarillo", "verde", "verde", "rojo", "verde"])
        v = ind.ventanas(horas, 2)
        self.assertEqual([x["semaforo"] for x in v], ["verde", "amarillo", "rojo", "rojo"])
        self.assertEqual(v[0]["inicio_lima"], "03/12 01:00")
        self.assertEqual(v, ind.ventanas(horas, 2))

import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.test import Client

from pronostico.models import Destino


class Command(BaseCommand):
    help = "Guarda las respuestas de la API en archivos JSON para que el frontend trabaje sin backend."

    def add_arguments(self, parser):
        parser.add_argument("destino", nargs="?", default="../wayra_frontend/public/mock")

    def handle(self, *args, **options):
        carpeta = Path(options["destino"])
        carpeta.mkdir(parents=True, exist_ok=True)
        c = Client(HTTP_HOST="127.0.0.1")

        rutas = {
            "destinos.json": "/api/destinos",
            "ejecucion.json": "/api/ejecucion",
        }
        for d in Destino.objects.filter(activo=True):
            rutas[f"destino_{d.codigo}.json"] = f"/api/destinos/{d.codigo}"
            rutas[f"pronostico_{d.codigo}.json"] = f"/api/destinos/{d.codigo}/pronostico"
            rutas[f"ventanas_{d.codigo}.json"] = f"/api/destinos/{d.codigo}/ventanas"
            primero = d.puntos.first()
            if primero:
                rutas[f"comparador_{primero.pk}.json"] = f"/api/comparador?punto_id={primero.pk}"
        for variable in ("temperatura", "humedad", "viento"):
            for fuente in ("wayra", "gfs"):
                rutas[f"mapa_{variable}_{fuente}.json"] = f"/api/mapa?variable={variable}&fuente={fuente}"

        for archivo, ruta in rutas.items():
            r = c.get(ruta)
            if r.status_code != 200:
                self.stderr.write(f"{ruta} respondió {r.status_code}, no se guardó")
                continue
            (carpeta / archivo).write_text(json.dumps(r.json(), ensure_ascii=False), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"{len(rutas)} archivos en {carpeta.resolve()}"))
